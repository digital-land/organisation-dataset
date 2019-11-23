#!/usr/bin/env python3

import sys
import csv
import requests
from SPARQLWrapper import SPARQLWrapper, JSON


organisations = {}

fields = [
    "organisation",
    "wikidata",
    "name",
    "website",
    "statistical-geography",
    "toid",
    "opendatacommunities",
    "esd-inventories",
    "start-date",
    "end-date",
]

def load(f, key, fields, prefix=None):
    if prefix is None:
        prefix = key + ":"
    for row in csv.DictReader(f):
        if row[key]:
            curie = prefix + row[key]
            organisations.setdefault(curie, {})
            for field in fields:
                to = (
                    "statistical-geography"
                    if field.startswith("statistical-geography")
                    else field
                )
                if row[field]:
                    organisations[curie][to] = row[field]


def load_register(key, fields, register=None):
    url = "https://%s.register.gov.uk/records.csv?page-index=1&page-size=5000" % (
        register or key
    )
    return load(requests.get(url).content.decode("utf-8").splitlines(), key, fields)


def load_file(path, key, fields, prefix=None):
    return load(open(path), key, fields, prefix)


def index(key):
    index = {}
    for o in organisations:
        if key in organisations[o]:
            index[organisations[o][key]] = o
    return index


def remove_prefix(value, prefix):
    if prefix and value.startswith(prefix):
        return value[len(prefix) :]
    return value


def patch(results, key, fields, prefix=None):
    keys = index(key)
    for d in results["results"]["bindings"]:
        row = {}
        for k in d:
            row[k] = remove_prefix(d[k]["value"], prefix)
            if k == "inception":
                row["start-date"] = row[k]
            elif k == "dissolved":
                row["end-date"] = row[k]
            elif k == "gss":
                row["statistical-geography"] = row[k]

        if key in row and row[key] in keys:
            organisation = keys[row[key]]
            for field in fields:
                if field in row:
                    organisations[organisation].setdefault(field, row[field])


def sparql(endpoint, query):
    s = SPARQLWrapper(
        endpoint,
        agent="Mozilla/5.0 (Windows NT 5.1; rv:36.0) Gecko/20100101 Firefox/36.0",
    )

    s.setQuery(query)
    s.setReturnFormat(JSON)
    return s.query().convert()


if True:
    load_register("local-authority-eng", ["name", "official-name", "end-date"])
    load_register("government-organisation", ["name", "website", "end-date"])

    # statistical geography codes
    load_register(
        "local-authority-eng",
        ["statistical-geography-county-eng"],
        register="statistical-geography-county-eng",
    )
    load_register(
        "local-authority-eng",
        ["statistical-geography-london-borough-eng"],
        register="statistical-geography-london-borough-eng",
    )
    load_register(
        "local-authority-eng",
        ["statistical-geography-metropolitan-district-eng"],
        register="statistical-geography-metropolitan-district-eng",
    )
    load_register(
        "local-authority-eng",
        ["statistical-geography-non-metropolitan-district-eng"],
        register="statistical-geography-non-metropolitan-district-eng",
    )
    load_register(
        "local-authority-eng",
        ["statistical-geography-unitary-authority-eng"],
        register="statistical-geography-unitary-authority-eng",
    )

# add curated organisations, which includes development corporations
load_file(
    "data/organisation.csv",
    "organisation",
    ["wikidata", "government-organisation", "website", "opendatacommunities", "esd-inventories", "statistical-geography"],
    prefix="",
    #add={"digital-land-organisation", True}
)

