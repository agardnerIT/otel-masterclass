"""Runs once after the dev container is created (Codespaces or local).

1. Creates .venv and installs the lab packages.
2. Writes .env from the secrets (PARTICIPANT, DT_ENDPOINT, DT_API_TOKEN).
3. Installs dtctl and points it at the tenant using DTCTL_PLATFORM_TOKEN.
4. Runs the prerequisite check.

Safe to run again: python .devcontainer/post_create.py
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
LOCAL_BIN = Path.home() / ".local" / "bin"
os.environ["PATH"] += os.pathsep + str(LOCAL_BIN)


def run(*cmd, check=True, **kw):
    return subprocess.run([str(c) for c in cmd], check=check, **kw)


def setup_python():
    if not Path(".venv").is_dir():
        run(sys.executable, "-m", "venv", ".venv")
    run(".venv/bin/pip", "install", "--quiet", "-r", "requirements.txt")
    # Activate the venv in every new terminal, once.
    line = f"source {ROOT}/.venv/bin/activate"
    for rc in (Path.home() / ".bashrc", Path.home() / ".zshrc"):
        if rc.exists() and line not in rc.read_text():
            with rc.open("a") as f:
                f.write(f"\n{line}\n")


def write_env():
    """Merge the secrets into .env. Values already in .env are kept unless a secret is set."""
    env_file = Path(".env")
    if not env_file.exists():
        shutil.copy(".env.example", env_file)
    lines = env_file.read_text().splitlines()
    for key in ("PARTICIPANT", "DT_ENDPOINT", "DT_API_TOKEN"):
        value = os.environ.get(key, "").strip()
        if not value:
            continue
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                break
        else:
            lines.append(f"{key}={value}")
    env_file.write_text("\n".join(lines) + "\n")
    missing = [k for k in ("PARTICIPANT", "DT_ENDPOINT", "DT_API_TOKEN") if not os.environ.get(k, "").strip()]
    if missing:
        print(f"Secrets not set: {', '.join(missing)}. Edit .env to add them (see docs/setup.md).")
    else:
        print(".env written from secrets.")


def apps_url(endpoint):
    """https://abc12345.live.dynatrace.com -> https://abc12345.apps.dynatrace.com"""
    m = re.match(r"https://([^.]+)\.(live|sprint|dev)\.dynatrace\.com", endpoint.strip())
    if not m:
        return None
    tenant, stage = m.groups()
    prefix = "" if stage == "live" else f"{stage}."
    return f"https://{tenant}.{prefix}apps.dynatrace.com"


def setup_dtctl():
    if not shutil.which("dtctl"):
        run("sh", "-c", "curl -fsSL https://raw.githubusercontent.com/dynatrace-oss/dtctl/main/install.sh | sh",
            check=False)
    if not shutil.which("dtctl"):
        print("dtctl could not be installed. Lab 08 needs it. See docs/setup.md.")
        return
    token = os.environ.get("DTCTL_PLATFORM_TOKEN", "").strip()
    url = apps_url(os.environ.get("DT_ENDPOINT", ""))
    if not token or not url:
        print("DTCTL_PLATFORM_TOKEN or DT_ENDPOINT not set. Skipping dtctl setup. Run: dtctl auth login")
        return
    run("dtctl", "config", "set-context", "lab", "--environment", url, "--token-ref", "lab-token")
    run("dtctl", "config", "set-credentials", "lab-token", "--token", token)
    run("dtctl", "config", "use-context", "lab", check=False)
    print(f"dtctl context 'lab' configured for {url}.")


if __name__ == "__main__":
    setup_python()
    write_env()
    setup_dtctl()
    run(".venv/bin/python", "scripts/check_prereqs.py", "--quick", check=False)
