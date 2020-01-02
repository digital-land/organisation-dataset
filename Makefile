.PHONY: init sync collect clobber black clean prune
.SECONDARY:
.DELETE_ON_ERROR:

SPARQL_DIR=sparql/

REGISTER_DIR=collection/register/
WIKIDATA_DIR=collection/wikidata/
OPENDATACOMMUNITIES_DIR=collection/opendatacommunities/

TARGETS=\
	collection/organisation.csv\
	collection/organisation-tag.csv

REGISTERS=\
	$(REGISTER_DIR)government-organisation.csv\
	$(REGISTER_DIR)local-authority-eng.csv\
	$(REGISTER_DIR)local-authority-type.csv\
	$(REGISTER_DIR)statistical-geography-county-eng.csv\
	$(REGISTER_DIR)statistical-geography-london-borough-eng.csv\
	$(REGISTER_DIR)statistical-geography-metropolitan-district-eng.csv\
	$(REGISTER_DIR)statistical-geography-non-metropolitan-district-eng.csv\
	$(REGISTER_DIR)statistical-geography-unitary-authority-eng.csv

SPARQL_DATA=\
	$(WIKIDATA_DIR)organisations.csv\
	$(OPENDATACOMMUNITIES_DIR)admingeo.csv\
	$(OPENDATACOMMUNITIES_DIR)localgov.csv

all: $(TARGETS)

collection/organisation.csv:	data/organisation.csv $(REGISTERS) $(SPARQL_DATA) bin/organisations.py
	mkdir -p collection
	python3 bin/organisations.py > $@

collection/organisation-tag.csv:	data/tag.csv
	cp data/tag.csv $@

$(REGISTER_DIR)%.csv:
	@mkdir -p $(REGISTER_DIR)
	curl -qs "https://$(notdir $(basename $@)).register.gov.uk/records.csv?page-index=1&page-size=5000" > $@

$(WIKIDATA_DIR)%.csv:	$(SPARQL_DIR)wikidata/%.rq bin/sparql.py
	@mkdir -p $(WIKIDATA_DIR)
	bin/sparql.py "https://query.wikidata.org/sparql" $< "http://www.wikidata.org/entity/" > $@

$(OPENDATACOMMUNITIES_DIR)%.csv:	$(SPARQL_DIR)opendatacommunities/%.rq bin/sparql.py
	@mkdir -p $(OPENDATACOMMUNITIES_DIR)
	bin/sparql.py "https://opendatacommunities.org/sparql" $< "" > $@

black:
	black .

init::
	pip3 install -r requirements.txt

clean::
	rm -rf ./collection

clobber::
	rm -f $(TARGETS)
