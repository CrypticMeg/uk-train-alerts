MODULE := check_trains.py

lint:
	pycodestyle $(MODULE)
	pydocstyle $(MODULE)

test:
	pytest $(MODULE)
