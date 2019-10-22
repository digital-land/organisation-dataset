#!/usr/bin/env python3

import sys
import csv
import requests

organisations = {}
fields = ["organisation", "name", "website", "statistical-geography", "start-date", "end-date"]


def load(key, fields, url=None, prefix=None):
    if prefix == None:
        prefix = key + ":"

    if url == None:
        url = "https://%s.register.gov.uk/records.csv?page-index=1&page-size=5000" % key

    if url.startswith("http"):
        f = requests.get(url).content.decode("utf-8").splitlines()
    else:
        f = open(url)

    for row in csv.DictReader(f):
        curie = "%s%s" % (prefix, row[key])
        organisations.setdefault(curie, {})
        for f in fields:
            if row[f]:
                organisations[curie][f] = row[f]


load("local-authority-eng", ["name", "official-name", "end-date"])
load("government-organisation", ["name", "website", "end-date"])
load("organisation", ["name", "website", "statistical-geography"], url="data/development-corporation.csv", prefix="")
load("organisation", ["website"], url="data/website.csv", prefix="")
load("organisation", ["statistical-geography"], url="data/statistical-geography.csv", prefix="")

w = csv.DictWriter(sys.stdout, fields, extrasaction='ignore')
w.writeheader()
for organisation in organisations:
    o = organisations[organisation]
    o["organisation"] = organisation
    o["name"] = o.get("official-name", o.get("name", ""))
    w.writerow(o)
