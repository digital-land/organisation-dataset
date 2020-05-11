#!/usr/bin/env python

import sys
from collections import OrderedDict
import csv
from zipfile import ZipFile
from docx.api import Document


name = {}


def load_names(prefix, path=None):
    if not path:
        path = "collection/register/" + prefix + ".csv"
    for row in csv.DictReader(open(path)):
        organisation = prefix + ":" + row[prefix]
        name[row["name"].lower()] = organisation
        if "official-name" in row:
            name[row["official-name"].lower()] = organisation


load_names("local-authority-eng")
load_names("local-authority-sct")
load_names("principal-local-authority")
load_names("government-organisation")

# load patched names
for row in csv.DictReader(open("patch/name.csv")):
    if row["name"] not in name:
        name[row["name"].lower()] = row["organisation"]

fields = OrderedDict(
    [
        ("addressbase-custodian", "Local Custodian Code"),
        ("name", "Authority"),
        ("region-name", "Region"),
        ("country-name", "Country"),
        ("organisation", "organisation"),
    ]
)

w = csv.DictWriter(sys.stdout, fields.keys(), extrasaction="ignore")
w.writeheader()

with ZipFile(sys.argv[1]) as z:
    z.extract("addressbase-products-local-custodian-codes.docx", "collection")
    document = Document("collection/addressbase-products-local-custodian-codes.docx")

    table = document.tables[0]

    keys = None
    for i, row in enumerate(table.rows):
        text = (cell.text for cell in row.cells)

        if i == 0:
            keys = tuple(text)
            continue

        o = dict(zip(keys, text))

        o["organisation"] = name.get(o["Authority"].lower(), "")

        w.writerow({k: o[ok] for (k, ok) in fields.items()})
