.PHONY: init sync collect clobber black clean prune
.SECONDARY:
.DELETE_ON_ERROR:

SPARQL_DIR=sparql/
DATA_DIR=data/
REGISTER_DIR=collection/register/
WIKIDATA_DIR=collection/wikidata/
OPENDATACOMMUNITIES_DIR=collection/opendatacommunities/
PATCH_DIR=patch/
COLLECTION_DIR=collection/

TARGETS:=\
	collection/organisation.csv\
	collection/organisation-tag.csv

all: $(TARGETS)

collection/organisation.csv:	$(SOURCE_DATA) bin/organisations.py
	mkdir -p collection
	python3 bin/organisations.py > $@

collection/organisation-tag.csv:	data/tag.csv
	cp data/tag.csv $@

black:
	black .

init::
	pip3 install -r requirements.txt

clean::
	rm -rf ./collection

clobber::
	rm -f $(TARGETS)
