# Lab 05: Collector basics

Run a collector that reads a log file and sends it to Dynatrace.
Full instructions: `docs/labs/05-collector-basics.md` (or the docs site).

Quick start (Docker must be running, `.env` filled in):

```bash
docker compose --env-file ../../.env up
# in a second terminal:
python append_logs.py
```

Files:

- `collector.yaml`: file_log to Dynatrace + debug (default)
- `collector.console.yaml`: no Dynatrace, debug only (use with `docker-compose.console.yaml`)
- `collector.otlp.yaml`: also receives OTLP from apps (use with `docker-compose.otlp.yaml`)
- `sample.log`: the log lines. `append_logs.py` copies them into `live.log` one per second.
