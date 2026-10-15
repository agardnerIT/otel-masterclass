# OpenTelemetry Masterclass
We are building a hands on OpenTelemetry masterclass lab. It will be 2-3hrs. Attendees will have their own laptops.

We must assume a mixed OpenTelemetry knowledge so we start at the basics, move quickly (this code will be open sourced after the session so attendees will have access to it to repeat afterwards).

I am most familiar with Python so we use Python as examples throughout unless there's a strong reason not to.

Doccumentation will be build into ./docs folder as mkdocs-material website, we'll use mkdocs gh-deploy to store in gh-pages (the repo is NOT yet configred - I'll do that when we're built).

Audience first language will not be English so keep vocab super simple.

## Proposed Agenda

- Short slides section which explains OTEL as: Telemetry generation, collect and capture, store and analyse, standardisation and control plane
- Generation:
  - Auto instrumentation - Hands on
  - Auto instrumentation expanded (perhaps using something like the RequestsInstrumenter and FastAPI libraries?) - Hands on
  - Manual instrumentation: What extra do you get w/ manual instrumentation? What are the tradeoffs? Hands on
  - OpenTelemetry Injector: This is OpenTelemetry's OneAgent using hte same LD_PRELOAD mechanism for auto injection - Discussion only
  - OpenTelemetry collector - Hands on
    - Filelog receiver + Dynatrace exporter - hands on
    - other receivers
- Collect and capture
  - collector processors (filtering, redaction - see https://github.com/dynatrace/demo-opentelemetry-patterns) - hands on
    - Perhaps we provide these logs and walk through filtering and redaction:
      INFO order-service GET /api/orders/48214 status=200 duration_ms=142
      INFO order-service GET /health status=200 duration_ms=3
      INFO order-service GET /health status=200 duration_ms=1
      WARN payment-service Connection reset by peer while calling downstream billing-api
      WARN payment-service Connection reset by peer while calling downstream billing-api
      WARN payment-service Connection reset by peer while calling downstream billing-api
      DEBUG order-service Cache lookup for key=order:48214 result=miss
      INFO account-service password reset for uid=jsmith email=john.smith999@gmail.com
      INFO payment-service Payment for txn tCode=PYMT-7784-AU amount=129.50 currency=AUD status=200
      INFO order-service GET /api/orders/48214 status=500
      INFO order-service GET /health status=200 duration_ms=2

      With 30 lines of YAML we can reduce by 63%

      receivers:
        filelog:
            include: [file.log]
    processors:
        filter/health:
            logs:
            log_record:
                - 'IsMatch(log.body, ".*GET /health.*")'
        log_dedup:
            log_count_attributes: log_duplicates
            interval: 10s
        filter/low_value:
            logs:
            log_record:
                - 'IsMatch(log.body, "^DEBUG.*")'
        filter/personal_info:
            logs:
            log_record:
                - 'IsMatch(log.body, ".*[pP]assword.*")'
    exporters:
        otlp_http/dynatrace:
            endpoint: https://abc12345.live.dynatrace.com/api/v2/otlp
            headers:
            Authorization: "Api-Token dt0c01.****.****"
    service:
        pipelines:
            logs:
            receivers: [filelog]
            processors: [filter/health, log_dedup, filter/low_value, filter/personal_info]
            exporters: [otlp_http/dynatrace]

  - Semantic conventions (see https://github.com/agardnerIT/otel-weaver-hands-on) - discussion
  - Hands on exercise: Write a log line for a web server that handled a request. Write in whatever format you’d normally use.
      Include:
      What method was used, What status was return, What path was requested, Who the client was (IP)
    This is to demonstrate the disparity of responses and that it'd be hard / impossible to filter for all of these in Dynatrace thus standards are crucial. Leads on to "how"?
- Standardisation
  - Hands on with weaver
- Control plan
  - Above is great but how about doing that at a realistic scale of thousands of collectors. You need a control plane. Perhaps here we can do a hands-on walkthrough of an OpAMP server (see https://github.com/agardnerIT/kcd-indonesia-2026)
  - Then we introduce bindplane
