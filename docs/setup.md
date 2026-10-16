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
git clone https://github.com/agardnerIT/otel-masterclass.git
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

## 4. Python environment

Create one virtual environment for **all** the labs and install every Python package once. Do this from the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\activate
```

Labs 01, 08 and 09 run Python on your machine and use this environment. Turn it on in every new terminal by running this from the repo root. Labs that run in Docker build their own images and do not need it.

```bash
source .venv/bin/activate
```

## 5. Check everything

```bash
./scripts/check-prereqs.sh
```

Or run:

```bash
make check
```

Fix anything marked `[FAIL]`. A `[WARN]` is fine.

## Stuck?

- **Docker is installed but not running:** start Docker Desktop.
- **`No module named venv` (Linux):** install it, for example `sudo apt install python3-venv`.
- **Dynatrace returns 401/403:** the token is missing a scope. Create a new one.
