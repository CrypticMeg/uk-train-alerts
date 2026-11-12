POC     := check_trains.py
PACKAGE := train_alerts
TESTS   := tests

.PHONY: check lint test test-smoke test-unit test-acceptance

check: lint test

lint:
	pycodestyle $(POC) $(PACKAGE) $(TESTS)
	pydocstyle $(POC) $(PACKAGE) $(TESTS)

test: test-smoke test-unit test-acceptance

test-smoke:
	pytest $(TESTS)/smoke

test-unit:
	pytest $(TESTS)/unit

test-acceptance:
	pytest $(TESTS)/acceptance
