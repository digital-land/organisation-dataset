.PHONY: init sync collect clobber black clean prune
.SECONDARY:
.DELETE_ON_ERROR:

TARGETS=collection/organisation.csv

all: $(TARGETS)

collection/organisation.csv:	data/organisation.csv bin/organisations.py
	mkdir -p collection
	python3 bin/organisations.py > $@

black:
	black .

init::
	pip3 install -r requirements.txt

clobber::
	rm -f $(TARGETS)
