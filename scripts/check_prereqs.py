"""Checks that the tools needed for the labs are installed.

Usage (any OS, no virtual environment needed):  python scripts/check_prereqs.py
On macOS/Linux you may need:                    python3 scripts/check_prereqs.py
Uses only the Python standard library.
"""
import contextlib
import io
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

failed = False


def ok(msg):
    print(f"  [ OK ] {msg}")


def bad(msg):
    global failed
    failed = True
    print(f"  [FAIL] {msg}")


def warn(msg):
    print(f"  [WARN] {msg}")


def run(*cmd):
    """Run a command. Returns (exit code, stdout) or (None, '') if it cannot start."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return p.returncode, p.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None, ""


def load_env(path):
    """Read KEY=VALUE lines from .env into a dict (same rules as training_status)."""
    env = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def check_docker():
    if not shutil.which("docker"):
        bad("docker not found. Install from https://docs.docker.com/get-docker/")
        return
    code, out = run("docker", "info")
    if code == 0:
        _, ver = run("docker", "--version")
        ok(f"docker is installed and running ({ver.split(',')[0]})")
    else:
        bad("docker is installed but not running. Start Docker Desktop (or your Docker daemon).")
    code, out = run("docker", "compose", "version", "--short")
    if code == 0:
        ok(f"docker compose ({out})")
    else:
        bad("docker compose plugin not found. See https://docs.docker.com/compose/install/")


def check_python():
    v = sys.version_info
    if v >= (3, 11):
        ok(f"python {platform.python_version()}")
    else:
        bad(f"python 3.11 or newer is needed (found {platform.python_version()})")
    try:
        import ensurepip, venv  # noqa: F401, E401
        ok("python venv and pip")
    except ImportError:
        bad("python venv/pip missing. On Debian/Ubuntu: sudo apt install python3-venv")


def check_dynatrace():
    env_file = Path(".env")
    if not env_file.is_file():
        copy = "copy .env.example .env" if os.name == "nt" else "cp .env.example .env"
        warn(f"No .env file. Labs will use the console fallback. To use Dynatrace: {copy}")
        return
    env = load_env(env_file)
    endpoint = env.get("DT_ENDPOINT", "")
    token = env.get("DT_API_TOKEN", "")
    if not endpoint or not token or "YOUR_TENANT" in endpoint or "REPLACE_ME" in token:
        warn(".env exists but DT_ENDPOINT / DT_API_TOKEN are not set. Labs will use the console fallback.")
        return
    ok(".env has DT_ENDPOINT and DT_API_TOKEN")

    req = urllib.request.Request(
        endpoint.rstrip("/") + "/api/v2/otlp/v1/traces", data=b"", method="POST",
        headers={"Authorization": f"Api-Token {token}",
                 "Content-Type": "application/x-protobuf"})
    try:
        code = urllib.request.urlopen(req, timeout=10).status
    except urllib.error.HTTPError as e:
        code = e.code
    except (urllib.error.URLError, OSError):
        code = 0

    if code in (200, 400):
        ok(f"Dynatrace accepts the token for OTLP ingest (HTTP {code})")
        report_status(env)
    elif code in (401, 403):
        bad(f"Dynatrace rejected the token (HTTP {code}). Check the token scopes in docs/setup.md.")
    elif code == 0:
        warn(f"Could not reach {endpoint}. Check your network. You can still use the console fallback.")
    else:
        warn(f"Unexpected answer from Dynatrace (HTTP {code}).")


def report_status(env):
    """Send "finished 99" so the instructor can confirm status reporting works for each participant."""
    for k in ("DT_ENDPOINT", "DT_API_TOKEN", "PARTICIPANT"):
        if env.get(k):
            os.environ.setdefault(k, env[k])
    if not os.environ.get("PARTICIPANT") and not (Path.home() / ".training-status-name").exists():
        warn("PARTICIPANT is not set in .env, so the training status was not reported.")
        return
    sys.path.insert(0, str(ROOT))
    old_argv = sys.argv
    sys.argv = ["finished", "99"]
    try:
        from training_status.cli import done
        with contextlib.redirect_stdout(io.StringIO()):
            done()
        ok("training status reported (finished 99)")
    except BaseException:  # the helper calls sys.exit() on failure
        warn("Could not send the training status (finished 99). Tell the instructor.")
    finally:
        sys.argv = old_argv


def check_dtctl():
    if shutil.which("dtctl"):
        ok("dtctl")
    else:
        warn("dtctl not found. Only lab 08 needs it. See docs/setup.md.")


def main():
    print("Checking prerequisites...")
    check_docker()
    check_python()
    check_dtctl()
    check_dynatrace()
    print()
    if failed:
        print("Some checks failed. Fix them and run again.")
        return 1
    print("All required checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
