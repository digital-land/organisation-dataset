#!/usr/bin/env python3

# run a SPARQL query, results as canonical CSV

import sys
from sys import argv
from SPARQLWrapper import SPARQLWrapper, JSON
import csv

names = {}


def sparql(endpoint, query):
    s = SPARQLWrapper(
        endpoint,
        agent="Mozilla/5.0 (Windows NT 5.1; rv:36.0) Gecko/20100101 Firefox/36.0",
    )

    s.setQuery(query)
    s.setReturnFormat(JSON)
    return s.query().convert()


def remove_prefix(value, prefix):
    if prefix and value.startswith(prefix):
        return value[len(prefix) :]
    return value


if __name__ == "__main__":
    data = sparql(argv[1], open(argv[2]).read())
    prefix = argv[3]

    fields = [field.replace("_", "-") for field in data["head"]["vars"]]

    w = csv.DictWriter(sys.stdout, fields, extrasaction="ignore")
    w.writeheader()

    for o in data["results"]["bindings"]:
        row = {}
        for field in fields:
            f = field.replace("-", "_")
            if f in o:
                value = o[f]["value"]
                row[field] = remove_prefix(value, prefix)

        w.writerow(row)
