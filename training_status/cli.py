import json, os, sys, urllib.request, urllib.error
from pathlib import Path


def _find_env():
    """Look for .env in the current directory, then walk up."""
    for d in [Path.cwd(), *Path.cwd().parents]:
        f = d / ".env"
        if f.is_file():
            return f
    return None


def _load_env():
    f = _find_env()
    if not f:
        return
    for line in f.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _participant():
    name = os.environ.get("PARTICIPANT")
    if name:
        return name.strip().lower()
    cache = Path.home() / ".training-status-name"
    if cache.exists():
        return cache.read_text(encoding="utf-8").strip()
    name = input("Your name: ").strip().lower()
    cache.write_text(name, encoding="utf-8")
    return name


def _send(status):
    _load_env()
    endpoint = os.environ.get("DT_ENDPOINT", "").rstrip("/")
    token = os.environ.get("DT_API_TOKEN", "")
    if not endpoint or not token:
        sys.exit("DT_ENDPOINT / DT_API_TOKEN not found. "
                 "Run this from inside the repo (where .env lives).")

    step = sys.argv[1] if len(sys.argv) > 1 else ""
    payload = [{
        "content": "status update",
        "log.source": "training",
        "participant": _participant(),
        "training.status": status,
        "step": step,
    }]
    req = urllib.request.Request(
        endpoint + "/api/v2/logs/ingest",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Api-Token " + token,
                 "Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        print(f"Sent: {status} (step {step or '-'})")
    except urllib.error.HTTPError as e:
        sys.exit(f"Couldn't send ({e.code}). Tell the instructor.")
    except Exception as e:
        sys.exit(f"Couldn't send ({e}). Tell the instructor.")


def stuck():  _send("stuck")
def solved(): _send("solved")
def done():   _send("done")
