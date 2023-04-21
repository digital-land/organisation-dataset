#!/usr/bin/env python3

import os.path
import sys
import csv
import logging
import re
import validators
from datetime import datetime

register_dir = "collection/register/"
data_dir = "data/"

organisations = {}

fields = [
    "organisation",
    "entity",
    "wikidata",
    "name",
    "website",
    "twitter",
    "statistical-geography",
    "boundary",
    "toid",
    "opendatacommunities",
    "opendatacommunities-area",
    "billing-authority",
    "census-area",
    "local-authority-type",
    "combined-authority",
    "esd-inventories",
    "local-resilience-forum",
    "region",
    "addressbase-custodian",
    "company",
    "wikipedia",
    "start-date",
    "end-date",
]


def save(organisations):
    w = csv.DictWriter(sys.stdout, fields, extrasaction="ignore")
    w.writeheader()
    for organisation in sorted(organisations):
        w.writerow(organisations[organisation])


def has_prefix(organisation, prefixes):
    return any([organisation.startswith(prefix + ":") for prefix in prefixes])


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


def valid_statistical_geography(organisation, value):
    prefix = (
        organisation.split(":")[0]
        + ":"
        + organisations[organisation].get("local-authority-type", "")
    )
    pattern = {
        "local-authority-eng:UA": r"^E06000\d\d\d",
        "local-authority-eng:NMD": r"^E07000\d\d\d",
        "local-authority-eng:MD": r"^E08000\d\d\d",
        "local-authority-eng:LBO": r"^E09000\d\d\d",
        "local-authority-eng:CC": r"^E09000\d\d\d",
        "local-authority-eng:CTY": r"^E10000\d\d\d",
        "local-authority-eng:SRA": r"^E12000\d\d\d",
        "local-authority-eng:COMB": r"^E47000\d\d\d",
        "national-park-authority:": r"^E260000\d\d",
        "development-corporation:": r"^E510000\d\d",
    }
    if value:
        if prefix not in pattern:
            logging.error(
                "%s: no pattern for statistical-geography %s (%s)"
                % (organisation, value, prefix)
            )
            return True

        if not re.match(pattern[prefix], value):
            logging.error(
                "%s: invalid statistical-geography %s (%s)"
                % (organisation, value, pattern[prefix])
            )
            return True

    return False


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

        # statistical geography
        if valid_statistical_geography(
            organisation, o.get("statistical-geography", "")
        ):
            errors += 1

        # mandatory fields ..
        mandatory_fields = set(["entity", "name", "wikidata"])
        expected_fields = set()
        unexpected_fields = set()

        # active organisations ..
        if not o.get("end-date", ""):
            mandatory_fields.add("website")

            # local government ..
            if organisation in [
                "transport-authority:Q682520",  # TfL
                "transport-authority:Q7834921",  # TfGM
            ]:
                expected_fields.update(["opendatacommunities", "billing-authority"])
            elif has_prefix(
                organisation,
                ["waste-authority", "transport-authority", "regional-park-authority"],
            ):
                mandatory_fields.update(["opendatacommunities", "billing-authority"])
                unexpected_fields.add("statistical-geography")
            elif has_prefix(
                organisation,
                [
                    "local-authority-eng",
                    "national-park-authority",
                    "development-corporation",
                ],
            ):
                local_fields = set(
                    [
                        "statistical-geography",
                        "opendatacommunities",
                        "opendatacommunities-area",
                    ]
                )
                mandatory_fields.update(local_fields)
                expected_fields.update(local_fields)
                expected_fields.update(["billing-authority"])

                if o.get("local-authority-type", "") not in ["", "COMB", "CTY", "SRA"]:
                    expected_fields.update(["addressbase-custodian"])

                # unable to find URIs for Combined Authorities ..
                if o.get("local-authority-type", "") == "COMB":
                    mandatory_fields.remove("opendatacommunities")
                    mandatory_fields.remove("opendatacommunities-area")

                # unable to find URIs for development corporation areas ..
                elif has_prefix(organisation, ["development-corporation"]):
                    mandatory_fields.remove("opendatacommunities-area")
                    expected_fields.remove("billing-authority")

                # unable to find an area for the GLA ..
                elif organisation in ["local-authority-eng:GLA"]:
                    mandatory_fields.remove("opendatacommunities-area")

                # find opendatacommunities doesn't yet have data for Northamptonshire UAs
                elif organisation in ["local-authority-eng:NNUA", "local-authority-eng:WNUA"]:
                    mandatory_fields.remove("opendatacommunities-area")
                    mandatory_fields.remove("opendatacommunities")

        for field in expected_fields:
            if field not in set(mandatory_fields).union(unexpected_fields):
                if not o.get(field, ""):
                    logging.warning("%s: missing %s field" % (organisation, field))
                    warnings += 1

        for field in unexpected_fields:
            if o.get(field, ""):
                logging.info(o)
                logging.error("%s: unexpected field %s" % (organisation, field))
                errors += 1

        for field in mandatory_fields:
            if field not in unexpected_fields:
                if not o.get(field, ""):
                    logging.info(o)
                    logging.error("%s: missing %s field" % (organisation, field))
                    errors += 1

    return errors, warnings


