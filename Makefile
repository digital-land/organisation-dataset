.PHONY: init sync collect clobber black clean prune
.SECONDARY:
.DELETE_ON_ERROR:

all: collection/organisation.csv

collection/organisation.csv:	data/organisation.csv bin/organisations.py
	mkdir -p collection
	python3 bin/organisations.py > $@

black:
	black --line-length 100 .

init::
	pip3 install -r requirements.txt

