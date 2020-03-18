"""
Spatial impact model

Written by Ed Oughton

March 2020

"""

import os
import configparser
import csv
import pandas as pd

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def get_lad_list(path):
    """

    """
    lad_lut = []

    files = os.listdir(path)

    for lad_file in files:

        lad = lad_file.split('_')[1]

        lad_lut.append(lad)

    return lad_lut


def process_data(lad, folder):
    """

    """
    output = []
    raw_data = []

    filename = 'ass_{}_MSOA11_2018.csv'.format(lad)
    path = os.path.join(folder, filename)

    with open(path, 'r') as capacity_lookup_file:
        reader = csv.DictReader(capacity_lookup_file)
        for item in reader:
            raw_data.append({
                'lad': lad,
                'age': item['DC1117EW_C_AGE'],
            })

    ages = set()

    for item in raw_data:
        ages.add(item['age'])

    for age in list(ages):
        number_of_age_group = 0
        for item in raw_data:
            if age == item['age']:
                number_of_age_group += 1

        output.append({
            'age': age,
            'population': number_of_age_group,
        })

    return output


def aggregate(data, parameters):
    """

    """
    output = []

    lut = []

    for age_group in parameters:

        lower = age_group[0]
        upper = age_group[1]

        group_tag = '{} to {}'.format(age_group[0], age_group[1])

        number = 0
        for item in data:
            if lower <= int(item['age']) <= upper:
                number += item['population']

        output.append({
            'age': group_tag,
            'population': number,
        })

    return output


def estimate_results(data, lad, parameters):
    """

    """
    output = []

    for age_group in parameters:

        lower = age_group[0]
        upper = age_group[1]
        group_tag = '{} to {}'.format(lower, upper)

        for item in data:
            if item['age'] == group_tag:

                hospitalisation = age_group[2]
                critical_care = age_group[3]
                fatality = age_group[4]

                hospitalisation = item['population'] * (hospitalisation/100)
                critical_care = hospitalisation * (critical_care/100)
                fatality = critical_care * (fatality/100)

                output.append({
                    'lad': lad,
                    'age': group_tag,
                    'population': item['population'],
                    'hospitalisation': hospitalisation,
                    'critical_care': critical_care,
                    'fatality': fatality,
                })

    return output


def aggregate_to_lads(results, lad):
    """

    """
    output = []

    population = 0
    hospitalisation = 0
    critical_care = 0
    fatality = 0

    for item in results:
        population += item['population']
        hospitalisation += item['hospitalisation']
        critical_care += item['critical_care']
        fatality += item['fatality']

    output.append({
        'lad': lad,
        'population': int(round(population)),
        'hospitalisation': int(round(hospitalisation)),
        'critical_care': int(round(critical_care)),
        'fatality': int(round(fatality)),
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

    results_folder = os.path.join(BASE_PATH, '..', 'results')
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    folder = os.path.join(BASE_PATH, 'msoa_2018')
    lad_list = get_lad_list(folder)

    lad_output = []

    for lad in lad_list:
        print('---')
        print('Working on {}'.format(lad))

        print('Processing data')
        data = process_data(lad, folder)

        print('Aggregating demographic bands')
        data = aggregate(data, parameters)
        # print(sum([p['population'] for p in data]))
        print('Estimating results')
        results = estimate_results(data, lad, parameters)

        results_to_write = pd.DataFrame(results)
        filename = '{}.csv'.format(lad)
        lad_folder = os.path.join(BASE_PATH, '..', 'results', 'lads')
        if not os.path.exists(lad_folder):
            os.makedirs(lad_folder)
        results_to_write.to_csv(os.path.join(lad_folder, filename), index=False)

        print('Aggregating to lads')
        lad_results = aggregate_to_lads(results, lad)

        lad_output = lad_output + lad_results

    print('Writing data')
    lads_to_write = pd.DataFrame(lad_output)
    filename = 'lad_results.csv'
    lads_to_write.to_csv(os.path.join(results_folder, filename), index=False)
