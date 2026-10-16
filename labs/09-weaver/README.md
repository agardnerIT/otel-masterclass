# 09-weaver

Files for the [Lab 09: Weaver](../../docs/labs/09-weaver.md) page.

- `model/`: the ACME registry. Defines `acme.cost.code` and imports the OpenTelemetry conventions.
- `policies/cost_code.rego`: the rules for the **value** of `acme.cost.code`.
- `emit_test_logs.py`: sends 3 test logs to Weaver.

Based on [agardnerIT/otel-weaver-hands-on](https://github.com/agardnerIT/otel-weaver-hands-on).
