"""Checks that the tools needed for the labs are installed.

Usage (any OS, no virtual environment needed):  python scripts/check_prereqs.py
On macOS/Linux you may need:                    python3 scripts/check_prereqs.py
Add --quick to skip the Docker download test (about 65 MB).
Uses only the Python standard library.
"""
import contextlib
import importlib.util
import io
import os
import platform
import shutil
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

IS_WINDOWS = os.name == "nt"
failed = False


def ok(msg):
    print(f"  [ OK ] {msg}")


def bad(msg):
    global failed
    failed = True
    print(f"  [FAIL] {msg}")


def warn(msg):
    print(f"  [WARN] {msg}")


def hint(mac_linux, windows):
    """Pick the fix that matches this computer."""
    return windows if IS_WINDOWS else mac_linux


def run(*cmd, timeout=30):
    """Run a command. Returns (exit code, stdout) or (None, '') if it cannot start."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
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


def check_venv():
    if sys.prefix == sys.base_prefix:
        activate = hint("source .venv/bin/activate", r".venv\Scripts\Activate.ps1")
        warn(f"The virtual environment is not active in this terminal. Run: {activate}")
    else:
        ok("virtual environment is active")
    if importlib.util.find_spec("opentelemetry") is None or importlib.util.find_spec("fastapi") is None:
        warn("Lab packages are not installed here. Activate the virtual environment, then run: pip install -r requirements.txt")
    else:
        ok("lab packages are installed")


def check_powershell():
    """PowerShell may refuse to run the venv activation script (common on company laptops)."""
    code, out = run("powershell", "-NoProfile", "-Command", "Get-ExecutionPolicy")
    if code != 0:
        return
    if out in ("Restricted", "AllSigned"):
        warn(f"PowerShell execution policy is {out}, so Activate.ps1 will be blocked. "
             "In each terminal run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass "
             r"(or call .venv\Scripts\python directly).")
    else:
        ok(f"PowerShell can run the activation script (policy: {out})")


def check_line_endings():
    """Windows git can turn LF into CRLF. Files mounted into Linux containers then break."""
    bad_files = [f for f in ("labs/06-processors/sample.log", "labs/06-processors/collector.yaml",
                             "labs/10-opamp/remote-config.yaml")
                 if b"\r\n" in (ROOT / f).read_bytes()]
    if bad_files:
        bad("Files have Windows line endings (CRLF), which breaks the labs: " + ", ".join(bad_files)
            + ". Fix: git config core.autocrlf false, then delete the folder and clone again.")
    else:
        ok("line endings are correct (LF)")


def check_ports():
    """The labs publish these ports. A program already using one makes that lab fail."""
    ports = {4317: "Weaver", 4318: "collector", 4320: "OpAMP server", 8000: "lab 01 app",
             9000: "lab 02/03 frontend", 9001: "lab 02/03 backend"}
    busy = []
    for port, what in ports.items():
        with socket.socket() as sk:
            sk.settimeout(0.5)
            if sk.connect_ex(("127.0.0.1", port)) == 0:
                busy.append(f"{port} ({what})")
    if busy:
        warn("These ports are already in use: " + ", ".join(busy) + ". Stop the program using them before that lab.")
    else:
        ok("lab ports are free (4317, 4318, 4320, 8000, 9000, 9001)")


def check_network():
    """Can this computer reach the places the labs download from? Any HTTP answer means yes."""
    sites = [("Docker Hub", "https://registry-1.docker.io/v2/", True),
             ("GitHub registry (ghcr.io)", "https://ghcr.io/v2/", True),
             ("Google registry (gcr.io)", "https://gcr.io/v2/", True),
             ("PyPI (Python packages)", "https://pypi.org/simple/", True),
             ("Go modules (lab 07)", "https://proxy.golang.org/", False)]
    for name, url, needed in sites:
        try:
            urllib.request.urlopen(url, timeout=10)
            ok(f"can reach {name}")
        except urllib.error.HTTPError:
            ok(f"can reach {name}")  # 401 etc. still means the server answered
        except (urllib.error.URLError, OSError) as e:
            reason = getattr(e, "reason", e)
            if isinstance(reason, ssl.SSLError):
                warn(f"{name}: TLS certificate not trusted. Your company probably inspects HTTPS traffic. "
                     "Docker and pip may need the company root certificate. Ask IT, or use Codespaces.")
            else:
                (bad if needed else warn)(f"cannot reach {name} ({url}). A firewall or proxy may block it.")


def check_docker_pull():
    """Download tiny images from each registry. This tests the Docker daemon, not just this script."""
    images = [("Docker Hub", "hello-world:latest"),
              ("gcr.io", "gcr.io/distroless/static-debian12:latest"),
              ("ghcr.io", "ghcr.io/open-telemetry/opentelemetry-collector-releases/"
                          "opentelemetry-collector-opampsupervisor:0.162.0")]
    if run("docker", "info")[0] != 0:
        return
    print("  ...    testing Docker downloads (about 65 MB, can take a minute)")
    for name, image in images:
        code, out = run("docker", "pull", "--quiet", image, timeout=180)
        if code == 0:
            ok(f"docker can download from {name}")
        else:
            bad(f"docker cannot download from {name}. Check Docker Desktop proxy settings "
                "(Settings > Resources > Proxies) or ask IT to allow it. Or use the cloud option in docs/setup.md.")


def check_dtctl():
    if shutil.which("dtctl"):
        ok("dtctl")
        code, out = run("dtctl", "config", "get-contexts")
        if code == 0 and len(out.splitlines()) > 1:
            ok("dtctl has a context configured")
        else:
            warn("dtctl has no context. Run: dtctl auth login (or set DTCTL_PLATFORM_TOKEN in Codespaces).")
    else:
        warn("dtctl not found. Only lab 08 needs it. See docs/setup.md.")


def main():
    print("Checking prerequisites...")
    check_docker()
    check_python()
    check_venv()
    if IS_WINDOWS:
        check_powershell()
    check_line_endings()
    check_ports()
    check_network()
    if "--quick" not in sys.argv:
        check_docker_pull()
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
