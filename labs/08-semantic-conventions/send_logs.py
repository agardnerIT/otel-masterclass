"""Send a log file to Dynatrace as OpenTelemetry logs.

Usage: python3 send_logs.py messy.log
       python3 send_logs.py standardised.log

messy.log:        each line is sent as plain text, as most teams do today.
standardised.log: each key=value pair becomes an attribute on the log record.

Needs DT_ENDPOINT and DT_API_TOKEN (see docs/setup.md). Token scope: logs.ingest
"""
import logging
import os
import sys
import time

from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import LogRecordExportResult, SimpleLogRecordProcessor
from opentelemetry.sdk.resources import Resource

path = sys.argv[1]
service = "semconv-" + os.path.basename(path).removesuffix(".log")
parse = path.endswith("standardised.log")

failures = []


class CheckedExporter(OTLPLogExporter):
    """The SDK hides export errors. Remember them, so we can report them."""

    def export(self, batch):
        result = super().export(batch)
        if result != LogRecordExportResult.SUCCESS:
            failures.append(result)
        return result


exporter = CheckedExporter(
    endpoint=os.environ["DT_ENDPOINT"].rstrip("/") + "/api/v2/otlp/v1/logs",
    headers={"Authorization": "Api-Token " + os.environ["DT_API_TOKEN"]},
)
provider = LoggerProvider(resource=Resource.create({"service.name": service}))
provider.add_log_record_processor(SimpleLogRecordProcessor(exporter))
logger = logging.getLogger("semconv")
logger.setLevel(logging.INFO)
logger.addHandler(LoggingHandler(logger_provider=provider))

for line in open(path).read().splitlines():
    attrs = {}
    if parse:
        attrs = dict(pair.split("=", 1) for pair in line.split())
        # status code is a number, so queries can compare it
        attrs["http.response.status_code"] = int(attrs["http.response.status_code"])
    logger.info(line, extra=attrs)

provider.shutdown()
time.sleep(1)
total = len(open(path).read().splitlines())
if failures:
    sys.exit(f"FAILED: {len(failures)} of {total} logs were rejected. Check DT_ENDPOINT and the logs.ingest scope.")
print(f"Sent {total} logs with service.name={service}")
