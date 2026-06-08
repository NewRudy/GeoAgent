PYTHON ?= python

.PHONY: smoke validate

smoke:
	$(PYTHON) -m geoagent.smoke

validate:
	$(PYTHON) -m geoagent.smoke --no-write
	$(PYTHON) -m pytest tests/test_smoke_command.py -v --tb=short
