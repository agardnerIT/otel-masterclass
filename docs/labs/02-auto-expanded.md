# Lab 02: Auto instrumentation expanded

**Time: 15 minutes**

## Goal

See one **distributed trace** that crosses two services. A `frontend` calls a `backend`, and you read the `traceparent` header that connects them.

## Why it matters

Real systems have many services. A trace is only useful if it follows a request from one service to the next. OpenTelemetry does this with **context propagation**: the caller puts the trace ID in an HTTP header, and the next service reads it. The instrumentation libraries do this for you.

## Steps

The lab files are in `labs/02-auto-expanded/`. Docker must be running.

- `frontend/app.py`: a FastAPI service. `GET /order/{id}` calls the backend with `requests`.
- `backend/app.py`: a FastAPI service. `GET /products/{id}` returns a product.

Neither file imports OpenTelemetry. Open them and check.

1. Go to the lab folder:
   ```bash
   cd labs/02-auto-expanded
   ```
2. Read `frontend/Dockerfile`. It installs the packages, runs `opentelemetry-bootstrap -a install` (as in Lab 01), and starts the app with `opentelemetry-instrument`. Bootstrap finds FastAPI **and** `requests`, so it installs an instrumentation library for each.
3. Fill in `.env` in the repo root first. See [Setup](../setup.md). Then start both services, and give compose the `.env` file:

    ```bash
    docker compose --env-file ../../.env up --build
    ```

    `docker-compose.yaml` sets `OTEL_TRACES_EXPORTER=otlp`, the endpoint (`$DT_ENDPOINT/api/v2/otlp`), and the token header. These are the same variables as in Lab 01.

    ??? note "No Dynatrace tenant? Print spans in the console"
        Add the console file. It turns the OTLP exporter into the console exporter. Spans then print in the container logs. The two values are dummies, because the main file needs them to be set:

        ```bash
        export DT_ENDPOINT=x DT_API_TOKEN=x
        docker compose -f docker-compose.yaml -f docker-compose.console.yaml up --build
        ```

4. In a second terminal, order a product:
   ```bash
   curl localhost:9000/order/1
   ```
   You get JSON back. Look at the field `traceparent_sent`.
5. Read the logs. The frontend prints `frontend sent traceparent: ...`. The backend prints `backend received traceparent: ...`. They are the **same value**.
6. Find the trace. In Dynatrace, open **Distributed Tracing** and filter by service `frontend-lab02`. (In console mode, look at the `trace_id` in every span, in both services.)

### Read the traceparent

The header looks like this:

```text
00-0d8a645dc4d5dcd1c2dbd31cc171983c-eca2e95684aac18e-03
│  │                                │                └─ flags
│  │                                └─ parent span ID (the frontend's outgoing call)
│  └─ trace ID (the same in every service)
└─ version
```

| Part | Meaning |
|---|---|
| version | Always `00` today (the W3C Trace Context standard) |
| trace ID | 32 hex characters. Every span of the request shares it. |
| parent span ID | 16 hex characters. The backend's server span uses this as its parent. |
| flags | `01` means "sampled" (keep this trace). The last digits can have other bits set; the sampled bit is the one to look for. |

The `requests` instrumentation **adds** the header to the outgoing call. The FastAPI instrumentation in the backend **reads** it and makes its span a child. That is all of context propagation.

### Agent or code?

In step 3 the agent (`opentelemetry-instrument`) did all the work. You can also turn the same instrumentation on **in code**. Look at `frontend/app_in_code.py`. The important lines are:

```python
FastAPIInstrumentor.instrument_app(app)  # one span for each incoming request
RequestsInstrumentor().instrument()      # one span for each outgoing request
```

Before that, the file builds the SDK itself: a `TracerProvider`, a service name, and an exporter. The agent did this for you from the environment variables.

Try it. Stop the stack (`Ctrl+C`), then run the frontend without the agent:

```bash
docker compose --env-file ../../.env \
  -f docker-compose.yaml -f docker-compose.code.yaml up --build
```

