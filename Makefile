MODULE := check_trains.py
TESTS  := tests

lint:
	pycodestyle $(MODULE) $(TESTS)
	pydocstyle $(MODULE) $(TESTS)

test:
	pytest $(TESTS)
