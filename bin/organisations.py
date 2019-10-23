#!/usr/bin/env python3

import sys
import csv
import requests

organisations = {}
fields = [
    "organisation",
    "name",
    "website",
    "statistical-geography",
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

w = csv.DictWriter(sys.stdout, fields, extrasaction="ignore")
w.writeheader()
for organisation in sorted(organisations):
    o = organisations[organisation]
    o["organisation"] = organisation
    o["name"] = o.get("official-name", o.get("name", ""))
    w.writerow(o)
