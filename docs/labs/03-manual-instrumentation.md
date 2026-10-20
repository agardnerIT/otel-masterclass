# Lab 03: Manual instrumentation

**Time: 25 minutes**

## Goal

Add your own spans, attributes, events, errors, metrics and correlated logs to the backend. Then compare this with what auto instrumentation gave you for free.

## Why it matters

Auto instrumentation knows about HTTP, databases and other libraries. It does not know about **your business**: an order, its value, a declined payment. Manual instrumentation adds that. It costs effort and needs care, so this lab shows what you gain and what you pay.

## Steps

The lab files are in `labs/03-manual-instrumentation/`. Docker must be running. Stop Lab 02 first, because both labs use ports 9000 and 9001.

- `frontend/`: the same frontend as Lab 02. It is auto instrumented. It has a new `quantity` parameter.
- `starter/backend/app.py`: the backend with manual instrumentation. **Two `TODO` markers are for you.**
- `solution/backend/app.py`: the finished backend.

The agent (`opentelemetry-instrument`) still sets up the SDK from environment variables. The code only uses the **API** (`trace.get_tracer`, `metrics.get_meter`). That is the normal way to mix auto and manual.

1. Go to the lab folder and start the **starter**:
   ```bash
   cd labs/03-manual-instrumentation
   docker compose --env-file ../../.env up --build
   ```
   Compared with Lab 02, `docker-compose.yaml` also turns on metrics and logs (`OTEL_METRICS_EXPORTER=otlp`, `OTEL_LOGS_EXPORTER=otlp`). It sets `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta`, because Dynatrace wants **delta** values for counters and histograms.

    ??? note "No Dynatrace tenant? Print telemetry in the console"
        ```bash
        docker compose -f docker-compose.yaml -f docker-compose.console.yaml up --build
        ```
        Metrics print every 5 seconds in this mode.

2. In a second terminal, send three orders:

    === "macOS / Linux"

        ```bash
        curl "localhost:9000/order/1?quantity=2"
        curl -i "localhost:9000/order/3?quantity=2"
        curl -i localhost:9000/order/99
        ```

    === "Windows (PowerShell)"

        Type `curl.exe`. In PowerShell, plain `curl` is a different command.

        ```powershell
        curl.exe "localhost:9000/order/1?quantity=2"
        curl.exe -i "localhost:9000/order/3?quantity=2"
        curl.exe -i localhost:9000/order/99
        ```

    - The first order works: 2 keyboards cost 98.
   - The second is declined: 2 monitors cost 600, and the payment limit is 500. You get a `402`.
   - The third returns `404`, because the product does not exist.
3. Open `starter/backend/app.py` and read it. Each feature is marked in the code:

    | Feature | Code | What you see |
    |---|---|---|
    | **Custom span** | `tracer.start_as_current_span("process_order")` | A new child span under the FastAPI span |
    | **Attributes** | `span.set_attribute("order.id", ...)` | Business data you can filter on |
    | **Span event** | `span.add_event("stock.checked", ...)` | A time stamp inside the span |
    | **Error** | `record_exception(...)` and `set_status(ERROR)` | A red span, with the exception details |
    | **Counter** | `orders_counter.add(1, {...})` | `shop.orders`: how many orders, by product and outcome |
    | **Histogram** | `order_value_histogram.record(...)` | `shop.order.value`: the spread of order values |
    | **Log correlation** | `logger.info(...)` inside the span | The log line carries the trace ID and span ID |

### Exercise: add one attribute and one span

In the starter, the order value is **not** on the span, and the payment call has **no span of its own**. Fix both.

1. **TODO 1:** add the attribute `order.value` to the `process_order` span.
2. **TODO 2:** put `charge_payment(order_value)` in its own span `charge_payment`. Set `payment.amount` on it. Record the error on this new span.
3. Restart, and send the same three orders again:
   ```bash
   docker compose --env-file ../../.env up --build
   ```
