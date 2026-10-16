package live_check_advice

import rego.v1

deny contains make_finding(id, level, context, message) if {
	input.sample.attribute
	input.sample.attribute.name == "acme.cost.code"
	is_string(input.sample.attribute.value)
	not regex.match(`^[A-Z]{3}[0-9]{4}$`, input.sample.attribute.value)
	id := "invalid_cost_code"
	level := "violation"
	context := {"attribute_name": input.sample.attribute.name}
	message := sprintf("acme.cost.code value '%s' does not match ^[A-Z]{3}[0-9]{4}$", [input.sample.attribute.value])
}

# Every log record must carry acme.cost.code
deny contains make_finding(id, level, context, message) if {
	input.sample.log
	not has_cost_code(input.sample.log.attributes)
	id := "missing_cost_code"
	level := "violation"
	context := {"attribute_name": "acme.cost.code"}
	message := "Log record is missing required attribute 'acme.cost.code'"
}

has_cost_code(attributes) if {
	some attr in attributes
	attr.name == "acme.cost.code"
}

make_finding(id, level, context, message) := {
	"id": id,
	"level": level,
	"context": context,
	"message": message,
}
