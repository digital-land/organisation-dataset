#!/usr/bin/env python3

import sys
import csv
import logging
import re
import validators
from datetime import datetime

register_dir = "collection/register/"
wikidata_dir = "collection/wikidata/"
opendatacommunties_dir = "collection/opendatacommunties/"

organisations = {}

fields = [
    "organisation",
    "wikidata",
    "name",
    "website",
    "statistical-geography",
    "toid",
    "opendatacommunities",
    "opendatacommunities-area",
    "esd-inventories",
    "start-date",
    "end-date",
]


def save(organisations):
    w = csv.DictWriter(sys.stdout, fields, extrasaction="ignore")
    w.writeheader()
    for organisation in sorted(organisations):
        w.writerow(organisations[organisation])


def valid_url(n, url):
    if url != "" and not validators.url(url):
        logging.error("%s: invalid url %s" % (n, url))
        return True
    return False


def valid_date(n, date):
    if date == None or date == "":
        return False

    if re.match(r"^\d\d\d\d$", date):
        date = date + "-01"

    if re.match(r"^\d\d\d\d-\d\d$", date):
        date = date + "-01"

    try:
        if date == datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d"):
            return False
    except ValueError:
        logging.error("%s: invalid date %s" % (n, date))

    return True


def validate(organisations):
    errors = 0
    for organisation in sorted(organisations):
        o = organisations[organisation]

        # some validation ..
        for url_field in ["opendatacommunities", "opendatacommunities-area", "website"]:
            if valid_url(organisation, o.get(url_field, "")):
                errors += 1

        for date_field in ["start-date", "end-date"]:
            if valid_date(organisation, o.get(date_field, "")):
                errors += 1

        # mandatory fields ..
        mandatory_fields = ["name", "wikidata"]

        if not o.get("end-date", ""):
            mandatory_fields.append("website")

            # LPA additional constraints ..
            if (
                organisation.startswith("local-authority-eng")
                or organisation.startswith("national-park")
                or organisation.startswith("development-corporation")
            ):
                mandatory_fields.extend(
                    [
                        "statistical-geography",
                        "opendatacommunities",
                        "opendatacommunities-area"
                    ]
                )

        for mandatory_field in mandatory_fields:
            if not o.get(mandatory_field, ""):
                logging.error("%s: missing %s field" % (organisation, mandatory_field))
                errors += 1

    return errors


def register_path(name):
    return register_dir + name + ".csv"


def load_register(register=None, key=None, prefix=None, path=None, fields={}):
    if path is None:
        path = register_path(register)

    if key is None:
        key = register

    if prefix is None:
        prefix = key + ":"

    for row in csv.DictReader(open(path)):
        if row[key]:
            curie = prefix + row[key]
            organisations.setdefault(curie, {})

            for field in row:
                to = fields.get(field, field)
                if row[field]:
                    organisations[curie][to] = row[field]


def load_statistical_geography_register(name):
    register = "statistical-geography-" + name
    fields = { register: "statistical-geography" }
    load_register(register, fields=fields, key="local-authority-eng")


# index organisations by key
def index(key):
    keys = {}
    for organisation in organisations:
        if key in organisations[organisation]:
            keys.setdefault(organisations[organisation][key], [])
            keys[organisations[organisation][key]].append(organisation)
    return keys


def patch(path, key):
    keys = index(key)
    for row in csv.DictReader(open(path)):
        for organisation in keys.get(row[key], []):
            for field in row:
                if not organisations[organisation].get(field, None):
                    organisations[organisation][field] = row[field]


def patch_register(register=None, key=None):
    key = key or register
    patch(register_path(register), key)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # load GOV.UK registers
    load_register("local-authority-eng")

    # add organisations missing from registers
    load_register(path="data/organisation.csv", key="organisation", prefix="")

    # add details for government organisations
    patch_register("government-organisation")

    # statistical geography codes
    load_statistical_geography_register("county-eng")
    load_statistical_geography_register("london-borough-eng")
    load_statistical_geography_register("metropolitan-district-eng")
    load_statistical_geography_register("non-metropolitan-district-eng")
    load_statistical_geography_register("unitary-authority-eng")

    # assert name from offical-name
    for organisation, o in organisations.items():
        o["organisation"] = organisation
        o["name"] = o.get("official-name", o.get("name", ""))

    patch("collection/wikidata/organisations.csv", key="name")
    patch("collection/wikidata/organisations.csv", key="wikidata")

    patch("collection/opendatacommunities/admingeo.csv", key="statistical-geography")
    patch("collection/opendatacommunities/localgov.csv", key="statistical-geography")

    for organisation, o in organisations.items():
        # strip blank times from dates
        for k in o:
            if k.endswith("-date") and o[k].endswith("T00:00:00Z"):
                o[k] = o[k][:10]

    save(organisations)

    errors = validate(organisations)

    if errors:
        logging.error("%d errors" % (errors))
        # live with errors .. for now ..
        #sys.exit(2)
