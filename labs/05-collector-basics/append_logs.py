"""Append the lines of sample.log to live.log, one line every second, forever.

Stop with Ctrl+C. The collector reads live.log.
"""
import time
from pathlib import Path

lines = Path("sample.log").read_text(encoding="utf-8").splitlines()

with open("live.log", "a", buffering=1, encoding="utf-8", newline="\n") as out:
    while True:
        for line in lines:
            out.write(line + "\n")
            print("wrote:", line)
            time.sleep(1)
