# Lab 06: Processors

**Time: 25 minutes**

## Goal

Add processors to the collector from Lab 05. Drop log lines you do not need, hide an email address, and collapse repeated lines. Measure how much data you save.

Let's reduce log volume by **64%**

## Why it matters

Many backends charge by volume, and some log lines add little value: health checks, debug output, the same error 1000 times. Logs can also hold personal data that must not leave your network. A processor fixes this **before** the data leaves the collector. The app does not change.

## The logs

`sample.log` (in `labs/06-processors`, which you open in the steps below) has 11 lines. Read them and find the problems:

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
    This lab uses the **contrib** image (`0.162.0`). The Dynatrace distro has `filter`, `transform` and `redaction`, but not `log_dedup`. See the table in [Lab 05](05-collector-basics.md#which-collector-image). Contrib is bigger, so [Lab 07](07-ocb.md) shows how to build your own.

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
   docker compose logs collector --no-log-prefix | python3 measure_reduction.py sample.log
   ```
   The script counts the lines in `sample.log` and the records the collector exported. You should see 11 records, 0% reduction, and `Email visible: YES (leak!)`.
5. Stop the collector. Do this before every change:
   ```bash
   docker compose down
   ```

You will now add each processor one by one and measure the reduction in log volume. The reduction percentage will increase each time we add a new processor.

### Exercise 1: Filter out health pings

Edit the `processors:` list in `collector.yaml`. Change:

```yaml
processors: []
```

to:

```yaml
processors: [filter/health]
```

Then run:

```bash
docker compose --env-file ../../.env up -d --force-recreate
```

Now run the measure command:

```bash
docker compose logs collector --no-log-prefix | python3 measure_reduction.py sample.log
```

You should see the logs have dropped from 11 to 8 (a 27% reduction) and the /health pings are no longer visible.


and run

```bash
docker compose down
```

### Exercise 2: Also filter out DEBUG logs

Edit `processors` in `collector.yaml` again and change:

```yaml
processors: [filter/health]
```

to:

```yaml
processors: [filter/health, filter/low_value]
```
Then run:

```bash
docker compose --env-file ../../.env up -d --force-recreate
```

Wait 15 seconds, run the measure command:

```bash
docker compose logs collector --no-log-prefix | python3 measure_reduction.py sample.log
```

You should see `11` logs have now been reduced to `7` (a `36%` reduction) and the `DEBUG` lines are no longer present in the collector output.

### Exercise 3: Also deduplicate identical logs

Edit `processors` in `collector.yaml` again and change:

```yaml
processors: [filter/health, filter/low_value]
```

to:

```yaml
processors: [filter/health, filter/low_value, log_dedup]
```
Then run:

```bash
docker compose --env-file ../../.env up -d --force-recreate
```

Run the measure command:

```bash
docker compose logs collector --no-log-prefix | python3 measure_reduction.py sample.log
```

You should see `11` logs have now been reduced to `5` (a `55%` reduction).

### Exercise 4: Also drop the line with personal data

Edit `processors` in `collector.yaml` again and change:

```yaml
processors: [filter/health, filter/low_value, log_dedup]
```

to:

```yaml
processors: [filter/health, filter/low_value, log_dedup, filter/personal_info]
```
Then run:

```bash
docker compose --env-file ../../.env up -d --force-recreate
```

Wait 15 seconds, run the measure command:

```bash
docker compose logs collector --no-log-prefix | python3 measure_reduction.py sample.log
```

You should see `11` logs have now been reduced to `4` (a `64%` reduction) and `Email visible: no`. The whole password reset line is gone.

Run:

```bash
docker compose down
```

### Exercise 5: Mask the email instead of dropping the line

Dropping the line also hides the fact that a password reset happened. Edit `processors` in `collector.yaml` again and change:

```yaml
processors: [filter/health, filter/low_value, log_dedup, filter/personal_info]
```

to:

```yaml
processors: [filter/health, filter/low_value, log_dedup, transform/mask_email]
```
Then run:

```bash
docker compose --env-file ../../.env up -d --force-recreate
```

Wait 15 seconds, run the measure command:

```bash
docker compose logs collector --no-log-prefix | python3 measure_reduction.py sample.log
```

You should see `11` logs have now been reduced to `5` (a `55%` reduction). The measure script reports `Email visible: no`. The password reset line is still there. To see the masked text in the collector's debug output, run:

```bash
docker compose logs collector --no-log-prefix | grep "password reset"
```

You should see `email=***@***` in the line.

Run:

```bash
docker compose down
```

### Summary


| Stage | `processors:` list | What it does |
|---|---|---|
| 1 | `[filter/health]` | Drops the 3 health checks |
| 2 | `[filter/health, filter/low_value]` | Also drops the DEBUG line |
| 3 | `[filter/health, filter/low_value, log_dedup]` | Collapses 3 identical warnings into 1 |
| 4 | `[filter/health, filter/low_value, log_dedup, filter/personal_info]` | **Drops** the line that has an email |
| 5 | `[filter/health, filter/low_value, log_dedup, transform/mask_email]` | **Masks** the email, keeps the line |

Stages 4 and 5 are two answers to the same problem. Exercise 5 replaces the filter from Exercise 4 with a mask.

??? note "Why does `log_dedup` wait 10 seconds?"
    `log_dedup` holds records for a time window (`interval: 10s`) and counts the identical ones. At the end of the window it sends **one** record with an attribute `log_duplicates: 3`. This is why we wait before we measure. It is also why `log_dedup` goes after the first two filters: there is no reason to count records you will drop.

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

Run the finished config (stage 5) to check:

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
| 4. + drop the email line | 4 | **64%** |
| 5. + mask the email (instead of drop) | 5 | **55%** |

The debug output (`docker compose logs collector --no-log-prefix`, before `docker compose down`) shows the masked email and the count:

```text
Body: Str(INFO account-service password reset for uid=jsmith email=***@***)
Body: Str(WARN payment-service Connection reset by peer while calling downstream billing-api)
     -> log_duplicates: Int(3)
```

!!! info "About the 63% number"
    Other material says "reduce by 63%". That is 7 of 11 lines removed (63.6%). Our script counts 4 of 11 records left with stage 4, and rounds the reduction to 64%. The number is **measured**, not assumed. With masking (stage 5) one more line stays, so the saving is 55%.

<!-- TODO: screenshot of the same logs in Dynatrace before and after the processors. Save as docs/assets/lab06-logs.png and link it here. -->

*Screenshot placeholder: the Dynatrace Logs app after stage 5. 5 records, one with `log_duplicates=3`, and no email.*

In Dynatrace, search for `order-service` again. The email line shows `email=***@***`, and no `/health` lines arrive.

## Stuck?

- **`unsupported protocol scheme ""` errors:** `DT_ENDPOINT` is empty. Use `--env-file ../../.env`. Your records are still counted correctly.
- **The count is lower than expected (for example 3):** the collector did not wait for `log_dedup`. Wait 15 seconds, then measure.
- **The count is the same as before:** you did not use `--force-recreate`, so the old config is still running. Reset and start again:
  ```bash
  docker compose down
  docker compose up -d
  ```
- **`'processors' ... unknown type`:** check that you spelled the name as in the `processors:` section, like `filter/health`.
- **YAML errors:** indentation is part of YAML. Use spaces, not tabs. The config in some older material has wrong indentation (`log_record` must be under `logs`, which is under the processor name).
- **The email is still visible:** you ran stage 1, 2 or 3 only. Add stage 4 or 5.
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
