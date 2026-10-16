# 10-opamp

A bare-bones OpAMP server (`server.py`, Python and FastAPI) and two kinds of agent that connect to it. See the [Lab 10: OpAMP](../../docs/labs/10-opamp.md) page for the steps.

| Path | What it is |
|---|---|
| `server.py` | The OpAMP server. Tracks agents, watches `remote-config.yaml` and pushes it to agents |
| `remote-config.yaml` | **The file the server watches.** Whatever is in it is what every agent is told to run |
| `examples/` | Ready-made contents for it: `baseline.yaml` (DEBUG dropped) and `capture-debug.yaml` (DEBUG kept) |
| `docker-compose.yaml` | Two agents: `plain` (a collector with the `opamp` extension) and `agent` (Supervisor + collector) |
| `plain-collector.yaml` | Config for the `plain` collector |
| `agent/` | The Supervisor image, its settings and the collector's local config |
| `logs/file.log` | The log file the `agent` collector tails |
| `watch_collector.py` | Prints the collector's output as just `LEVEL message` |
| `opamp/v1/` | Python code generated from the [OpAMP protobuf files](https://github.com/open-telemetry/opamp-spec/tree/main/proto/opamp/v1). Committed, so you do not need `protoc` |

Based on [agardnerIT/kcd-indonesia-2026](https://github.com/agardnerIT/kcd-indonesia-2026), which builds the same server one step at a time.
