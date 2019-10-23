#!/usr/bin/env python3

import sys
import csv
import requests
from SPARQLWrapper import SPARQLWrapper, CSV


organisations = {}
gss = {}

fields = [
    "organisation",
    "name",
    "website",
    "statistical-geography",
    "opendatacommunities",
    "data-govuk",
    "start-date",
    "end-date",
]


def load(f, key, fields, prefix=""):
    for row in csv.DictReader(f):
        if row[key]:
            curie = prefix + row[key]
            organisations.setdefault(curie, {})
            for f in fields:
                t = (
                    "statistical-geography"
                    if f.startswith("statistical-geography")
                    else f
                )
                if row[f]:
                    organisations[curie][t] = row[f]


def load_register(key, fields, register=None):
    url = "https://%s.register.gov.uk/records.csv?page-index=1&page-size=5000" % (
        register or key
    )
    return load(
        requests.get(url).content.decode("utf-8").splitlines(),
        key,
        fields,
        prefix=key + ":",
    )


def load_file(path, key, fields):
    return load(open(path), key, fields)


def index_gss():
    for o in organisations:
        if "statistical-geography" in organisations[o]:
            gss[organisations[o]["statistical-geography"]] = o


def load_opendatacommunities():
    sparql = SPARQLWrapper("https://opendatacommunities.org/sparql")
    sparql.setQuery(
        """
    SELECT ?uri ?name ?gss
    WHERE {
      VALUES ?o { 
        <http://opendatacommunities.org/def/ontology/admingeo/nationalPark>
        <http://opendatacommunities.org/def/ontology/admingeo/County>
        <http://opendatacommunities.org/def/ontology/admingeo/UnitaryAuthority>
        <http://opendatacommunities.org/def/ontology/admingeo/MetropolitanDistrict>
        <http://opendatacommunities.org/def/ontology/admingeo/NonMetropolitanDistrict>
        <http://opendatacommunities.org/def/ontology/admingeo/LondonBorough>
        <http://opendatacommunities.org/def/local-government/DevelopmentCorporation>
      }

        ?uri ?p ?o ;
            <http://www.w3.org/2000/01/rdf-schema#label> ?name ;
            <http://publishmydata.com/def/ontology/foi/code> ?gss
      }
    """
    )
    sparql.setReturnFormat(CSV)
    results = sparql.query().convert()
    for row in csv.DictReader(results.decode("utf-8").splitlines()):
        if row["gss"] in gss:
            organisations[gss[row["gss"]]]["opendatacommunities"] = row["uri"]


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

# assert fixes
load_file(
    "data/organisation.csv",
    "organisation",
    ["name", "website", "statistical-geography"],
)

index_gss()
load_opendatacommunities()


w = csv.DictWriter(sys.stdout, fields, extrasaction="ignore")
w.writeheader()
for organisation in sorted(organisations):
    o = organisations[organisation]
    o["organisation"] = organisation
    o["name"] = o.get("official-name", o.get("name", ""))
    w.writerow(o)