4. Stuck? Compare with `solution/backend/app.py`. You can run it with:
   ```bash
   docker compose --env-file ../../.env -f docker-compose.yaml -f docker-compose.solution.yaml up --build
   ```

## Expected result

For the declined order, one trace with:

```text
frontend-lab03  GET /order/{product_id}
frontend-lab03    GET                              (client span)
backend-lab03       GET /orders/{product_id}       (server span, 402)
backend-lab03         process_order                (ERROR, order.id, order.value ...)
backend-lab03           charge_payment             (ERROR, exception event)
```

- In Dynatrace, open **Distributed Tracing**, filter by service `backend-lab03`, and open the `process_order` span. Look at the attributes and the `stock.checked` event.
- Open **Notebooks** (or **Metrics**) and search for `shop.orders` and `shop.order.value`. Split `shop.orders` by `order.outcome`.
- Open **Logs** and find `order ... declined`. Open the trace from the log line (it has the same trace ID).

<!-- TODO: screenshot of the trace, the metric and the correlated log. Save as docs/assets/lab03-trace.png and link it here. -->

*Screenshot placeholder: the `process_order` span with attributes, and the `shop.orders` metric.*

!!! note "A 402 is not a server error"
    The FastAPI span stays without an error status, because a 4xx is the client's problem (Lab 01). But **your** span says "payment declined" and is an `ERROR`. Only your code knows that this matters to the business.

## Auto or manual?

| | Auto instrumentation | Manual instrumentation |
|---|---|---|
| **Effort** | Almost none | Real work: someone must write and review it |
| **Detail** | HTTP, database, framework level | Business level: orders, values, decisions |
| **Maintenance** | Update the library | Update your code when the logic changes |
| **Risk of noise** | High: it traces everything it finds | Low if you are careful. High if you add a span to every function. |
| **Cardinality** | Controlled by the library | **You control it, so you can break it** |
| **PII risk** | Low, but URLs and queries can leak data | Higher: you choose the attribute values (emails, names, card numbers) |

Rules of thumb:

- Auto and manual are both valid, and they can be combined. Auto gives broad coverage quickly. Manual gives full control over what is created. Some teams use only manual instrumentation, for example to keep tight control over volume, naming, cost or PII.
- Choose based on the questions you need to answer and how much control you need, not on a default order.
- Every span adds data volume and cost. Teams often reserve spans for "an operation worth seeing on its own", rather than wrapping every function.
- Put business data on **spans** (`order.id` is fine here). Keep **metric** attributes to a small set of values.

!!! warning "Cardinality"
    Every different combination of metric attribute values makes a new time series. Look at the counter in the code: it uses `product.name` and `order.outcome`. A handful of products and two outcomes is fine. If you used `order.id` or a **user ID**, you would create one series for each order or user. This makes metrics slow and expensive. Unbounded values like these are usually placed on spans or logs instead of metric attributes.

## Stuck?

- **`port is already allocated`:** Lab 02 is still running. Stop it from `labs/02-auto-expanded`:
  ```bash
  docker compose down
  ```
- **No metrics in Dynatrace:** the metric export interval is 10 seconds. Wait, then check the token has `metrics.ingest`. Logs need `logs.ingest`. See [Setup](../setup.md).
- **Metrics are there but histogram is empty or odd:** check that `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE` is `delta`.
- **Logs have no trace ID:** the log call must run **inside** the `with tracer.start_as_current_span(...)` block.
- **Changed the code but nothing changed:** rebuild:
  ```bash
  docker compose up --build
  ```
- **`required variable DT_ENDPOINT is missing a value`:** add the env file to the command:
  ```bash
  docker compose --env-file ../../.env up --build
  ```

## Going further

- Add a `quantity` attribute to the `shop.orders` counter. Is this safe for cardinality? Why or why not?
- Add a second span event when the payment is declined. What data would help the person who gets paged?
- Look at the `traceparent` between the two services (Lab 02). Your custom spans did not need any propagation code. Why?
