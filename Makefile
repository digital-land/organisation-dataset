.PHONY: init sync collect clobber black clean prune
.SECONDARY:
.DELETE_ON_ERROR:

DATA=\
	data/development-corporation.csv\
	data/statistical-geography.csv\
	data/website.csv

all: data/organisations.csv

data/organisations.csv:	$(DATA)
	mkdir -p collection
	python3 bin/organisations.py > collection/organisations.csv

black:
	black --line-length 100 .

init::
	pip3 install -r requirements.txt

