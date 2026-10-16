# Lab 01: Auto instrumentation

Full instructions, step by step: `docs/labs/01-auto-instrumentation.md`.

Short version (console output):

```bash
# once, from the repo root: python3 -m venv .venv && pip install -r requirements.txt
source ../../.venv/bin/activate
opentelemetry-bootstrap -a install
export OTEL_SERVICE_NAME=shop-lab01 OTEL_TRACES_EXPORTER=console OTEL_METRICS_EXPORTER=none OTEL_LOGS_EXPORTER=none OTEL_SEMCONV_STABILITY_OPT_IN=http
opentelemetry-instrument uvicorn app:app --port 8000
```
