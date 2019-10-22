#!/usr/bin/env python3

import sys
import csv
import requests

organisations = {}
fields = ["organisation", "name", "website", "statistical-geography", "start-date", "end-date"]


def load(key, fields, url=None, prefix=None, register=None):
    if prefix == None:
        prefix = key + ":"

    if url == None:
        url = "https://%s.register.gov.uk/records.csv?page-index=1&page-size=5000" % (register or key)

    if url.startswith("http"):
        f = requests.get(url).content.decode("utf-8").splitlines()
    else:
        f = open(url)

    for row in csv.DictReader(f):
        if row[key]:
            curie = "%s%s" % (prefix, row[key])
            organisations.setdefault(curie, {})
            for f in fields:
                t = "statistical-geography" if f.startswith("statistical-geography") else f
                if row[f]:
                    organisations[curie][t] = row[f]


load("local-authority-eng", ["name", "official-name", "end-date"])
load("government-organisation", ["name", "website", "end-date"])

load("local-authority-eng", ["statistical-geography-county-eng"], register="statistical-geography-county-eng")
load("local-authority-eng", ["statistical-geography-london-borough-eng"], register="statistical-geography-london-borough-eng")
load("local-authority-eng", ["statistical-geography-metropolitan-district-eng"], register="statistical-geography-metropolitan-district-eng")
load("local-authority-eng", ["statistical-geography-non-metropolitan-district-eng"], register="statistical-geography-non-metropolitan-district-eng")
load("local-authority-eng", ["statistical-geography-unitary-authority-eng"], register="statistical-geography-unitary-authority-eng")

# assert fixes
load("organisation", ["name", "website", "statistical-geography"], url="data/organisations.csv", prefix="")

w = csv.DictWriter(sys.stdout, fields, extrasaction='ignore')
w.writeheader()
for organisation in sorted(organisations):
    o = organisations[organisation]
    o["organisation"] = organisation
    o["name"] = o.get("official-name", o.get("name", ""))
    w.writerow(o)
