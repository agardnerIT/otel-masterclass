.PHONY: check docs
check:
	./scripts/check-prereqs.sh
docs:
	mkdocs serve
