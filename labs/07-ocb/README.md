# Lab 07: Custom collector with OCB

Build a small collector with the OpenTelemetry Collector Builder and run the Lab 06 pipeline on it.
Full instructions: `docs/labs/07-ocb.md` (or the docs site).

```bash
docker compose build        # 2-3 minutes
docker run --rm otelcol-masterclass:0.162.0 components
docker compose --env-file ../../.env up -d
sleep 15
docker compose logs collector --no-log-prefix | python measure_reduction.py sample.log
docker compose down
```

- `builder-config.yaml`: the OCB manifest (the list of components).
- `Dockerfile`: builds the collector with `ocb`, then copies the binary into a small image.
- `collector.yaml`: the Lab 06 solution pipeline.
