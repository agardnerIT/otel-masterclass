# pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc
import logging
import time

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor
from opentelemetry.sdk.resources import Resource

ENDPOINT = "http://localhost:4317"

# Each case is (service.name, attributes set on the log record)
CASES = {
    "good": ("team-a", {"acme.cost.code": "ABC1234"}),
    "bad-format": ("team-b", {"acme.cost.code": "abc-12"}),
    "wrong-key": ("team-c", {"cost-code": "ABC1234"}),
}

for name, (service, attrs) in CASES.items():
    print(f"=== Sending: {name} log with attributes: {attrs} to Weaver ===")
    provider = LoggerProvider(resource=Resource.create({"service.name": service}))
    provider.add_log_record_processor(
        SimpleLogRecordProcessor(OTLPLogExporter(endpoint=ENDPOINT, insecure=True))
    )
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(LoggingHandler(logger_provider=provider))
    logger.info("test log from %s", name, extra=attrs)
    provider.shutdown()
    time.sleep(0.5)
