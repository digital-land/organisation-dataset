.PHONY: init sync collect clobber black clean prune
.SECONDARY:
.DELETE_ON_ERROR:

all: data/organisations.csv

data/organisations.csv:
	mkdir -p data
	python3 bin/organisations.py > data/organisations.py

black:
	black --line-length 100 .

init::
	pip3 install -r requirements.txt

