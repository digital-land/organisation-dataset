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

local_authority_to_region_lookup = (
    "Local Authority District to Region (April 2019) Lookup in England",
    "https://opendata.arcgis.com/datasets/3ba3daf9278f47daba0f561889c3521a_0.geojson",
    "https://geoportal.statistics.gov.uk/datasets/local-authority-district-to-region-april-2019-lookup-in-england",
    [
        ('la-statistical-geography', 'LAD19CD', False),
        ('region-statistical-geography', 'RGN19CD', False)
    ],
    "data/lookup/statistical-geography-la-to-region-lookup.csv"
)


datasets = [
    region_data,
    local_resilience_forum_data,
    local_resilience_forum_local_authority_lookup,
    local_authority_to_combined_authority_lookup,
    local_authority_to_region_lookup
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


def remove_field(data, field):
    for d in data:
        if field in d.keys():
            del d[field]
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
            rename_field(mapped_dict, field[0], field[1])
        else:
            mapped_dict = joiner(mapped_dict, table, 'statistical-geography', [field])

        # remove temp field
        mapped_dict = remove_field(mapped_dict, 'statistical-geography')
        if not keep:
            # if not keeping also remove the original statistical geography field
            mapped_dict = remove_field(mapped_dict, statistical_geography_field)

    return mapped_dict


def map_to_identifiers(lookup, mappings, output, exclude_incomplete=True):
    # load lookup data
    lookup_data = get_csv_as_json(f'data/lookup/{lookup}.csv')

    data = map_statistical_geography_lookup(lookup_data, mappings)

    if exclude_incomplete:
        # only include lookup entry if all keys have a value
        successfully_mapped = []
        for r in data:
            if None not in r.values():
                successfully_mapped.append(r)
    else:
        successfully_mapped = data

    # write to file
    json_to_csv_file(f'data/lookup/{output}.csv', successfully_mapped)


if __name__ == "__main__":

    # collect LRF and Region data
    for dataset in datasets:
        (name, endpoint, doc_url, fields, save_path) = dataset
        filename = extract_name_from_document_url(doc_url)
        entries = collect_geojson(name, endpoint, filename, fields)
        json_to_csv_file(save_path, entries)


    # load organisation data
    organisations = get_csv_as_json(organisation_csv)


    # map statistical geography lookups to identifier lookups
    map_to_identifiers(
        "statistical-geography-la-to-lrf-lookup",
        [
            ('la-statistical-geography', 'organisation', organisations),
            ('lrf-statistical-geography', 'local-resilience-forum', get_csv_as_json("data/local-resilience-forum.csv"))
        ],
        "local-resilience-forum-to-local-authority"
    )

    map_to_identifiers(
        "statistical-geography-la-to-comb-lookup",
        [
            ('comb-statistical-geography', ('organisation', 'combined-authority'), organisations),
            ('la-statistical-geography', 'organisation', organisations)
        ],
        "local-authority-to-combined-authority"
    )

    map_to_identifiers(
        "statistical-geography-la-to-region-lookup",
        [
            ('la-statistical-geography', 'organisation', organisations),
            ('region-statistical-geography', 'region', get_csv_as_json("data/region.csv"))
        ],
        "local-authority-to-region"
    )
