# 08-semantic-conventions

Files for the [Semantic conventions](../../docs/labs/08-semantic-conventions.md) page.

- `messy.log`: 7 request logs from 7 "teams", each in its own style.
- `standardised.log`: the same 7 requests, using OpenTelemetry names.
- `send_logs.py`: sends a file to Dynatrace as OpenTelemetry logs.
- `count_errors.py`: offline fallback. Runs the same query on the files, without Dynatrace.
