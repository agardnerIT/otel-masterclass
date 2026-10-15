#!/usr/bin/env bash
# Checks that the tools needed for the labs are installed.
# Usage: ./scripts/check-prereqs.sh   (or: make check)

cd "$(dirname "$0")/.." || exit 1
fail=0
ok()   { printf '  [ OK ] %s\n' "$1"; }
bad()  { printf '  [FAIL] %s\n' "$1"; fail=1; }
warn() { printf '  [WARN] %s\n' "$1"; }

echo "Checking prerequisites..."

# Docker
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    ok "docker is installed and running ($(docker --version | cut -d, -f1))"
  else
    bad "docker is installed but not running. Start Docker Desktop (or your Docker daemon)."
  fi
  if docker compose version >/dev/null 2>&1; then
    ok "docker compose ($(docker compose version --short))"
  else
    bad "docker compose plugin not found. See https://docs.docker.com/compose/install/"
  fi
else
  bad "docker not found. Install from https://docs.docker.com/get-docker/"
fi

# Python 3.11+
py=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1; then py="$c"; break; fi
done
if [ -n "$py" ]; then
  if "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    ok "python $("$py" -c 'import platform; print(platform.python_version())')"
  else
    bad "python 3.11 or newer is needed (found $("$py" --version 2>&1))"
  fi
else
  bad "python not found. Install Python 3.11 or newer."
fi

# venv + pip (the labs use a plain virtual environment)
if [ -n "$py" ]; then
  if "$py" -c 'import venv, ensurepip' >/dev/null 2>&1; then
    ok "python venv and pip"
  else
    bad "python venv/pip missing. On Debian/Ubuntu: sudo apt install python3-venv"
  fi
fi

# curl
if command -v curl >/dev/null 2>&1; then ok "curl"; else bad "curl not found."; fi

# Dynatrace settings (optional)
if [ -f .env ]; then
  set -a; . ./.env; set +a
  if [ -n "${DT_ENDPOINT:-}" ] && [ -n "${DT_API_TOKEN:-}" ] \
     && [[ "$DT_ENDPOINT" != *YOUR_TENANT* ]] && [[ "$DT_API_TOKEN" != *REPLACE_ME* ]]; then
    ok ".env has DT_ENDPOINT and DT_API_TOKEN"
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 \
      -X POST "${DT_ENDPOINT%/}/api/v2/otlp/v1/traces" \
      -H "Authorization: Api-Token ${DT_API_TOKEN}" \
      -H "Content-Type: application/x-protobuf" --data-binary '')
    case "$code" in
      200|400) ok "Dynatrace accepts the token for OTLP ingest (HTTP $code)" ;;
      401|403) bad "Dynatrace rejected the token (HTTP $code). Check the token scopes in docs/setup.md." ;;
      000)     warn "Could not reach $DT_ENDPOINT. Check your network. You can still use the console fallback." ;;
      *)       warn "Unexpected answer from Dynatrace (HTTP $code)." ;;
    esac
  else
    warn ".env exists but DT_ENDPOINT / DT_API_TOKEN are not set. Labs will use the console fallback."
  fi
else
  warn "No .env file. Labs will use the console fallback. To use Dynatrace: cp .env.example .env"
fi

echo
if [ "$fail" -eq 0 ]; then echo "All required checks passed."; else echo "Some checks failed. Fix them and run again."; fi
exit "$fail"
