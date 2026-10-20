"""Runs once after the dev container is created (Codespaces or local).

1. Creates .venv and installs the lab packages.
2. Writes .env from the secrets (PARTICIPANT, DT_TENANT, DT_API_TOKEN). DT_TENANT is just the
   tenant ID (abc12345); the full URLs are built from it.
3. Installs dtctl and points it at the tenant using DTCTL_PLATFORM_TOKEN.
4. Runs the prerequisite check.

Safe to run again: python .devcontainer/post_create.py
"""
import os
import re
import shutil
import subprocess
import sys
from functools import cache
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


def tenant_id():
    """The tenant ID from DT_TENANT. Tolerates a pasted URL by keeping only the first label."""
    raw = os.environ.get("DT_TENANT", "").strip().removeprefix("https://")
    return raw.split(".")[0].strip("/")


def ingest_url(tenant):
    return f"https://{tenant}.live.dynatrace.com"  # used by the labs (DT_ENDPOINT)


def apps_url(tenant):
    return f"https://{tenant}.apps.dynatrace.com"  # used by dtctl


@cache  # called twice (.env and dtctl); only report problems once
def clean_secrets():
    """Return the secrets that look valid. Bad ones are reported and dropped, never written."""
    tenant = tenant_id()
    checks = {
        "DT_TENANT": (tenant, r"[a-z0-9]{8}", "the 8-character tenant ID, e.g. abc12345"),
        "DT_API_TOKEN": (os.environ.get("DT_API_TOKEN", "").strip(), r"dt0c01\.[A-Za-z0-9]+\.[A-Za-z0-9]+",
                         "an access token starting dt0c01."),
        "DTCTL_PLATFORM_TOKEN": (os.environ.get("DTCTL_PLATFORM_TOKEN", "").strip(),
                                 r"dt0s16\.[A-Za-z0-9]+\.[A-Za-z0-9]+", "a platform token starting dt0s16."),
    }
    good = {"PARTICIPANT": os.environ.get("PARTICIPANT", "").strip()}
    for key, (value, pattern, expected) in checks.items():
        if value and re.fullmatch(pattern, value):
            good[key] = value
        elif value:
            print(f"WARNING: {key} does not look right (expected {expected}). It was NOT saved.")
        else:
            print(f"{key} was not provided.")
    return good


def write_env():
    """Merge the secrets into .env. Values already in .env are kept unless a secret is set."""
    env_file = Path(".env")
    if not env_file.exists():
        shutil.copy(".env.example", env_file)
    lines = env_file.read_text().splitlines()
    good = clean_secrets()
    values = {
        "PARTICIPANT": good.get("PARTICIPANT", ""),
        "DT_ENDPOINT": ingest_url(good["DT_TENANT"]) if "DT_TENANT" in good else "",
        "DT_API_TOKEN": good.get("DT_API_TOKEN", ""),
    }
    for key, value in values.items():
        if not value:
            continue
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                break
        else:
            lines.append(f"{key}={value}")
    env_file.write_text("\n".join(lines) + "\n")
    if all(values.values()):
        print(f".env written from secrets (DT_ENDPOINT={values['DT_ENDPOINT']}).")
    else:
        print("Some values are missing or invalid. Fix them by editing .env directly. "
              "The labs read it every time. See docs/setup.md.")


def setup_dtctl():
    if not shutil.which("dtctl"):
        run("sh", "-c", "curl -fsSL https://raw.githubusercontent.com/dynatrace-oss/dtctl/main/install.sh | sh",
            check=False)
    if not shutil.which("dtctl"):
        print("dtctl could not be installed. Lab 08 needs it. See docs/setup.md.")
        return
    good = clean_secrets()
    token = good.get("DTCTL_PLATFORM_TOKEN")
    url = apps_url(good["DT_TENANT"]) if "DT_TENANT" in good else None
    if not token or not url:
        print("DTCTL_PLATFORM_TOKEN or DT_TENANT not set. Skipping dtctl setup. Run: dtctl auth login")
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
