# Setup

Do this before the workshop. It takes about 10 minutes.

## What you need

| Tool | Version | Why |
|---|---|---|
| Docker (with Compose) | recent | Runs the collector and multi-service labs |
| Python | 3.11 or newer | All code examples |
| Dynatrace tenant + token | optional | See your data in Dynatrace |

## 1. Get the code

```bash
git clone https://github.com/CHANGE_ME/otel-masterclass.git
cd otel-masterclass
```

## 2. Install the tools

- **Docker:** <https://docs.docker.com/get-docker/>
- **Python:** <https://www.python.org/downloads/>. The labs use the built-in `venv` and `pip`. You do not need any other Python tool.

## 3. Dynatrace (optional)

No tenant? Skip this step. Each lab can print telemetry to the console instead.

1. Create an API token: **Access Tokens** > **Generate new token**.
2. Add these scopes:
    - `openTelemetryTrace.ingest`
    - `metrics.ingest`
    - `logs.ingest`
3. Copy the settings file and fill it in:
   ```bash
   cp .env.example .env
   ```
   ```
   DT_ENDPOINT=https://abc12345.live.dynatrace.com
   DT_API_TOKEN=dt0c01.xxxx.xxxx
   ```

4. Install `dtctl`, the Dynatrace command line tool. Lab 08 (Semantic conventions) uses it to run DQL queries. Follow the instructions at <https://github.com/dynatrace-oss/dtctl>, then log in:
   ```bash
   dtctl auth login
   ```

!!! warning
    Never commit `.env`. It is already in `.gitignore`.

## 4. Check everything

```bash
./scripts/check-prereqs.sh
```

(or `make check`). Fix anything marked `[FAIL]`. A `[WARN]` is fine.

## Stuck?

- **Docker is installed but not running:** start Docker Desktop.
- **`No module named venv` (Linux):** install it, for example `sudo apt install python3-venv`.
- **Dynatrace returns 401/403:** the token is missing a scope. Create a new one.