# add development corporations and national parks
corporations = sparql(
    "https://query.wikidata.org/sparql",
    """
    SELECT DISTINCT * WHERE {
      VALUES ?q { 
            wd:Q3336962 # National Park Authority
            wd:Q5266682 # Development Corporation
        }
      ?wikidata wdt:P31 ?q .
         OPTIONAL { ?wikidata wdt:P856 ?website }
         OPTIONAL { ?wikidata wdt:P3120 ?toid }
         OPTIONAL { ?wikidata wdt:P836 ?gss }
         OPTIONAL { ?wikidata wdt:P571 ?inception }
         OPTIONAL { ?wikidata wdt:P576 ?dissolved }
         ?wikidata rdfs:label ?name .
           FILTER (langMatches( lang(?name), "EN" ) )
    }
    """)

patch(corporations, key="wikidata", fields=["name", "website", "statistical-geography", "start-date", "end-date"], prefix="http://www.wikidata.org/entity/")

# match opencommunities.org
s = sparql(
    "https://opendatacommunities.org/sparql",
    """
    PREFIX admingeo: <http://opendatacommunities.org/def/ontology/admingeo/>
    PREFIX localgov: <http://opendatacommunities.org/def/local-government/>
    SELECT DISTINCT ?opendatacommunities ?name ?gss
    WHERE {
        VALUES ?o {
            admingeo:nationalPark
            admingeo:County
            admingeo:UnitaryAuthority
            admingeo:MetropolitanDistrict
            admingeo:NonMetropolitanDistrict
            admingeo:LondonBorough
            localgov:DevelopmentCorporation
        }
        ?opendatacommunities ?p ?o ;
            <http://publishmydata.com/def/ontology/foi/displayName> ?name ;
            <http://publishmydata.com/def/ontology/foi/code> ?gss
    }
    """)

patch(s, key="statistical-geography", fields=["name", "opendatacommunities"])

# add website, toids from wikidata
authorities = sparql(
    "https://query.wikidata.org/sparql",
    """
    SELECT DISTINCT * WHERE {
      VALUES ?q {
        wd:Q4321471 # county council 
        wd:Q5150900 # combined authority 
        wd:Q21561328 # English unitary authority council 
        wd:Q19414242 # English metropolitan district council 
        wd:Q21561306 # English non-metropolitan district council 
        wd:Q21561350 # London borough council 
        wd:Q16690653 # borough council 
        wd:Q180673 # ceremonial county of England
        wd:Q171809 # county of England
        wd:Q1138494 # historic county of England
        wd:Q769628 # metropolitan county
        wd:Q769603 # non-metropolitan county
        wd:Q1136601 # unitary authority of England
        wd:Q21272231 # county council area
        wd:Q211690 #  London borough
        wd:Q1002812 # metropolitan borough
        wd:Q1187580 # non-metropolitan district
        wd:Q1006876 # borough in the United Kingdom
      }
      ?wikidata wdt:P31 ?q .
         { ?wikidata wdt:P856 ?website }
         OPTIONAL { ?wikidata wdt:P3120 ?toid }
         OPTIONAL { ?wikidata wdt:P836 ?gss }
         ?wikidata rdfs:label ?name .
           FILTER (langMatches( lang(?name), "EN" ) )
    }
    """)
patch(authorities, key="statistical-geography", fields=["wikidata", "website", "toid"], prefix="http://www.wikidata.org/entity/")
patch(authorities, key="wikidata", fields=["website", "toid", "statistical-geography"], prefix="http://www.wikidata.org/entity/")

errors = 0

w = csv.DictWriter(sys.stdout, fields, extrasaction="ignore")
w.writeheader()
for organisation in sorted(organisations):
    o = organisations[organisation]
    o["organisation"] = organisation
    o["name"] = o.get("official-name", o.get("name", ""))

    # strip blank times from dates
    for k in o:
        if k.endswith("-date") and o[k].endswith("T00:00:00Z"):
            o[k] = o[k][:10]

    if not all(k in o and o[k] for k in ["name", 
#    "website", 
    #"statistical-geography"
]):
        print(o, file=sys.stderr)
        errors += 1
    w.writerow(o)

if errors:
    print(errors, "errors", file=sys.stderr)
    #sys.exit(2)