Run `curl localhost:9000/order/1` again. You get the same trace.

| | Agent (`opentelemetry-instrument`) | In code |
|---|---|---|
| Code changes | None | A few lines at startup |
| Control | Environment variables only | Full: choose which libraries, set options, add hooks |
| Good for | Fast start, many services, code you cannot change | Services where you need exact control, or later add manual spans (Lab 03) |
| Risk | Turns on everything it finds (can be noisy) | You must keep the setup code correct |

## Expected result

One trace with spans from **two services**:

```text
frontend-lab02  GET /order/{product_id}      (server span)
frontend-lab02    GET                         (client span, the call made by requests)
backend-lab02       GET /products/{product_id} (server span)
```

All of them have the same trace ID. The backend span is a child of the frontend's client span. FastAPI also adds small `http send` and `http receive` child spans.

<!-- TODO: screenshot of the Dynatrace trace (frontend-lab02 and backend-lab02). Save as docs/assets/lab02-trace.png and link it here. -->

*Screenshot placeholder: a Dynatrace trace with `frontend-lab02` and `backend-lab02` spans.*

## Stuck?

- **`port is already allocated` or `Not Found` from curl:** another program uses port 9000 or 9001 (for example, an old Lab 01 app). Stop it, or change the left number in the `ports` lines of `docker-compose.yaml`.
- **`curl: connection refused`:** the containers are still starting. Wait a few seconds.
- **Two separate traces, not one:** the `traceparent` header was lost. Check that the frontend logs show `frontend sent traceparent: ...` and not `None`.
- **No spans in console mode:** spans are printed in batches. Wait about 5 seconds after a request.
- **`required variable DT_ENDPOINT is missing a value`:** add `--env-file ../../.env` to the command, and check that `.env` has both values.
- **Nothing in Dynatrace:** check `DT_ENDPOINT` (no `/api/...` at the end) and the token scopes. See Lab 01.
- **Changed a file but nothing changed:** run `docker compose up --build` to rebuild the image.

## Going further

Exercise: **find an error in a trace.**

1. Run `curl -i localhost:9000/order/13`. The backend raises an exception for product 13.
2. Find this trace. Which span has the error? The backend server span has status `ERROR` and an exception event. The frontend returns `502`.
3. Run `curl -i localhost:9000/order/99`. This is a `404`. Compare it: is any span marked as an error? (Remember Lab 01: a 4xx is not a server error.)

Exercise: **add a third hop.**

The folder `inventory/` is ready. It is a third FastAPI service with `GET /stock/{id}` on port 8002. It is not in `docker-compose.yaml` yet. Your job is to wire it in, so the trace has three services.

1. Add the service to `docker-compose.yaml`, below `backend`:
   ```yaml
     inventory:
       build: ./inventory
       environment:
         <<: *otel-env
         OTEL_SERVICE_NAME: inventory-lab02
   ```
2. Tell the backend where it is. In the `backend` service, add this to `environment`, and add a `depends_on` for `inventory`:
   ```yaml
         INVENTORY_URL: http://inventory:8002
   ```
3. In `backend/requirements.txt`, add `requests==2.32.5`. The backend will make an outgoing call, so it needs `requests`. Bootstrap installs the matching instrumentation for you when the image builds.
4. In `backend/app.py`, call the inventory service before `return PRODUCTS[product_id]`:
   ```python
   stock = requests.get(f"{INVENTORY_URL}/stock/{product_id}", timeout=5).json()
   return {**PRODUCTS[product_id], "in_stock": stock["in_stock"]}
   ```
   You also need these lines at the top of the file:
   ```python
   import os
   import requests

   INVENTORY_URL = os.getenv("INVENTORY_URL", "http://localhost:8002")
   ```
5. Run `docker compose --env-file ../../.env up --build` and call `curl localhost:9000/order/1`.
6. Check the result. The response has `in_stock`. The logs of all three services show the **same trace ID** in the `traceparent`. The parent span ID is different in each, because each hop makes a new client span. In Dynatrace, you see `inventory-lab02` as a third service in the trace.
