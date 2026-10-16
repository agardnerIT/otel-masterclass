# The supervisor image doesn't contain a collector, so borrow the binary from the contrib image.
FROM otel/opentelemetry-collector-contrib:0.162.0 AS collector

FROM ghcr.io/open-telemetry/opentelemetry-collector-releases/opentelemetry-collector-opampsupervisor:0.162.0
COPY --from=collector /otelcol-contrib /otelcol-contrib
COPY supervisor.yaml collector.yaml /etc/opampsupervisor/

USER root
RUN mkdir -p /var/lib/otelcol/supervisor /var/lib/otelcol/filelog \
 && chown -R 10001:10001 /var/lib/otelcol
USER opampsupervisor

ENTRYPOINT ["opampsupervisor", "--config", "/etc/opampsupervisor/supervisor.yaml"]
