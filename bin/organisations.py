#!/usr/bin/env python3

import os.path
import sys
import csv
import logging
import re
import validators
from datetime import datetime

register_dir = "collection/register/"

organisations = {}

fields = [
    "organisation",
    "wikidata",
    "name",
    "website",
    "twitter",
    "statistical-geography",
    "toid",
    "opendatacommunities",
    "opendatacommunities-area",
    "billing-authority",
    "census-area",
    "local-authority-type",
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
    errors = warnings = 0
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
        expected_fields = []

        # active organisations ..
        if not o.get("end-date", ""):
            mandatory_fields.append("website")

            # opendatacommunities doesn't yet have URIs for Combined Authorities ..

            if (
                organisation.startswith("local-authority-eng:")
                and organisations[organisation]["local-authority-type"] == "COMB"
            ):
                expected_fields.extend(
                    [
                        "statistical-geography",
                        "opendatacommunities",
                        "opendatacommunities-area",
                    ]
                )
            # unable to find URIs for development corporation areas ..
            elif organisation.startswith(
                "development-corporation:"
            ) or organisation in ["local-authority-eng:GLA"]:
                mandatory_fields.extend(
                    ["statistical-geography", "opendatacommunities"]
                )
                expected_fields.extend(["opendatacommunities-area"])
            elif organisation.startswith(
                "local-authority-eng:"
            ) or organisation.startswith("national-park:"):
                mandatory_fields.extend(
                    [
                        "statistical-geography",
                        "opendatacommunities",
                        "opendatacommunities-area",
                    ]
                )

        for expected_field in expected_fields:
            if not o.get(expected_field, ""):
                logging.warning("%s: missing %s field" % (organisation, expected_field))
                warnings += 1

        for mandatory_field in mandatory_fields:
            if not o.get(mandatory_field, ""):
                print(o, file=sys.stderr)
                logging.error("%s: missing %s field" % (organisation, mandatory_field))
                errors += 1

    return errors, warnings


def register_path(name):
    return os.path.join(register_dir, name + ".csv")


# add to organisations
def load_file(path, key=None, prefix=None, fields={}):

    logging.info("loading %s" % (path))

    # construct prefix for curie
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


def load_register(register=None, key=None, prefix=None, fields={}):
    key = key or register
    load_file(register_path(register), key=key, prefix=prefix, fields=fields)


def load_statistical_geography_register(name):
    register = "statistical-geography-" + name
    fields = {register: "statistical-geography"}
    load_register(register, key="local-authority-eng", fields=fields)


# index organisations by key
def index(key):
    keys = {}
    for organisation in organisations:
        if key in organisations[organisation]:
            keys.setdefault(organisations[organisation][key], [])
            keys[organisations[organisation][key]].append(organisation)
    return keys


# add to existing organisations
def patch_file(path, key):
    logging.info("patching %s with %s" % (path, key))
    keys = index(key)
    for row in csv.DictReader(open(path)):
        if key in row:
            for organisation in keys.get(row[key], []):
                for field in row:
                    if not organisations[organisation].get(field, None):
                        organisations[organisation][field] = row[field]


def patch_register(register=None, key=None):
    key = key or register
    patch_file(register_path(register), key=key)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s"
    )

    # load GOV.UK registers
    load_register("local-authority-eng")

    # add organisations missing from registers
    load_file("data/organisation.csv", key="organisation", prefix="")

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

    # patch files by various keys, needs two passes!
    for _pass in range(2):
        for path in sys.argv[1:]:
            for key in [
                "statistical-geography",
                "local-authority-eng",
                "wikidata",
                "billing-authority",
                "name",
            ]:
                patch_file(path, key=key)

    for organisation, o in organisations.items():
        # strip blank times from dates
        for k in o:
            if k.endswith("-date") and o[k].endswith("T00:00:00Z"):
                o[k] = o[k][:10]

    save(organisations)

    errors, warnings = validate(organisations)

    if warnings:
        logging.warning("%d warnings" % (warnings))

    if errors:
        logging.error("%d errors" % (errors))
        sys.exit(2)
