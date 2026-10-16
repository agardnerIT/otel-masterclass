"""Show just "LEVEL message" for each log record the collector prints.

The Supervisor wraps the collector's output in JSON, and the debug exporter prints
many lines per batch of records. This script strips that down. Usage:

    docker compose logs -f --no-log-prefix agent | python3 watch_collector.py
"""
import json
import re
import sys

SEVERITY = re.compile(r"^SeverityText: (\w+)$", re.MULTILINE)
BODY = re.compile(r"^Body: Str\((.*)\)$", re.MULTILINE)

for line in sys.stdin:
    try:
        outer = json.loads(line)
        if outer.get("logger") != "supervisor.collector":
            continue
        text = json.loads(outer["msg"]).get("msg", "")
    except (ValueError, KeyError, TypeError):
        continue
    # One batch can hold several records: split on the record header first.
    for record in text.split("LogRecord #")[1:]:
        severity, body = SEVERITY.search(record), BODY.search(record)
        if severity and body:
            print(f"{severity.group(1):<6} {body.group(1)}", flush=True)
