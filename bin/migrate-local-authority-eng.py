#!/usr/bin/env python3

import os
import csv

fieldnames = [
    "local-authority-eng",
    # for matching and patching register data
    "wikidata",
    "statistical-geography",
    "esd-inventories",
    # data missing from the register
    "name",
    "local-authority-type",
    "start-date",
]

writer = csv.DictWriter(
    open("local-authority-eng.csv", "w"), fieldnames=fieldnames, extrasaction="ignore"
)
writer.writeheader()

for row in csv.DictReader(open("data/local-authority-eng.csv")):
    writer.writerow(row)
