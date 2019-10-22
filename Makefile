.PHONY: init sync collect clobber black clean prune
.SECONDARY:
.DELETE_ON_ERROR:

all: collect

collect:
	python3 organisations.py

black:
	black .

init::
	pip3 install -r requirements.txt

