"""The same frontend, but OpenTelemetry is set up in code (no agent)."""
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app import app

# 1. The SDK: who we are, and where spans go.
provider = TracerProvider(
    resource=Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "frontend")})
)
if os.getenv("OTEL_TRACES_EXPORTER") == "otlp":
    exporter = OTLPSpanExporter()  # reads the endpoint and headers from OTEL_EXPORTER_OTLP_*
else:
    exporter = ConsoleSpanExporter()
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

# 2. The instrumentation libraries: you turn them on yourself.
FastAPIInstrumentor.instrument_app(app)  # one span for each incoming request
RequestsInstrumentor().instrument()      # one span for each outgoing request
