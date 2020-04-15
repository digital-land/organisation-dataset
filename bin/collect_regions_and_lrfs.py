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


def fetch_json_from_endpoint(endpoint):
    json_url = requests.get(endpoint)
    return json_url.json()


# write json to csv file
def json_to_csv_file(output_file, data):
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


def generate_regions_csv():
    regions = collect_regions()
    regions_csv_path = "data/region.csv"
    print(f'Write region data to {regions_csv_path}')
    json_to_csv_file(regions_csv_path, regions)


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


def generate_lrf_csv():
    lrfs = collect_lrfs()
    lrfs_csv_path = "data/lrf.csv"
    print(f'Write LRF data to {lrfs_csv_path}')
    json_to_csv_file(lrfs_csv_path, lrfs)



if __name__ == "__main__":
    # create LRF and Region CSVs
    generate_regions_csv()
    generate_lrf_csv()

