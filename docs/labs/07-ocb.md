# Lab 07: Custom collector with OCB

**Time: 10-15 minutes**

## Goal

Build your own collector that contains only the components you need. Run the Lab 06 pipeline on it and compare the image size with the contrib image.

## Why it matters

The contrib image has hundreds of components. You use a handful, but you ship and patch all of them. A smaller collector starts faster, has a smaller attack surface, and is easier to review. It is also the only way to use a component that no ready-made image includes.

The tool for this is the **OpenTelemetry Collector Builder**, called **OCB** (`ocb`). You give it a list of components. It generates Go code and compiles one binary.

## Steps

The lab files are in `labs/07-ocb/`. Docker must be running. You do **not** need Go: the build runs inside Docker.

1. Go to the lab folder:
   ```bash
   cd labs/07-ocb
   ```
2. Open `builder-config.yaml`. This is the **manifest**. It lists every component. Each `gomod` line is a Go module and a version:
   ```yaml
   processors:
     - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/processor/filterprocessor v0.162.0
     - gomod: github.com/open-telemetry/opentelemetry-collector-contrib/processor/logdedupprocessor v0.162.0
   ```
   It has the two receivers, two processors and two exporters that Lab 06 needs. Nothing else.
3. Open `Dockerfile`. It has two stages. The first runs `ocb` to compile the collector. The second copies only the binary into a tiny image.
4. Build it. This downloads and compiles Go code, so it takes 2-3 minutes:
   ```bash
   docker compose build
   ```
5. List the components inside your new collector:
   ```bash
   docker run --rm otelcol-masterclass:0.162.0 components
   ```
   You should see `file_log` and `otlp`, then `filter` and `log_dedup`, then `debug` and `otlp_http`. Nothing more.
6. Compare the size with the contrib image from Lab 06:
   ```bash
   docker images | grep -E "otelcol-masterclass|opentelemetry-collector-contrib"
   ```
   There are two size columns:

    - **DISK USAGE** is the unpacked size on your machine. This is the number we compare.
    - **CONTENT SIZE** is the compressed size, close to what you download from a registry.

   Your collector is much smaller in both.<br /><br />
7. Run the Lab 06 pipeline on your collector. `collector.yaml` here is the Lab 06 solution.
   ```bash
   docker compose --env-file ../../.env up -d
   ```
??? note "No Dynatrace tenant?"
       ```bash
       export DT_ENDPOINT=http://localhost:1 DT_API_TOKEN=x
       docker compose up -d
       ```
       The Dynatrace exporter will print errors. Ignore them.
8. Wait 15 seconds. Then measure:
   ```bash
   docker compose logs collector --no-log-prefix | python3 measure_reduction.py sample.log
   ```
9. Clean up:
   ```bash
   docker compose down
   ```

## Expected result

- The `components` list has exactly the 6 components in the manifest.
- Your image is about **62 MB** on disk. The contrib image is about **482 MB**.
- The measure script shows 11 input lines, 4 records exported (a 64% reduction), and no email, `/health` or `DEBUG` lines. It is the same result as Lab 06, from a much smaller collector.

## Stuck?

| Problem | Fix |
|---|---|
| `unknown type: "filelog"` | Component names use an underscore in this version: `file_log`. See [Lab 05](05-collector-basics.md#which-collector-image). |
| `unknown type` for any component | The component is not in `builder-config.yaml`. Add its `gomod` line and run `docker compose build` again. |
| Build fails with a network error | The build downloads Go modules. Check your connection or proxy and try again. |
| Version mismatch error | Keep the `v0.162.0` version the same on every line, and the same as `dist.version`. |

## Going further

- Add the `host_metrics` receiver. Find its `gomod` line on [opentelemetry.io/ecosystem/registry](https://opentelemetry.io/ecosystem/registry/), add it to the manifest, rebuild, and check it with `components`.
- Run the builder with `--skip-compilation` to see the generated Go code.
