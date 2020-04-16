#!/usr/bin/env python3

import os
import csv
import json
import requests
import pandas as pd


regions_ep = "https://opendata.arcgis.com/datasets/18b9e771acb84451a64d3bcdb3f3145c_0.geojson"
lrf_ep = "https://opendata.arcgis.com/datasets/d81478eef3904c388091e40f4b344714_0.geojson"
la_to_lrf_ep = "https://opendata.arcgis.com/datasets/203ea94d324b4fcda24875e83e577060_0.geojson"
organisation_csv = os.environ.get("organisation_csv", "https://raw.githubusercontent.com/digital-land/organisation-collection/master/collection/organisation.csv")


def name_to_identifier(n):
    return n.lower().replace(" ", "-").replace(",", "")


def get_csv_as_json(path_to_csv):
    csv_pd = pd.read_csv(path_to_csv, sep=",")
    return json.loads(csv_pd .to_json(orient='records'))


def fetch_json_from_endpoint(endpoint):
    json_url = requests.get(endpoint)
    return json_url.json()


# write json to csv file
def json_to_csv_file(output_file, data):
    print(f'Write data to {output_file}')
    # now we will open a file for writing 
    data_file = open(output_file, 'w')
    # create the csv writer object 
    csv_writer = csv.writer(data_file)
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


def map_region(region):
    props = region['properties']
    return {
        "region": name_to_identifier(props['RGN19NM']),
        "name": props['RGN19NM'],
        "statistical-geography": props['RGN19CD']
    }


def collect_regions():
    print(f"Collect region data from {regions_ep}")
    d = fetch_json_from_endpoint(regions_ep)
    regions = [map_region(r) for r in d['features']]
    return regions


def map_lrf(lrf):
    props = lrf['properties']
    return {
        "lrf": name_to_identifier(props['LRF19NM']),
        "name": props['LRF19NM'],
        "statistical-geography": props['LRF19CD']
    }


def collect_lrfs():
    print(f"Collect LRF data from {regions_ep}")
    d = fetch_json_from_endpoint(lrf_ep)
    lrfs = [map_lrf(r) for r in d['features'] if r['properties']['LRF19CD'].startswith('E48')]
    return lrfs
 

def fetch_statistical_geography_lookup():
    d = fetch_json_from_endpoint(la_to_lrf_ep)
    return [
        {'la-statistical-geography': r['properties']['LAD19CD'],
        'lrf-statistical-geography': r['properties']['LRF19CD'] }
        for r in d['features'] if r['properties']['LRF19CD'].startswith('E48')]


def collect_statistical_geography_lookup():
    print(f"Collect LRF data from {la_to_lrf_ep}")
    json_to_csv_file("data/lookup/statistical-geography-la-to-lrf-lookup.csv", fetch_statistical_geography_lookup())


# how to create the identifier lookup from the statistical geography lookup
# requires organisation data with associated statistical geographies
def generate_la_to_lrf_lookup():
    # get data from master organisation.csv
    org_pd = pd.read_csv(organisation_csv, sep=",")
    org_data = json.loads(org_pd.to_json(orient='records'))
    las = [x for x in org_data if x['organisation'].startswith('local-authority-eng:')]

    la_to_lrf = fetch_statistical_geography_lookup()
    # firstly join on la statistical geography
    for r in la_to_lrf:
        r['statistical-geography'] = r['la-statistical-geography']
    lookup = joiner(la_to_lrf, las, 'statistical-geography', ['organisation'])

    lrfs = get_csv_as_json("data/lrf.csv")
    # next join on lrf statistical geography
    for r in lookup:
        r['statistical-geography'] = r['lrf-statistical-geography']
    lookup = joiner(lookup, lrfs, 'statistical-geography', ['lrf'])

    # remove temporary 'statistical-geography' key
    for r in lookup:
        r.pop('statistical-geography')

    # write to file
    json_to_csv_file("data/lookup/la_to_lrf_lookup.tmp.csv", lookup)
    print("Temporary lookup file created: data/lookup/la_to_lrf_lookup.tmp.csv")


if __name__ == "__main__":
    # collect LRF and Region CSVs
    json_to_csv_file("data/region.csv", collect_regions())
    json_to_csv_file("data/lrf.csv", collect_lrfs())
    # collect LA to LRF lookup, statistical-geography
    collect_statistical_geography_lookup()

