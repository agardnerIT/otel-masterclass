FROM otel/opentelemetry-collector-builder:0.162.0 AS build
WORKDIR /build
COPY builder-config.yaml .
RUN CGO_ENABLED=0 ocb --config=builder-config.yaml

FROM gcr.io/distroless/static-debian12
COPY --from=build /build/out/otelcol-masterclass /otelcol-masterclass
ENTRYPOINT ["/otelcol-masterclass"]
