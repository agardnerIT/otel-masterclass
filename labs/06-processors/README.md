# Lab 06: Processors

Filter, mask and deduplicate logs in the collector, and measure the reduction.
Full instructions: `docs/labs/06-processors.md` (or the docs site).

```bash
docker compose --env-file ../../.env up -d
sleep 15
docker compose logs collector --no-log-prefix | python3 measure_reduction.py sample.log
docker compose down
```

- `collector.yaml`: starter. Edit the `processors:` list in the pipeline.
- `collector.solution.yaml`: the finished config (use with `docker-compose.solution.yaml`).
- `measure_reduction.py`: counts input lines and exported records.
