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

COLLECTED_REGISTERS:=\
	$(REGISTER_DIR)government-organisation.csv\
	$(REGISTER_DIR)local-authority-eng.csv\
	$(REGISTER_DIR)local-authority-sct.csv\
	$(REGISTER_DIR)principal-local-authority.csv\
	$(REGISTER_DIR)local-authority-type.csv\
	$(REGISTER_DIR)government-domain.csv\
	$(REGISTER_DIR)statistical-geography-county-eng.csv\
	$(REGISTER_DIR)statistical-geography-london-borough-eng.csv\
	$(REGISTER_DIR)statistical-geography-metropolitan-district-eng.csv\
	$(REGISTER_DIR)statistical-geography-non-metropolitan-district-eng.csv\
	$(REGISTER_DIR)statistical-geography-unitary-authority-eng.csv

COLLECTED_DATA:=\
	$(COLLECTION_DIR)addressbase-custodian.csv\
	$(WIKIDATA_DIR)legislature.csv\
	$(WIKIDATA_DIR)authority.csv\
	$(OPENDATACOMMUNITIES_DIR)admingeo.csv\
	$(OPENDATACOMMUNITIES_DIR)localgov.csv\
	$(OPENDATACOMMUNITIES_DIR)billing-authority.csv\
	$(OPENDATACOMMUNITIES_DIR)governed-by.csv\
	$(OPENDATACOMMUNITIES_DIR)development-corporation.csv\
	$(OPENDATACOMMUNITIES_DIR)national-park-authority.csv

PATCH_FILES:=\
	$(DATA_DIR)development-corporation.csv\
	$(DATA_DIR)government-organisation.csv\
	$(DATA_DIR)local-authority-eng.csv\
	$(PATCH_DIR)name.csv\
	$(DATA_DIR)national-park-authority.csv\
	$(DATA_DIR)public-authority.csv\
	$(DATA_DIR)waste-authority.csv

SOURCE_DATA:=\
	$(COLLECTED_REGISTERS)\
	$(COLLECTED_DATA)\
	$(PATCH_FILES)

all: $(TARGETS)

collection/organisation.csv:	$(SOURCE_DATA) bin/organisations.py
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
	bin/sparql.py "https://opendatacommunities.org/sparql" $< > $@

collection/addressbase-custodian.csv: bin/addressbase-custodian.py collection/addressbase-products-local-custodian-codes.zip $(COLLECTED_REGISTERS) patch/name.csv
	mkdir -p collection
	python3 bin/addressbase-custodian.py collection/addressbase-products-local-custodian-codes.zip > $@

collection/addressbase-products-local-custodian-codes.zip:
	curl -qsL 'https://www.ordnancesurvey.co.uk/documents/product-support/support/addressbase-products-local-custodian-codes.zip' > collection/addressbase-products-local-custodian-codes.zip

lookup/local-authority-statistical-geography-boundary.csv:
	curl -qsL -H 'Accept: application/vnd.github.v3.raw' 'https://github.com/digital-land/boundary-collection/raw/master/index/local-authority-boundary.csv' > data/lookup/local-authority-statistical-geography-boundary.csv

black:
	black .

init::
	pip3 install -r requirements.txt

clean::
	rm -rf ./collection

clobber::
	rm -f $(TARGETS)

regions::
	python3 bin/collect_regions_and_lrfs.py
