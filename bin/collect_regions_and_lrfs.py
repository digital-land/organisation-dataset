#!/usr/bin/env python3

import os
import csv
import json
import requests
import pandas as pd

region_data = (
    "Regions (December 2019) Names and Codes in England",
    "https://opendata.arcgis.com/datasets/18b9e771acb84451a64d3bcdb3f3145c_0.geojson",
    "https://geoportal.statistics.gov.uk/datasets/regions-december-2019-names-and-codes-in-england",
    # fields we want to map
    [
        ("region", 'RGN19NM', True),
        ("name", 'RGN19NM', False),
        ("statistical-geography", 'RGN19CD', False)
    ],
    "data/region.csv"
)

local_resilience_forum_data = (
    "Local Resilience Forums (December 2019) Names and Codes in England and Wales",
    "https://opendata.arcgis.com/datasets/d81478eef3904c388091e40f4b344714_0.geojson",
    "https://geoportal.statistics.gov.uk/datasets/local-resilience-forums-december-2019-names-and-codes-in-england-and-wales",
    [
        ("local-resilience-forum", 'LRF19NM', True),
        ("name", 'LRF19NM', False),
        ("statistical-geography", 'LRF19CD', False)
    ],
    "data/local-resilience-forum.csv"
)

local_resilience_forum_local_authority_lookup = (
    "Local Authority District to Local Resilience Forum (December 2019) Lookup in England and Wales",
    "https://opendata.arcgis.com/datasets/203ea94d324b4fcda24875e83e577060_0.geojson",
    "https://geoportal.statistics.gov.uk/datasets/local-authority-district-to-local-resilience-forum-december-2019-lookup-in-england-and-wales",
    [
        ('la-statistical-geography', 'LAD19CD', False),
        ('lrf-statistical-geography', 'LRF19CD', False)
    ],
    "data/lookup/statistical-geography-la-to-lrf-lookup.csv"
)

local_authority_to_combined_authority_lookup = (
    "Local Authority District to Combined Authority (December 2019) Lookup in England",
    "https://opendata.arcgis.com/datasets/db4f8bae6bfa41babfafea3ec8a38c0e_0.geojson",
    "https://geoportal.statistics.gov.uk/datasets/local-authority-district-to-combined-authority-december-2019-lookup-in-england",
    [
        ('la-statistical-geography', 'LAD19CD', False),
        ('comb-statistical-geography', 'CAUTH19CD', False)
    ],
    "data/lookup/statistical-geography-la-to-comb-lookup.csv"
)


datasets = [
    region_data,
    local_resilience_forum_data,
    local_resilience_forum_local_authority_lookup,
    local_authority_to_combined_authority_lookup
]


organisation_csv = os.environ.get("organisation_csv", "https://raw.githubusercontent.com/digital-land/organisation-collection/master/collection/organisation.csv")


def name_to_identifier(n):
    return n.lower().replace(" ", "-").replace(",", "")


def get_csv_as_json(path_to_csv):
    csv_pd = pd.read_csv(path_to_csv, sep=",")
    return json.loads(csv_pd .to_json(orient='records'))


def fetch_json_from_endpoint(endpoint):
    json_url = requests.get(endpoint)
    # should this check response is OK?
    return json_url.json()


# write json to csv file
def json_to_csv_file(output_file, data):

    print(f'Write data to {output_file}')
    # now we will open a file for writing 
    data_file = open(output_file, 'w')
    # create the csv writer object 
    csv_writer = csv.writer(data_file, lineterminator='\n')
    # Counter variable used for writing  
    # headers to the CSV file
    count = 0


    for row in data: 
        if count == 0: 
    
            # Writing headers of CSV file 
            header = row.keys() 
            csv_writer.writerow(header) 
            count += 1
    
        # Writing data of CSV file 
        csv_writer.writerow(row.values()) 
    
    data_file.close()


def join_col(d1, idx_d2, k, col):
    for row in d1:
        if row[k] is not None:
            if idx_d2.get(row[k]) is not None:
                row[col] = idx_d2[row[k]][col]
            else:
                print(f"no match for '{k}'", row[k])
                row[col] = None
    return d1


def joiner(d1, d2, k, cols):
    if k in d1[0].keys() and k in d2[0].keys():
        # index d2 by key
        d2_idx = {x[k]: x for x in d2}

        for col in cols:
            if col in d2[0].keys():
                d1 = join_col(d1, d2_idx, k, col)
    return d1


