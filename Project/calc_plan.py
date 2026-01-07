#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading
from read_data import *
from init_sol import *
from write_load_csv import *
from optimize_sol import *

def invalidate_data():
    global data
    data = None

data = None
def get_data():
    global data

    if data != None:
        return data

    data = create_data()
    return data

def prepare_plan():
    global data
    get_data()

    starting_plan, unassigned_groups = init_sol(data)

    # write_plan_to_csv(starting_plan)

    # loaded_plan = load_plan_from_csv()

    loaded_plan = starting_plan

    identical = True
    for group in starting_plan.keys():
        if starting_plan[group] != loaded_plan[group]:
            identical = False
    goal_fun_sum, marked_groups = goal_function(starting_plan, unassigned_groups, data)

    return starting_plan, unassigned_groups

