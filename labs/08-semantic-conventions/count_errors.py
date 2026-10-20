"""One query for the whole company: how many requests ended in a server error (5xx)?

The query uses the standard name http.response.status_code. Nothing else.
Usage: python count_errors.py <file>
"""
import re
import sys

QUERY = re.compile(r"http\.response\.status_code=(5\d\d)")

path = sys.argv[1]
lines = open(path, encoding="utf-8").read().splitlines()
found = [line for line in lines if QUERY.search(line)]

print(f"File: {path}")
print(f"Query: http.response.status_code >= 500")
print(f"Lines: {len(lines)}")
print(f"Server errors found: {len(found)}")
for line in found:
    print(f"  {line}")
