# Lab 06: Processors

**Time: 25 minutes**

## Goal

Add processors to the collector from Lab 05. Drop log lines you do not need, hide an email address, and collapse repeated lines. Measure how much data you save.

## Why it matters

Backends charge by volume, and most log lines are noise: health checks, debug output, the same error 1000 times. Logs can also hold personal data that must not leave your network. A processor fixes this **before** the data leaves the collector. The app does not change.

## The logs

`sample.log` has 11 lines. Read them and find the problems:

```text
INFO order-service GET /api/orders/48214 status=200 duration_ms=142
INFO order-service GET /health status=200 duration_ms=3                 <- health check
INFO order-service GET /health status=200 duration_ms=1                 <- health check
WARN payment-service Connection reset by peer while calling downstream billing-api   <- repeated
WARN payment-service Connection reset by peer while calling downstream billing-api   <- repeated
WARN payment-service Connection reset by peer while calling downstream billing-api   <- repeated
DEBUG order-service Cache lookup for key=order:48214 result=miss        <- debug noise
INFO account-service password reset for uid=jsmith email=john.smith999@gmail.com     <- personal data
INFO payment-service Payment for txn tCode=PYMT-7784-AU amount=129.50 currency=AUD status=200
INFO order-service GET /api/orders/48214 status=500
INFO order-service GET /health status=200 duration_ms=2                 <- health check
```

## The tools

| Processor | What it does | Use it when |
|---|---|---|
| `filter` | **Drops** records that match a rule | The whole record has no value |
| `transform` | **Changes** a record (here: replace text) | The record is useful, but one part is not |
| `log_dedup` | **Collapses** identical records into one with a count | The same message repeats |

