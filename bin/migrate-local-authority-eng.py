#!/usr/bin/env python3

import os
import csv

fieldnames = [
    "local-authority-eng",
    "local-authority-type",
    "name",
    "wikidata",
    "billing-authority",
    "esd-inventories",
    "statistical-geography",
    "start-date",
    "end-date",
]

writer = csv.DictWriter(open('local-authority-eng.csv', 'w'), fieldnames=fieldnames, extrasaction="ignore")
writer.writeheader()

for row in csv.DictReader(open("data/local-authority-eng.csv")):
    writer.writerow(row)
