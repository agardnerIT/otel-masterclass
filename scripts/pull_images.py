"""Download and build every Docker image the labs need, in lab order.

Start this in its own terminal at the beginning of the workshop and leave it running while
the slides are on. It is safe to run again: layers that are already downloaded are skipped,
so a second run after a Wi-Fi drop only fetches what is missing.

Usage (any OS, no virtual environment needed):  python scripts/pull_images.py
On macOS/Linux you may need:                    python3 scripts/pull_images.py
Uses only the Python standard library.
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LABS = ROOT / "labs"
MIN_FREE_GB = 6  # the images and build cache need about 3 GB

# (label, lab folder, docker compose arguments), in lab order so early labs are ready first.
STEPS = [
    ("Lab 02  build the three services", "02-auto-expanded", ["build"]),
    ("Lab 03  build the frontend and starter backend", "03-manual-instrumentation", ["build"]),
    ("Lab 03  build the solution backend",
     "03-manual-instrumentation", ["-f", "docker-compose.yaml", "-f", "docker-compose.solution.yaml", "build", "backend"]),
    ("Lab 05  pull the Dynatrace collector", "05-collector-basics", ["pull"]),
    ("Lab 06  pull the contrib collector", "06-processors", ["pull"]),
    ("Lab 07  build the custom collector (slowest: downloads Go modules)", "07-ocb", ["build"]),
    ("Lab 09  pull Weaver", "09-weaver", ["pull"]),
    ("Lab 10  pull the plain collector", "10-opamp", ["pull", "plain"]),
    ("Lab 10  build the Supervisor agent", "10-opamp", ["build", "agent"]),
]


def run_step(folder, args):
    """Run one docker compose command. Returns (ok, output). Prints a heartbeat while it runs."""
    p = subprocess.Popen(["docker", "compose", *args], cwd=LABS / folder,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    started = time.time()
    # Read output on a thread-free loop: communicate() with a timeout lets us print a heartbeat.
    chunks = []
    while True:
        try:
            out, _ = p.communicate(timeout=30)
            chunks.append(out)
            break
        except subprocess.TimeoutExpired:
            print(f"         ... still working ({int(time.time() - started)}s)", flush=True)
    return p.returncode == 0, "".join(chunks)


def main():
    if not shutil.which("docker"):
        sys.exit("docker not found. Install Docker first. See docs/setup.md.")
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        sys.exit("Docker is not running. Start Docker Desktop, then run this again.")
    free_gb = shutil.disk_usage(ROOT).free / 1e9
    if free_gb < MIN_FREE_GB:
        print(f"WARNING: only {free_gb:.1f} GB free. The images need about 3 GB. Free some space.\n")

    print("Downloading the lab images. Leave this running. It is safe to run again.\n")
    failed = []
    total_start = time.time()
    for i, (label, folder, args) in enumerate(STEPS, 1):
        print(f"[{i}/{len(STEPS)}] {label}", flush=True)
        t = time.time()
        ok, out = run_step(folder, args)
        if not ok:
            print("         first try failed, retrying once...", flush=True)
            ok, out = run_step(folder, args)
        if ok:
            print(f"         done in {int(time.time() - t)}s", flush=True)
        else:
            failed.append(label)
            print(f"         FAILED. Last lines of the output:")
            for line in out.strip().splitlines()[-6:]:
                print(f"           {line}")

    print(f"\nFinished in {int((time.time() - total_start) // 60)} min.")
    if failed:
        print("These steps failed. Check your network, then run this script again (it only fetches what is missing):")
        for label in failed:
            print(f"  - {label}")
        return 1
    print("All images are ready. The labs will start quickly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