def csv_path(directory, name):
    return os.path.join(directory, name + ".csv")


# add to organisations
def load_file(path, key=None, prefix=None, fields=None, ignore_ended=False):

    logging.info("loading %s" % (path))

    # construct prefix for curie
    if prefix is None:
        prefix = key + ":"

    for row in csv.DictReader(open(path)):
        if row[key]:
            curie = prefix + row[key]
            organisations.setdefault(curie, {})

            for field in row:
                if field is None:
                    logging.error("%s: %s has extra columns" % (path, curie))
                if (not fields) or (field in fields):
                    to = fields[field] if fields else field
                    if row[field]:
                        # stop statistical-geography entries with end-date 
                        # overriding latest
                        if ignore_ended and row.get('end-date') is not None:
                            pass
                        else:
                            organisations[curie][to] = row[field]


def load_register(register, key=None, fields={}, ignore_ended=False):
    key = key or register
    load_file(csv_path(register_dir, register), key=key, fields=fields, ignore_ended=ignore_ended)


def load_statistical_geography_register(name):
    register = "statistical-geography-" + name
    fields = {register: "statistical-geography"}
    load_register(register, key="local-authority-eng", fields=fields, ignore_ended=True)


def load_data(register, key=None):
    key = key or register
    load_file(csv_path(data_dir, register), key=key)


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
                    if row[field] and not organisations[organisation].get(field, None):
                        organisations[organisation][field] = row[field]
                        logging.debug([path, key, organisation, field, row[field]])


def patch_register(register, key=None):
    key = key or register
    patch_file(csv_path(register_dir, register), key=key)


def patch_wikidata(name, key):
    patch_file(csv_path("collection/wikidata", name), key)


def patch_odc(name, key):
    patch_file(csv_path("collection/opendatacommunities", name), key)


def patch_lookup(name, key):
    patch_file(csv_path("data/lookup", name), key)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s"
    )

    # load GOV.UK registers
    load_register("local-authority-eng")

    # add organisations and data missing from registers
    load_data("government-organisation")
    load_data("development-corporation")
    load_data("local-authority-eng")
    load_data("national-park-authority")
    load_data("regional-park-authority")
    load_data("transport-authority")
    load_data("waste-authority")
    load_data("public-authority")
    load_data("nonprofit")

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

    # patch wikidata
    patch_wikidata("legislature", "wikidata")
    patch_wikidata("legislature", "name")
    patch_wikidata("authority", "wikidata")

    patch_odc("localgov", "local-authority-eng")
    patch_odc("localgov", "billing-authority")
    patch_odc("localgov", "name")

    patch_odc("national-park-authority", "billing-authority")
    patch_odc("national-park-authority", "name")

    patch_odc("development-corporation", "name")

    patch_odc("admingeo", "opendatacommunities")
    patch_odc("admingeo", "statistical-geography")

    patch_lookup("local-authority-to-region", "organisation")
    patch_lookup("local-resilience-forum-to-local-authority", "organisation")
    patch_lookup("local-authority-statistical-geography-boundary", "statistical-geography")
    patch_lookup("local-authority-to-combined-authority", 'organisation')

    patch_file("collection/addressbase-custodian.csv", "organisation")
    patch_file("data/entity.csv", "organisation")
    patch_file("data/government-organisation.csv", "organisation")

    for organisation, o in organisations.items():
        # strip blank times from dates
        for k in o:
            if k.endswith("-date") or o[k].endswith("T00:00:00Z"):
                o[k] = o[k][:10]

    save(organisations)

    errors, warnings = validate(organisations)

    if warnings:
        logging.warning("%d warnings" % (warnings))

    if errors:
        logging.error("%d errors" % (errors))
        sys.exit(2)
