"""Small helpers for Lab 10, so the steps are the same on every OS (no cp, echo or printf).

Run from this folder:
    python lab.py log "INFO user logged in"     append a line to logs/file.log
    python lab.py config capture-debug          copy examples/capture-debug.yaml to remote-config.yaml
    python lab.py config baseline               copy examples/baseline.yaml to remote-config.yaml
    python lab.py reset                         put remote-config.yaml and logs/file.log back to the start
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE / "logs" / "file.log"
REMOTE = HERE / "remote-config.yaml"
START_LOG = "DEBUG starting up\nDEBUG loaded 3 plugins\nDEBUG cache miss key=user:42\n"


def use_config(name):
    src = HERE / "examples" / f"{name}.yaml"
    if not src.is_file():
        sys.exit(f"No such example: {src.name}. Choose from: "
                 + ", ".join(p.stem for p in sorted((HERE / "examples").glob("*.yaml"))))
    shutil.copyfile(src, REMOTE)
    print(f"remote-config.yaml is now {src.name}")


def main(argv):
    if len(argv) >= 2 and argv[0] == "log":
        with open(LOG, "a", encoding="utf-8", newline="\n") as f:
            f.write(" ".join(argv[1:]) + "\n")
        print(f"wrote to logs/file.log: {' '.join(argv[1:])}")
    elif len(argv) == 2 and argv[0] == "config":
        use_config(argv[1])
    elif argv == ["reset"]:
        use_config("baseline")
        with open(LOG, "w", encoding="utf-8", newline="\n") as f:
            f.write(START_LOG)
        print("logs/file.log is back to its starting lines")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
