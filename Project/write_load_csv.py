#!/usr/bin/python
# -*- coding: utf-8 -*-
import csv
from copy import deepcopy

def write_plan_to_csv(inserted_plan):
    plan = deepcopy(inserted_plan)
    # CSV file name
    csv_filename = "plan.csv"

    # Converting nested values to a string
    for group in plan.keys():
        for i in range(3):
            plan[group][i] = str(plan[group][i])
        plan[group] = ', '.join(plan[group])

    # Writing single dictionary to CSV
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(plan.keys())  # Write header
        writer.writerow(plan.values())  # Write values

def load_plan_from_csv():
    csv_filename = "plan.csv"

    with open(csv_filename, 'r') as data:
        plan = {}
        for raw_plan in csv.DictReader(data):
            for group in list(raw_plan.keys()):
                raw_data = raw_plan[group]
                seperated_data = raw_data.split(', ')
                for i in range(0, 2):
                    seperated_data[i] = int(seperated_data[i])
                raw_plan[group] = seperated_data
            plan = raw_plan

    return plan
