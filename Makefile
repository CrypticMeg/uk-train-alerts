POC     := check_trains.py
PACKAGE := train_alerts
TESTS   := tests

.PHONY: lint test test-smoke test-acceptance

lint:
	pycodestyle $(POC) $(PACKAGE) $(TESTS)
	pydocstyle $(POC) $(PACKAGE) $(TESTS)

test: test-smoke test-acceptance

test-smoke:
	pytest $(TESTS)/smoke

test-acceptance:
	pytest $(TESTS)/acceptance
