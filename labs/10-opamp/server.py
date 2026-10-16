"""Lab 10: a bare-bones OpAMP server that tracks agents and pushes configuration to them.

  * decodes OpAMP messages (protobuf) and keeps a registry of agents (GET /agents)
  * speaks OpAMP over plain HTTP and over WebSocket on /v1/opamp. Over WebSocket the server
    can talk to an agent at any time (over plain HTTP the agent has to ask first, up to ~30s of lag)
  * watches a file, remote-config.yaml: whatever is in it is sent to every agent as remote
    config, when the agent connects and again each time the file changes
  * tracks what each agent says about applying it (RemoteConfigStatus)
"""
import asyncio
import contextlib
import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect

from opamp.v1 import opamp_pb2

CONFIG_FILE = Path(__file__).parent / "remote-config.yaml"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    watcher = asyncio.create_task(watch_config_file())
    yield
    watcher.cancel()


app = FastAPI(title="Bare-bones OpAMP server", lifespan=lifespan)


@dataclass
class Agent:
    uid: str
    description: dict = field(default_factory=dict)
    capabilities: list = field(default_factory=list)
    healthy: bool | None = None
    last_sequence_num: int = 0
    last_seen: float = 0.0
    connected: bool = True
    effective_config: str = ""
    remote_config: opamp_pb2.AgentRemoteConfig | None = None  # what we want it to run
    remote_config_sent_hash: bytes | None = None  # so we don't resend while it is applying
    remote_config_status: str | None = None  # what it says about applying it


# The "database": instance_uid (hex) -> Agent. Lost on restart, which is fine for a demo.
agents: dict[str, Agent] = {}
# Agents that are connected over WebSocket right now, so we can message them.
connections: dict[str, WebSocket] = {}
# The config we want every capable agent to run: the contents of CONFIG_FILE.
desired_config: opamp_pb2.AgentRemoteConfig | None = None


def log(text: str) -> None:
    print(text, flush=True)


def attributes(kvs) -> dict:
    """Flatten a list of OpAMP KeyValue messages into a plain dict of strings."""
    return {kv.key: kv.value.string_value for kv in kvs}


def capability_names(bitmask: int) -> list[str]:
    """Turn the capabilities bitmask into names, e.g. ['ReportsStatus', 'AcceptsRemoteConfig']."""
    return [
        name.removeprefix("AgentCapabilities_")
        for name, bit in opamp_pb2.AgentCapabilities.items()
        if bit and bitmask & bit
    ]


def update_registry(msg: opamp_pb2.AgentToServer) -> bool:
    """Record what the agent told us. Returns True if we need the agent's full state."""
    uid = msg.instance_uid.hex()
    agent = agents.get(uid)
    is_new = agent is None
    if is_new:
        agent = agents[uid] = Agent(uid)
        log(f"+ agent {uid} connected")

    # Agents may omit unchanged fields to save bandwidth, so only update what is present.
    if msg.HasField("agent_description"):
        agent.description = {
            **attributes(msg.agent_description.identifying_attributes),
            **attributes(msg.agent_description.non_identifying_attributes),
        }
    if msg.capabilities:
        agent.capabilities = capability_names(msg.capabilities)
    if msg.HasField("health"):
        agent.healthy = msg.health.healthy
    if msg.HasField("effective_config"):
        files = msg.effective_config.config_map.config_map.values()
        agent.effective_config = "\n".join(f.body.decode() for f in files)
    if msg.HasField("remote_config_status"):
        status = opamp_pb2.RemoteConfigStatuses.Name(msg.remote_config_status.status)
        status = status.removeprefix("RemoteConfigStatuses_")
        if status != agent.remote_config_status:
            log(f"~ agent {uid} remote config {status} {msg.remote_config_status.error_message}")
        agent.remote_config_status = status

    # sequence_num goes up by 1 per message. A gap means we missed something
    # (or we restarted and lost state), so ask the agent to resend everything.
    gap = not is_new and msg.sequence_num != agent.last_sequence_num + 1
    if gap:
        log(f"! agent {uid}: expected seq {agent.last_sequence_num + 1}, got {msg.sequence_num}")

    agent.last_sequence_num = msg.sequence_num
    agent.last_seen = time.time()
    agent.connected = not msg.HasField("agent_disconnect")
    if not agent.connected:
        log(f"- agent {uid} disconnected")

    # A brand new agent that opens with sequence_num > 1 also skipped ahead (we lost state).
    return gap or (is_new and msg.sequence_num != 1)


