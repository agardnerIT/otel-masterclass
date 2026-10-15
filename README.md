# OpenTelemetry Masterclass

A hands-on workshop (2-3 hours) that teaches OpenTelemetry with Python and Dynatrace.
You will generate telemetry, collect it, process it, standardise it, and manage it at scale.

Everything here is open source (Apache 2.0). Each lab runs from a clean clone, so you can repeat it at home.

## Read the docs

```
pip install -r requirements-docs.txt
mkdocs serve
```

Then open http://127.0.0.1:8000.

## Before you start

```
cp .env.example .env     # add your Dynatrace details (optional)
./scripts/check-prereqs.sh
```

No Dynatrace tenant? Every lab has a console fallback.

## Layout

| Folder | Content |
|---|---|
| `docs/` | The workshop website (mkdocs-material) |
| `labs/` | Code for each lab |
| `scripts/` | Helper scripts |
