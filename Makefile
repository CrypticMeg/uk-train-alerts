POC     := check_trains.py
PACKAGE := train_alerts
TESTS   := tests

.PHONY: check lint test test-smoke test-unit test-acceptance release

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

release:
	@echo "release: not implemented until Debian packaging exists" >&2
	@exit 1
