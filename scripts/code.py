"""
Spatial impact model

Written by Ed Oughton

March 2020

"""

import os
import configparser
import csv
import pandas as pd
# import geopandas as gpd
# import pyproj
# from shapely.geometry import MultiPolygon, mapping, shape, LineString
# from shapely.ops import transform, unary_union
# from fiona.crs import from_epsg
# import rasterio
# from rasterio.mask import mask
# from rasterstats import zonal_stats
# import networkx as nx
# from rtree import index
# import numpy as np
# from sklearn.linear_model import LinearRegression

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def process_data(path):
    """

    """
    output = []

    lad_lut = []

    files = os.listdir(path)[:2]

    for msoa_file in files:

        lad = msoa_file.split('_')[1]

        raw_data = []

        msoas = set()

        with open(os.path.join(path, msoa_file), 'r') as capacity_lookup_file:
            reader = csv.DictReader(capacity_lookup_file)
            for item in reader:
                msoas.add(item['Area'])
                raw_data.append({
                    'msoa': item['Area'],
                    'age': item['DC1117EW_C_AGE'],
                })

        for msoa_id in msoas:
            lad_lut.append({
                'lad': lad,
                'msoa': msoa_id,
            })

        for area in list(msoas):

            # if not area == 'E02002483':
            #     continue

            ages = set()

            for item in raw_data:
                if area == item['msoa']:
                    ages.add(item['age'])

            for age in list(ages):
                number_of_age_group = 0
                for item in raw_data:
                    if area == item['msoa']:
                        if age == item['age']:
                            number_of_age_group += 1

                output.append({
                    'msoa': area,
                    'age': age,
                    'number': number_of_age_group,
                })

    lad_lut = list({v['msoa']:v for v in lad_lut}.values())

    return output, msoas, lad_lut


def aggregate(data, msoas, parameters):
    """

    """
    output = {}

    for area in list(msoas):

        # if not area == 'E02002483':
        #     continue

        interim = {}

        for age_group in parameters:

            lower = age_group[0]
            upper = age_group[1]

            group_tag = '{} to {}'.format(age_group[0], age_group[1])

            number = 0
            for item in data:
                if area == item['msoa']:
                    if lower <= int(item['age']) <= upper:
                        number += item['number']

            interim[group_tag] = number

        output[area] = interim

    return output


def estimate_results(data, msoas, parameters):
    """

    """
    output = []

    for key, values in data.items():
        for k, v in values.items():
            for age_group in parameters:

                lower = age_group[0]
                upper = age_group[1]
                group_tag = '{} to {}'.format(age_group[0], age_group[1])

                if k == group_tag:

                    hospitalisation = age_group[2]
                    critical_care = age_group[3]
                    fatality = age_group[4]

                    output.append({
                        'msoa': key,
                        'age': k,
                        'population': v,
                        'hospitalisation': v * hospitalisation,
                        'critical_care': v * critical_care,
                        'fatality': v * fatality,
                    })

    return output


def aggregate_to_lads(msoa_results, lad_lut):
    """

    """
    output = []

    lads = set()

    for lad in lad_lut:
        lads.add(lad['lad'])

    for lad_id in lads:

        print('Working on {}'.format(lad_id))

        msoas = set()

        for msoa in lad_lut:
            if lad_id == msoa['lad']:
                msoas.add(msoa['msoa'])

        population = 0
        hospitalisation = 0
        critical_care = 0
        fatality = 0

        for item in msoa_results:
            if item['msoa'] in msoas:

                population += item['population']
                hospitalisation += item['hospitalisation']
                critical_care += item['critical_care']
                fatality += item['fatality']

        output.append({
            'lad': lad_id,
            'population': population,
            'hospitalisation': hospitalisation,
            'critical_care': critical_care,
            'fatality': fatality,
        })

    return output


if __name__ == '__main__':

    #lower age, upper age, hospitalisation, critical care, fatality
    parameters = [
        (0, 9, 0.1, 5, 0.002),
        (10, 19, 0.3, 5, 0.006),
        (20, 29, 1.2, 5, 0.03),
        (30, 39, 3.2, 5, 0.08),
        (40, 49, 4.9, 6.3, 0.15),
        (50, 59, 10.2, 12.2, 0.6),
        (60, 69, 16.6, 27.4, 2.2),
        (70, 79, 24.3, 43.2, 5.1),
        (80, 200, 27.3, 70.9, 9.3),
    ]
    path = os.path.join(BASE_PATH, 'msoa_2018')
    data, msoas, lad_lut = process_data(path)

    data = aggregate(data, msoas, parameters)

    msoa_results = estimate_results(data, msoas, parameters)

    # msoas_to_write = pd.DataFrame(msoa_results)
    # filename = 'msoa_results.csv'
    # folder = os.path.join(BASE_PATH, '..', 'results')
    # msoas_to_write.to_csv(os.path.join(folder, filename), index=False)

    # lad_results = aggregate_to_lads(msoa_results, lad_lut)

    # lads_to_write = pd.DataFrame(lad_results)
    # filename = 'lad_results.csv'
    # folder = os.path.join(BASE_PATH, '..', 'results')
    # lads_to_write.to_csv(os.path.join(folder, filename), index=False)
