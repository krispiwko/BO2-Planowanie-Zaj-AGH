#!/usr/bin/python
# -*- coding: utf-8 -*-
from random import random
import numpy as np

def goal_function(plan, unassigned_groups, data):
    coeffs = {"unassigned_groups": 500}
    coeffs_students = {
            "max_time_in_one_day": 360,
            "cost_per_minute_over_limit": 0.01,
            "min_window_length": 90,
            "window_cost": 2,
            }
    coeffs_lecturers = {
            "max_time_in_one_day": 360,
            "cost_per_minute_over_limit": 0.01,
            "min_window_length": 90,
            "window_cost": 2,
            }
    marked_groups = {}
    fun_sum = 0
    fun_sum += coeffs["unassigned_groups"] * len(unassigned_groups)
    for student in data["student_dict"].keys():
        groups_on_day = {day_of_week: [group for group in plan.keys() if plan[group][1] == day_of_week] for day_of_week
                         in range(0, 5)}
        marked_groups["max_time_in_one_day"] = [[],[],[],[],[]]
        for day_of_week in range(0, 5):
            time_sum = 0
            for group in groups_on_day[day_of_week]:
                time_sum += data["subject_dict"][group][0]
            if time_sum > coeffs_students["max_time_in_one_day"]:
                fun_sum += coeffs_students["cost_per_minute_over_limit"] * (
                            time_sum - coeffs_students["cost_per_minute_over_limit"])
                marked_groups["max_time_in_one_day"][day_of_week] += [groups_on_day[day_of_week]]
            chronological_groups = sorted(groups_on_day[day_of_week], key=lambda x: plan[x][0])
            marked_groups["window"] = []
            for i in range(1, len(chronological_groups)):
                if plan[chronological_groups[i]][0] - plan[chronological_groups[i - 1]][0] > coeffs_students[
                        "min_window_length"]:
                    fun_sum += coeffs_students["window_cost"]
                    marked_groups["window"] += [chronological_groups[i - 1], chronological_groups[i]]
    for lecturer in data["lecturer_dict"].keys():
        groups_on_day = {day_of_week: [group for group in plan.keys() if plan[group][1] == day_of_week] for day_of_week
                         in range(0, 5)}
        for day_of_week in range(0, 5):
            time_sum = 0
            for group in groups_on_day[day_of_week]:
                time_sum += data["subject_dict"][group][0]
            if time_sum > coeffs_lecturers["max_time_in_one_day"]:
                fun_sum += coeffs_lecturers["cost_per_minute_over_limit"] * (
                        time_sum - coeffs_lecturers["cost_per_minute_over_limit"])
                marked_groups["max_time_in_one_day"][day_of_week]  += [groups_on_day[day_of_week]]
            chronological_groups = sorted(groups_on_day[day_of_week], key=lambda x: plan[x][0])
            for i in range(1, len(chronological_groups)):
                if plan[chronological_groups[i]][0] - plan[chronological_groups[i - 1]][0] > coeffs_lecturers[
                        "min_window_length"]:
                    fun_sum += coeffs_lecturers["window_cost"]
                    marked_groups["window"] += [chronological_groups[i - 1], chronological_groups[i]]
    return fun_sum, marked_groups

def change_plan(plan, unassigned_groups, marked_groups, data):
    new_plan = {}
    new_unassigned_groups = []
    overloaded_days = []
    for day_of_week in range(5):
        if len(marked_groups["max_time_in_one_day"][day_of_week]) != 0:
            overloaded_days.append(day_of_week)
    for day_of_week in overloaded_days:



    return new_plan, new_unassigned_groups

def optimize_sol(plan, unassigned_groups, data):
    T = 500
    alpha = 0.999
    T_eps = 0.01
    max_iter = 10000
    iter = 0
    goal_sum, marked_groups = goal_function(plan, unassigned_groups, data)
    best_plan = plan
    best_unassigned_groups = unassigned_groups
    best_goal_sum = goal_sum
    while iter < max_iter and T > T_eps:
        new_plan, new_unassigned_groups = change_plan(plan, unassigned_groups, marked_groups, data)
        new_goal_sum, marked_groups = goal_function(new_plan, new_unassigned_groups, data)
        delta = new_goal_sum - goal_sum
        if new_goal_sum < best_goal_sum:
            best_plan = new_plan
            best_unassigned_groups = new_unassigned_groups
            best_goal_sum = new_goal_sum
        if random() < np.exp(-delta / T):
            plan = new_plan
            unassigned_groups = new_unassigned_groups
            goal_sum = new_goal_sum
        T *= alpha
        iter += 1
    return best_plan, best_unassigned_groups, best_goal_sum