!!! note "Which image?"
    This lab uses the **contrib** image (`0.162.0`). The Dynatrace distro has `filter`, `transform` and `redaction`, but not `log_dedup`. See the table in [Lab 05](05-collector-basics.md#which-collector-image). Contrib is bigger, so [Lab 06b](06b-ocb.md) shows how to build your own.

The rules are written in **OTTL**, the OpenTelemetry Transformation Language. `IsMatch(log.body, "...")` is true when the log text matches a regular expression. A `filter` condition says what to **drop**.

## Steps

The lab files are in `labs/06-processors/`. Docker must be running.

1. Go to the lab folder:
   ```bash
   cd labs/06-processors
   ```
2. Open `collector.yaml`. It **defines** five processors, but the pipeline uses none:
   ```yaml
   service:
     pipelines:
       logs:
         receivers: [file_log]
         processors: []
         exporters: [otlp_http/dynatrace, debug]
   ```
   The collector reads `sample.log` once, from the start. The `debug` exporter prints every record in full, so we can count them.
3. Start it with no processors. This is our baseline:
   ```bash
   docker compose --env-file ../../.env up -d
   ```
   ??? note "No Dynatrace tenant?"
       ```bash
       export DT_ENDPOINT=http://localhost:1 DT_API_TOKEN=x
       docker compose up -d
       ```
       The Dynatrace exporter will print errors. Ignore them. The debug output is correct. Use `--force-recreate` and `docker compose down` as in the steps below, without `--env-file`.
4. Wait 15 seconds. Then measure:
   ```bash
   sleep 15
   docker compose logs collector --no-log-prefix | python3 measure_reduction.py sample.log
   ```
   The script counts the lines in `sample.log` and the records the collector exported. You should see 11 records, 0% reduction, and `Email visible: YES (leak!)`.
5. Stop the collector. Do this before every change:
   ```bash
   docker compose down
   ```

### Exercise: add one processor at a time

Edit the `processors:` list in `collector.yaml`. After each change, run `docker compose --env-file ../../.env up -d --force-recreate`, wait 15 seconds, run the measure command, and run `docker compose down`.

| Stage | `processors:` list | What it does |
|---|---|---|
| 1 | `[filter/health]` | Drops the 3 health checks |
| 2 | `[filter/health, filter/low_value]` | Also drops the DEBUG line |
| 3 | `[filter/health, filter/low_value, log_dedup]` | Collapses 3 identical warnings into 1 |
| 4a | `[filter/health, filter/low_value, filter/personal_info, log_dedup]` | **Drops** the line that has an email |
| 4b | `[filter/health, filter/low_value, transform/mask_email, log_dedup]` | **Masks** the email, keeps the line |

Stage 4a and 4b are two answers to the same problem. Try both.

??? note "Why does `log_dedup` wait 10 seconds?"
    `log_dedup` holds records for a time window (`interval: 10s`) and counts the identical ones. At the end of the window it sends **one** record with an attribute `log_duplicates: 3`. This is why we wait before we measure. It is also why `log_dedup` goes **after** the filters: there is no reason to count records you will drop.

## Drop or mask?

| | `filter` (drop) | `transform` (mask) |
|---|---|---|
| Result | The line is gone | The line stays, one part changes |
| Volume | Lower | Almost the same |
| You still see | Nothing | That a password reset happened, for which user |
| Risk | You lose useful events | A bad pattern can miss some data |
| Pick it when | The line has no value | The line has value, but part of it is sensitive |

Our line says "password reset for uid=jsmith". That event is useful for security. Dropping it hides it. **Masking is the better choice here.** The solution uses masking.

!!! warning "Masking is not perfect"
    The mask only catches what the pattern matches. The line still has `uid=jsmith`. Think about what else is personal data in your own logs. Test your patterns with real samples.

## Expected result

Run the finished config (stage 4b) to check:

```bash
docker compose --env-file ../../.env -f docker-compose.yaml -f docker-compose.solution.yaml up -d --force-recreate
sleep 15
docker compose logs collector --no-log-prefix | python3 measure_reduction.py sample.log
docker compose down
```

We measured these numbers with the pinned versions:

| Stage | Records | Reduction |
|---|---:|---:|
| 0. No processors | 11 | 0% |
| 1. `filter/health` | 8 | 27% |
| 2. + `filter/low_value` | 7 | 36% |
| 3. + `log_dedup` | 5 | 55% |
| 4a. + drop the email line | 4 | **64%** |
| 4b. + mask the email (instead of drop) | 5 | **55%** |

The debug output shows the masked email and the count:

```text
Body: Str(INFO account-service password reset for uid=jsmith email=***@***)
Body: Str(WARN payment-service Connection reset by peer while calling downstream billing-api)
     -> log_duplicates: Int(3)
```

!!! info "About the 63% number"
    Other material says "reduce by 63%". That is 7 of 11 lines removed (63.6%). Our script counts 4 of 11 records left with stage 4a, and rounds the reduction to 64%. The number is **measured**, not assumed. With masking (stage 4b) one more line stays, so the saving is 55%.

<!-- TODO: screenshot of the same logs in Dynatrace before and after the processors. Save as docs/assets/lab06-logs.png and link it here. -->

*Screenshot placeholder: the Dynatrace Logs app after stage 4b. 5 records, one with `log_duplicates=3`, and no email.*

In Dynatrace, search for `order-service` again. The email line shows `email=***@***`, and no `/health` lines arrive.

## Stuck?

- **`unsupported protocol scheme ""` errors:** `DT_ENDPOINT` is empty. Use `--env-file ../../.env`. Your records are still counted correctly.
- **The count is lower than expected (for example 3):** the collector did not wait for `log_dedup`. Wait 15 seconds, then measure.
- **The count is the same as before:** you did not use `--force-recreate`, so the old config is still running. Run `docker compose down`, then `up -d` again.
- **`'processors' ... unknown type`:** check that you spelled the name as in the `processors:` section, like `filter/health`.
- **YAML errors:** indentation is part of YAML. Use spaces, not tabs. The config in some older material has wrong indentation (`log_record` must be under `logs`, which is under the processor name).
- **The email is still visible:** you ran stage 1, 2 or 3 only. Add stage 4a or 4b.
- **Validate before you run:**
  ```bash
  docker run --rm -e DT_ENDPOINT=https://x.live.dynatrace.com -e DT_API_TOKEN=x \
    -v "$PWD/collector.yaml:/c.yaml:ro" otel/opentelemetry-collector-contrib:0.162.0 \
    validate --config=/c.yaml
  ```

## Going further

- Use `redaction` instead of `transform`. It is built to hide secrets in **attributes**. Parse the log text into attributes first, then redact them.
- Add a processor that drops all `INFO` lines unless they have `status=500`.
- See more patterns in [dynatrace/demo-opentelemetry-patterns](https://github.com/dynatrace/demo-opentelemetry-patterns).
