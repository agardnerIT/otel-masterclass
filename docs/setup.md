# Setup

Do this before the workshop. It takes about 10 minutes.

## What you need

| Tool | Version | Why |
|---|---|---|
| Docker, including Compose v2 (`docker compose`) | recent | Runs the collector and multi-service labs |
| Python | 3.11 or newer | All code examples |
| Dynatrace tenant + token | optional | See your data in Dynatrace |

## Easiest: GitHub Codespaces or a dev container

Everything below (Docker, Python, the virtual environment, `dtctl`) comes preinstalled, so you can skip to [Download the lab images](#6-download-the-lab-images-at-the-start-of-the-workshop).

1. Do the [Dynatrace step](#3-dynatrace) first. You need **two** tokens:
    - an **access token** (`dt0c01.`) with the three ingest scopes listed there, and
    - a **platform token** (`dt0s16.`) with `storage:logs:read` and `storage:metrics:read`. Create it under **Account Management** > **Platform tokens**. `dtctl` uses it in lab 08.
2. Open the repo: [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/agardnerIT/otel-masterclass)
   Or, locally, open the folder in VS Code and run **Dev Containers: Reopen in Container** (needs Docker Desktop).
3. In Codespaces you are asked for `PARTICIPANT` (your name), `DT_ENDPOINT`, `DT_API_TOKEN` and `DTCTL_PLATFORM_TOKEN`. Paste them in. The setup writes `.env` for you and configures `dtctl`.
4. When the terminal finishes, check the output of the prerequisite check. Re-run it any time: `python scripts/check_prereqs.py`.

!!! note
    Locally, a dev container does not prompt for these values. Fill in `.env` as described in step 3 below, and run `dtctl auth login`.

Prefer to install everything yourself? Continue below.

## 1. Get the code

```bash
git clone https://github.com/agardnerIT/otel-masterclass.git
cd otel-masterclass
```

## 2. Install the tools

- **Docker:** <https://docs.docker.com/get-docker/>. Compose is **included** with Docker Desktop (Windows and macOS) and Rancher Desktop, so there is nothing extra to install. Only on Linux with plain Docker Engine do you add it: `sudo apt install docker-compose-plugin`. The older `docker-compose` command (with a hyphen) does not work for the labs.
- **Python:** <https://www.python.org/downloads/>. The labs use the built-in `venv` and `pip`. You do not need any other Python tool.

## 3. Dynatrace

[Get a free trial here](https://dt-url.net/trial)

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

=== "macOS / Linux"

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

=== "Windows (PowerShell)"

    ```powershell
    py -3 -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```

    !!! tip "`running scripts is disabled on this system`?"
        Your PowerShell blocks activation scripts. Allow them for this terminal only. It needs no admin rights:

        ```powershell
        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
        ```

        If your company blocks that too, skip activation and call the tools directly: `.venv\Scripts\python`, `.venv\Scripts\pip`.

Every lab that runs Python on your machine uses this environment. Turn it on in **every new terminal** by running this from the repo root. After that, `python` works the same on every OS.

=== "macOS / Linux"

    ```bash
    source .venv/bin/activate
    ```

=== "Windows (PowerShell)"

    ```powershell
    .venv\Scripts\Activate.ps1
    ```

## 5. Check everything

=== "macOS / Linux"

    ```bash
    python3 scripts/check_prereqs.py
    ```

=== "Windows (PowerShell)"

    ```powershell
    python scripts\check_prereqs.py
    ```

The check tests more than "is it installed". It also tries the things that go wrong on company laptops: whether Docker can really download from Docker Hub, `ghcr.io` and `gcr.io`, whether a firewall or proxy blocks PyPI, whether PowerShell will run the activation script, whether the lab ports are free, and whether git changed the line endings. It downloads about 65 MB. Add `--quick` to skip that download test.

Fix anything marked `[FAIL]`. A `[WARN]` is fine, but read it: it usually tells you what will go wrong in a later lab. Run the check **before** the workshop. If something fails and you cannot fix it (for example, your company blocks Docker downloads), tell the instructor in advance.

## 6. Download the lab images (at the start of the workshop)

The labs use about 3 GB of Docker images. Do **not** wait until each lab to download them, especially on conference Wi-Fi. **When the workshop starts, open a separate terminal, run this and leave it running while the slides are on.** It downloads and builds everything, in lab order:

=== "macOS / Linux"

    ```bash
    python3 scripts/pull_images.py
    ```

=== "Windows (PowerShell)"

    ```powershell
    python scripts\pull_images.py
    ```

When it prints `All images are ready`, you are set. If the Wi-Fi drops, or a step fails, run it again. It only fetches what is missing. You need about 6 GB of free disk space.

## Stuck?

- **Docker is installed but not running:** start Docker Desktop.
- **`No module named venv` (Linux):** install it, for example `sudo apt install python3-venv`.
- **Dynatrace returns 401/403:** the token is missing a scope. Create a new one.
