# Lab 08: Semantic conventions

**Time: 15 minutes** (discussion and exercise)

## Goal

Find out for yourself why shared attribute names matter. Write one log line, compare it with the rest of the room, then run one query across messy and standard logs.

## Why it matters

Your company has many teams, and every team writes telemetry. Does it all look the same? Let's find out.

!!! warning "Do the exercise first"
    Do not read past Part 1 until you have finished it. Later parts reveal the point of the exercise.

## Part 1: Exercise (5 minutes)

On paper or in a text editor, write **one log line** for a web server that handled a request. Use the format you normally use at work. Include:

- the HTTP method
- the status that was returned
- the path that was requested
- who the client was (IP address)

Now compare with the person next to you. Did you use the same order? The same words? The same format?

Keep your line. You need it in a minute.

## Part 2: Discuss (5 minutes)

Look at the lines in the room. Different order, different words, different formats. Now imagine one question for all of them: "show me all server errors". You need one query for each team. Dashboards, alerts and AI tools all break the same way.

**Semantic conventions** are the fix. They are a list of standard names and meanings for common things, such as an HTTP request. They are part of OpenTelemetry. If everyone uses the same name, one query works for everyone.

OpenTelemetry already has conventions for HTTP, databases, messaging, cloud, Kubernetes, GenAI and more. Here are the four we use in this section:

| Meaning | Standard name | Example |
|---|---|---|
| HTTP method | `http.request.method` | `GET` |
| HTTP status code | `http.response.status_code` | `500` |
| URL path | `url.path` | `/api/orders` |
| Client IP address | `client.address` | `10.0.0.5` |

You have already used them. In [Lab 01](01-auto-instrumentation.md), the auto instrumentation set `http.request.method` and `http.response.status_code` on the spans for you. That is why `OTEL_SEMCONV_STABILITY_OPT_IN: http` is in the Docker Compose files: it selects the new, stable HTTP names.

Browse the full list: [opentelemetry.io/docs/specs/semconv](https://opentelemetry.io/docs/specs/semconv/).

!!! info "What is in a convention?"
    A convention is not only a name. It also says the **type** (string, number), the **meaning**, example values, and how stable it is (`stable` or `development`).

Rewrite your own line from Part 1 with these four names. How different is it from what you wrote?

## Part 3: Try one query (5 minutes)

Now see the problem in a real backend. You send the **same 7 requests** to Dynatrace twice, once from the messy logs and once from the standardised logs. Then you ask one question of both with DQL (Dynatrace Query Language), using the `dtctl` command line tool.

You need Python 3.11+, a Dynatrace tenant and `dtctl`. See [Setup](../setup.md#3-dynatrace-optional). The token needs the `logs.ingest` scope. No tenant? Use the fallback at the end of this part.

1. Go to the folder and turn on the virtual environment from [Setup](../setup.md#4-python-environment):

    === "macOS / Linux"

        ```bash
        cd labs/08-semantic-conventions
        source ../../.venv/bin/activate
        ```

    === "Windows (PowerShell)"

        ```powershell
        cd labs\08-semantic-conventions
        ..\..\.venv\Scripts\Activate.ps1
        ```

2. Read `messy.log`. These are 7 logs from 7 "teams". All 7 are the same kind of event: a handled HTTP request.
   ```text
   GET /api/orders 200 from 10.0.0.5
   [checkout] method=POST path=/pay status_code=500 client=10.0.0.9
   2026-10-16 INFO order-svc: user at 10.0.0.7 requested GET /api/orders/42 -> HTTP 404
   {"verb":"GET","uri":"/health","code":200,"ip":"10.0.0.5"}
   inventory: 10.0.0.8 "PUT /stock/7" 503
   {"verb":"POST","uri":"/pay","code":502,"ip":"10.0.0.9"}
   payment-svc: http.request.method=POST url.path=/refund http.response.status_code=200 client.address=10.0.0.9
   ```
   Three of them are server errors (`500`, `503`, `502`).
3. Send both files to Dynatrace. `messy.log` is sent as plain text, one line per log record. `standardised.log` has the same 7 requests, but each name becomes an attribute. The script reads `DT_ENDPOINT` and `DT_API_TOKEN` from the `.env` file in the repo root:
   ```bash
   python send_logs.py messy.log
   python send_logs.py standardised.log
   ```
   You should see `Sent 7 logs` twice. Wait about 30 seconds for the logs to arrive.
4. First check that the messy logs arrived. If `dtctl` says `token ... not found`, log in first:
   ```bash
   dtctl auth login
   ```
   Then run the query:
   ```bash
   dtctl query 'fetch logs
   | filter service.name == "semconv-messy"
   | fields timestamp, content'
   ```
   You should see all 7 lines, as plain text.
5. Now ask for the server errors in the **messy** logs. The query uses the standard name `http.response.status_code` and a value of 500 or more. `toLong` turns the value into a number, because Dynatrace shows it as text:
   ```bash
   dtctl query 'fetch logs
   | filter service.name == "semconv-messy"
   | filter toLong(http.response.status_code) >= 500'
   ```
   You should get **no records** (`No resources found.`). The 7 logs are there, and 3 of them are real errors, but the query finds none.
6. Run the **same query** on the standardised logs. Only the `service.name` is different:
   ```bash
   dtctl query 'fetch logs
   | filter service.name == "semconv-standardised"
   | filter toLong(http.response.status_code) >= 500
   | fields timestamp, content, http.request.method, url.path, http.response.status_code'
   ```
   You should get 3 records: the `500`, the `502` and the `503`.

The query did not change. Only the names did.

??? note "No Dynatrace tenant? Run the query on your laptop"
    `count_errors.py` runs the same rule on the files, with no network:
    ```bash
    python count_errors.py messy.log
    python count_errors.py standardised.log
    ```
    You should see `Server errors found: 0`, then `Server errors found: 3`.

## Expected result

| Data | Server errors found | Real server errors |
|---|---:|---:|
| `semconv-messy` | 0 | 3 |
| `semconv-standardised` | 3 | 3 |

To make the first one work, you would need a different rule for every team, and a new rule every time a new team starts. That does not scale.

## Stuck?

- **`python: command not found`:** the virtual environment is not on. See [Setup](../setup.md#4-python-environment).
- **The standardised query finds nothing:** the logs can take a minute to arrive. Check the time range, and that the token has `logs.ingest`. Check that `toLong(...)` is in the query: without it, text is compared to a number and nothing matches.
- **You get 6 or 9 records, not 3:** you ran `send_logs.py` more than once. Each run adds the same logs again. Add `from:-10m` after `fetch logs` to see only the latest.
- **`send_logs.py` fails with `KeyError: 'DT_ENDPOINT'`:** the script found no `.env` file, or it has no `DT_ENDPOINT`. Check `.env` in the repo root. See [Setup](../setup.md).
- **The messy query returns records:** you changed `messy.log`, or you sent a file twice with a different name.

## Going further

- Look at your own logs. Which standard names could you use? Search the [attribute registry](https://opentelemetry.io/docs/specs/semconv/attributes-registry/).
- You do not have a convention for something, for example a **cost code** or a **team name**? You can write your own. But how do you make sure everyone uses it correctly? Next: [Lab 09: Weaver](09-weaver.md).
