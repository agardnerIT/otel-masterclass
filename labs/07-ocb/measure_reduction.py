"""Measure how much the processors reduce the log volume.

Usage:
    docker compose logs collector --no-log-prefix | python3 measure_reduction.py sample.log

It counts the lines in the input file, and the records the debug exporter printed.
"""
import re
import sys

input_lines = len(open(sys.argv[1]).read().splitlines())
output = sys.stdin.read()

records = len(re.findall(r"^LogRecord #\d+", output, re.MULTILINE))
reduction = 100 * (input_lines - records) / input_lines

print(f"Input lines:      {input_lines}")
print(f"Records exported: {records}")
print(f"Reduction:        {reduction:.0f}%")
print(f"Email visible:    {'YES (leak!)' if re.search(r'@gmail', output) else 'no'}")
print(f"/health visible:  {'yes' if 'GET /health' in output else 'no'}")
print(f"DEBUG visible:    {'yes' if re.search(r'Body: Str\(DEBUG', output) else 'no'}")
