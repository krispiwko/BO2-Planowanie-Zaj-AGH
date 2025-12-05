#!/usr/bin/python
# -*- coding: utf-8 -*-

def goal_function(plan, unassigned_groups, data):
    coeffs = {"unassigned_groups": 100}
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
        print(groups_on_day)
        marked_groups["max_time_in_one_day"] = []
        for day_of_week in range(0, 5):
            time_sum = 0
            for group in groups_on_day[day_of_week]:
                time_sum += data["subject_dict"][group][0]
            if time_sum > coeffs_students["max_time_in_one_day"]:
                fun_sum += coeffs_students["cost_per_minute_over_limit"] * (
                            time_sum - coeffs_students["cost_per_minute_over_limit"])
                marked_groups["max_time_in_one_day"] += groups_on_day[day_of_week]
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
                marked_groups += groups_on_day[day_of_week]
            chronological_groups = sorted(groups_on_day[day_of_week], key=lambda x: plan[x][0])
            for i in range(1, len(chronological_groups)):
                if plan[chronological_groups[i]][0] - plan[chronological_groups[i - 1]][0] > coeffs_lecturers[
                        "min_window_length"]:
                    fun_sum += coeffs_lecturers["window_cost"]
                    marked_groups += [chronological_groups[i - 1], chronological_groups[i]]
    return fun_sum


def optimize_sol(plan, unassigned_groups, data):
    pass