def handle_message(msg: opamp_pb2.AgentToServer) -> opamp_pb2.ServerToAgent:
    """Everything the server does with one AgentToServer message, whatever the transport."""
    needs_full_state = update_registry(msg)
    agent = agents[msg.instance_uid.hex()]

    response = opamp_pb2.ServerToAgent(
        instance_uid=msg.instance_uid,  # required in every response
        capabilities=(
            opamp_pb2.ServerCapabilities_AcceptsStatus
            | opamp_pb2.ServerCapabilities_OffersRemoteConfig
            | opamp_pb2.ServerCapabilities_AcceptsEffectiveConfig
        ),
    )
    if needs_full_state:
        response.flags = opamp_pb2.ServerToAgentFlags_ReportFullState

    # Offer the config we want it to run, unless it already runs it or we just sent it.
    if desired_config and "AcceptsRemoteConfig" in agent.capabilities:
        agent.remote_config = desired_config
    want = agent.remote_config
    if (
        want
        and msg.remote_config_status.last_remote_config_hash != want.config_hash
        and agent.remote_config_sent_hash != want.config_hash
    ):
        response.remote_config.CopyFrom(want)
        agent.remote_config_sent_hash = want.config_hash
        log(f"> agent {agent.uid}: sending {CONFIG_FILE.name}")
    return response


@app.post("/v1/opamp")
async def opamp_http(request: Request) -> Response:
    """OpAMP over HTTP: one request, one response. The agent polls."""
    msg = opamp_pb2.AgentToServer()
    msg.ParseFromString(await request.body())
    response = handle_message(msg)
    return Response(response.SerializeToString(), media_type="application/x-protobuf")


@app.websocket("/v1/opamp")
async def opamp_ws(ws: WebSocket) -> None:
    """OpAMP over WebSocket: one long-lived connection, either side can send at any time."""
    await ws.accept()
    uid = None
    try:
        while True:
            data = await ws.receive_bytes()
            msg = opamp_pb2.AgentToServer()
            msg.ParseFromString(data[1:])  # skip the header: a varint, always 0 for now
            uid = msg.instance_uid.hex()
            connections[uid] = ws
            response = handle_message(msg)
            await ws.send_bytes(b"\x00" + response.SerializeToString())
    except WebSocketDisconnect:
        pass
    finally:
        if uid:
            connections.pop(uid, None)
            agents[uid].connected = False
            agents[uid].remote_config_sent_hash = None  # re-offer the config if it comes back
            log(f"- agent {uid} connection closed")


async def watch_config_file() -> None:
    """Every second, check CONFIG_FILE; when its contents change, push it to the agents.

    Comparing a hash of the contents (not the modified time) works however the file is
    changed: saved in an editor, `cp`, `echo >`, ...
    """
    global desired_config
    last_hash = None
    while True:
        if CONFIG_FILE.exists():
            body = CONFIG_FILE.read_bytes()
            config_hash = hashlib.sha256(body).digest()
            if config_hash != last_hash:
                last_hash = config_hash
                log(f"* {CONFIG_FILE.name} changed ({config_hash.hex()[:8]})")
                desired_config = opamp_pb2.AgentRemoteConfig(config_hash=config_hash)
                desired_config.config.config_map[""].body = body
                desired_config.config.config_map[""].content_type = "text/yaml"
                await push_to_agents()
        await asyncio.sleep(1)


async def push_to_agents() -> None:
    """Send the desired config to every agent that is connected over WebSocket right now."""
    for agent in agents.values():
        ws = connections.get(agent.uid)
        if ws and "AcceptsRemoteConfig" in agent.capabilities:
            agent.remote_config = desired_config
            agent.remote_config_sent_hash = desired_config.config_hash
            response = opamp_pb2.ServerToAgent(
                instance_uid=bytes.fromhex(agent.uid), remote_config=desired_config
            )
            await ws.send_bytes(b"\x00" + response.SerializeToString())
            log(f"> agent {agent.uid}: pushed {CONFIG_FILE.name}")
    # Agents that are not connected over WebSocket (e.g. HTTP) get it in their next reply,
    # and agents that connect later get it from handle_message().


@app.get("/agents")
async def list_agents() -> list[dict]:
    now = time.time()
    return [
        {
            "instance_uid": a.uid,
            "connected": a.connected,
            "healthy": a.healthy,
            "seconds_since_seen": round(now - a.last_seen, 1),
            "description": a.description,
            "capabilities": a.capabilities,
            "remote_config": a.remote_config.config_hash.hex()[:8] if a.remote_config else None,
            "remote_config_status": a.remote_config_status,
        }
        for a in agents.values()
    ]


@app.get("/agents/{uid}/effective-config")
async def effective_config(uid: str) -> Response:
    """The config the collector is really running, as it reported it."""
    if uid not in agents:
        raise HTTPException(404, "unknown agent")
    return Response(agents[uid].effective_config, media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4320, log_level="warning")