def save_geojson(data, filename):
    with open(f'collection/{filename}.geojson', "w") as f:
        json.dump(data,f)


def extract_name_from_document_url(url):
    return url.split("/")[-1]


# pass list of tuples
# (desired field name, current field name, identifier(BOOL))
def map_fields(d, field_tuples):
    entry = {}
    for (field, current, k) in field_tuples:
        entry[field] = d.get(current)
        if k:
            entry[field] = name_to_identifier(d.get(current))
    return entry


def collect_geojson(name, endpoint, filename, fields):
    print(f"Collect: {name}\nfrom: {endpoint}")
    d = fetch_json_from_endpoint(endpoint)
    #save_geojson(d, extract_name_from_document_url(region_data[2]))
    save_geojson(d, filename)
    entries = [map_fields(r['properties'], fields) for r in d['features']]
    return entries


def rename_field(data, _from, to):
    for d in data:
        d[to] = d[_from]
        d.pop(_from)
    return data


def map_statistical_geography_lookup(statistical_geography_lookup, mappings, keep=False):
    mapped_dict = statistical_geography_lookup

    for mapping in mappings:

        # eg ('la-statistical-geography', 'organisation', las)
        (statistical_geography_field, field, table) = mapping

        for entry in mapped_dict:
            entry['statistical-geography'] = entry[statistical_geography_field]

        if type(field) == tuple:
            # handle cases where we want to rename newly added field
            mapped_dict = joiner(mapped_dict, table, 'statistical-geography', [field[0]])
            rename_field(mapped_dict, field[0], f'{field[0]}:{field[1]}')
        else:
            mapped_dict = joiner(mapped_dict, table, 'statistical-geography', [field])


        for entry in mapped_dict:
            # remove temp field
            entry.pop('statistical-geography')
            if not keep:
                # if not keeping also remove the original statistical geography field
                entry.pop(statistical_geography_field)

    return mapped_dict


# create the identifier lookup from the statistical geography lookup
# requires organisation data with associated statistical geographies
def map_la_to_lrf_lookup_data():
    # load lookup data
    lookup_data = get_csv_as_json("data/lookup/statistical-geography-la-to-lrf-lookup.csv")

    # load data to map on
    organisations = get_csv_as_json(organisation_csv)
    lrfs = get_csv_as_json("data/local-resilience-forum.csv")

    # list field mappings
    mappings = [
        ('la-statistical-geography', 'organisation', organisations),
        ('lrf-statistical-geography', 'local-resilience-forum', lrfs)
    ]

    data = map_statistical_geography_lookup(lookup_data, mappings)

    # only add lookup entry if organisation field set
    successfully_mapped = []
    for r in data:
        if r['organisation'] is not None:
            successfully_mapped.append(r)

    # write to file
    json_to_csv_file("data/lookup/local-resilience-forum-to-local-authority.csv", successfully_mapped)


def map_la_to_comb_lookup_data():
    # load lookup data
    lookup_data = get_csv_as_json("data/lookup/statistical-geography-la-to-comb-lookup.csv")

    # load data to map on
    organisations = get_csv_as_json(organisation_csv)

    # list field mappings
    mappings = [
        ('la-statistical-geography', ('organisation', 'local-authority'), organisations),
        ('comb-statistical-geography', ('organisation', 'combined-authority'), organisations)
    ]

    data = map_statistical_geography_lookup(lookup_data, mappings)

    # only add lookup entry if organisation field set
    successfully_mapped = []
    for r in data:
        if r['organisation:local-authority'] is not None and r['organisation:combined-authority']:
            successfully_mapped.append(r)

    # write to file
    json_to_csv_file("data/lookup/local-authority-to-combined-authority.csv", successfully_mapped)


if __name__ == "__main__":

    # collect LRF and Region data
    for dataset in datasets:
        (name, endpoint, doc_url, fields, save_path) = dataset
        filename = extract_name_from_document_url(doc_url)
        entries = collect_geojson(name, endpoint, filename, fields)
        json_to_csv_file(save_path, entries)

    # create local-authority code to local-resilience-forum id lookup
    map_la_to_lrf_lookup_data()
    map_la_to_comb_lookup_data()

