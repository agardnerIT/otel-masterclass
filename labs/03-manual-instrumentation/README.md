# Lab 03: Manual instrumentation

Full instructions: `docs/labs/03-manual-instrumentation.md` (or the docs site).

Stop Lab 02 first. Both labs use ports 9000 and 9001.

Run the starter backend:

```bash
cd labs/03-manual-instrumentation
docker compose --env-file ../../.env up --build
```

Run the solution backend:

```bash
docker compose --env-file ../../.env -f docker-compose.yaml -f docker-compose.solution.yaml up --build
```
