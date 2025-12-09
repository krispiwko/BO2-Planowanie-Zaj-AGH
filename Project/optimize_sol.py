#!/usr/bin/python
# -*- coding: utf-8 -*-
from random import random
from enums import *
import numpy as np
from init_sol import try_to_insert_group, modify_time_and_day

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

def goal_function(plan, unassigned_groups, data):

    marked_groups = {MarkEnum.MAX_TIME: {},
                     MarkEnum.WINDOW: {}}
    fun_sum = 0
    fun_sum += coeffs["unassigned_groups"] * len(unassigned_groups)
    for student in data[DataEnum.STUDENT_DICT].keys():
        groups_on_day = {day_of_week: [group for group in data[DataEnum.STUDENT_DICT][student] if plan[group][1] == day_of_week] for day_of_week
                         in range(0, 5)}
        marked_groups[MarkEnum.MAX_TIME][student] = [[],[],[],[],[]]
        marked_groups[MarkEnum.WINDOW][student] = []
        for day_of_week in range(0, 5):
            time_sum = 0
            for group in groups_on_day[day_of_week]:
                time_sum += data[DataEnum.SUBJECT_DICT][group][0]
            if time_sum > coeffs_students["max_time_in_one_day"]:
                fun_sum += coeffs_students["cost_per_minute_over_limit"] * (
                            time_sum - coeffs_students["cost_per_minute_over_limit"])
                marked_groups[MarkEnum.MAX_TIME][student][day_of_week] = groups_on_day[day_of_week]
            chronological_groups = sorted(groups_on_day[day_of_week], key=lambda x: plan[x][0])
            marked_groups[MarkEnum.WINDOW][student] = []
            for i in range(1, len(chronological_groups)):
                if plan[chronological_groups[i]][0] - plan[chronological_groups[i - 1]][0] > coeffs_students[
                        "min_window_length"]:
                    fun_sum += coeffs_students["window_cost"]
                    marked_groups[MarkEnum.WINDOW][student] += [chronological_groups[i - 1], chronological_groups[i]]
    for lecturer in data[DataEnum.LECTURER_DICT].keys():
        groups_on_day = {day_of_week: [group for group in data[DataEnum.LECTURER_DICT][lecturer] if plan[group][1] == day_of_week] for day_of_week
                         in range(0, 5)}
        marked_groups[MarkEnum.MAX_TIME][lecturer] = [[], [], [], [], []]
        marked_groups[MarkEnum.WINDOW][lecturer] = []
        for day_of_week in range(0, 5):
            time_sum = 0
            for group in groups_on_day[day_of_week]:
                time_sum += data[DataEnum.SUBJECT_DICT][group][0]
            if time_sum > coeffs_lecturers["max_time_in_one_day"]:
                fun_sum += coeffs_lecturers["cost_per_minute_over_limit"] * (
                        time_sum - coeffs_lecturers["cost_per_minute_over_limit"])
                marked_groups[MarkEnum.MAX_TIME][lecturer][day_of_week]  = groups_on_day[day_of_week]
            chronological_groups = sorted(groups_on_day[day_of_week], key=lambda x: plan[x][0])
            for i in range(1, len(chronological_groups)):
                if plan[chronological_groups[i]][0] - plan[chronological_groups[i - 1]][0] > coeffs_lecturers[
                        "min_window_length"]:
                    fun_sum += coeffs_lecturers["window_cost"]
                    marked_groups[MarkEnum.WINDOW][lecturer] += [chronological_groups[i - 1], chronological_groups[i]]
    return fun_sum, marked_groups

def change_plan(plan, unassigned_groups, marked_groups, data):

    #   Sytuacja: za dużo godzin w jednym dniu dla konkretnego studenta
    #   Jak naprawić? Przestawić na inny dzień, na którym ma mało zajęć
    #   Jakie mogą być skutki? -> Zajęcia mogą być przestawione na dzień, w którym wiele innych
    # studentów ma dużo zajęć, co sprawi że plan będzie gorszy
    # ALBO: Zajęcia będą przestawione i będą przeszkadzały mniejszej ilości studentów
    # O tym zdecyduje FUNKCJA OCENY!!! -> my robimy zmianę na chybił trafił
    # Ile zmian zrobić? -> najlepiej rozważyć każdy przedmiot, który został odnotowany
    # w marked_groups[MarkEnum.MAX_TIME]
    unmarked_group = []
    for student in [x for x in data[DataEnum.STUDENT_DICT].keys() if marked_groups[MarkEnum.MAX_TIME][x] != [[], [], [], [], []]]:
        for day in range(5):
            for group in marked_groups[MarkEnum.MAX_TIME][student][day]:
                if group in unmarked_group:
                    marked_groups[MarkEnum.MAX_TIME][student][day].remove(group)
        class_time_in_day = {day: 0 for day in range(5)}
        for group in [group for group in data[DataEnum.STUDENT_DICT][student]]:
            day = plan[group][1]
            class_time_in_day[day] += data[DataEnum.SUBJECT_DICT][group][0]
        overloaded_days = [day for day in range(5) if class_time_in_day[day] > coeffs_students["max_time_in_one_day"]]
        free_days = [day for day in range(5) if class_time_in_day[day] + 90 < coeffs_students["max_time_in_one_day"]]
        while len(free_days) != 0 and len(overloaded_days) != 0:
            for day in overloaded_days:
                marked_groups[MarkEnum.MAX_TIME][student][day] = sorted(marked_groups[MarkEnum.MAX_TIME][student][day], key=lambda x: data[DataEnum.SUBJECT_DICT][x][0], reverse=True)
                while len(marked_groups[MarkEnum.MAX_TIME][student][day]) != 0:
                    group_to_move = marked_groups[MarkEnum.MAX_TIME][student][day].pop()
                    for free_day in free_days:
                        if_out_of_time = False
                        if class_time_in_day[free_day] + data[DataEnum.SUBJECT_DICT][group_to_move][0] > coeffs_students["max_time_in_one_day"]:
                            free_days.remove(free_day)
                            continue
                        else:
                            group_not_assigned = True
                            curr_time = 0
                            while group_not_assigned:
                                group_not_assigned, remembered_room = try_to_insert_group(data, group_to_move, plan, curr_time, free_day)
                                if group_not_assigned:
                                    if_out_of_time, curr_time, free_day = modify_time_and_day(data, group_to_move, curr_time, free_day, change_day = False)
                                    if if_out_of_time:
                                        break
                                else:
                                    plan[group_to_move][0] = curr_time
                                    plan[group_to_move][1] = free_day
                                    plan[group_to_move][2] = remembered_room
                                    unmarked_group.append(group_to_move)
                                    class_time_in_day[free_day] += data[DataEnum.SUBJECT_DICT][group_to_move][0]
                                    class_time_in_day[day] -= data[DataEnum.SUBJECT_DICT][group_to_move][0]
                        if if_out_of_time:
                            continue
                else:
                    if len(free_days) != 0:
                        overloaded_days.remove(day)
    for lecturer in [x for x in data[DataEnum.LECTURER_DICT].keys() if
                    marked_groups[MarkEnum.MAX_TIME][x] != [[], [], [], [], []]]:
        for day in range(5):
            for group in marked_groups[MarkEnum.MAX_TIME][lecturer][day]:
                if group in unmarked_group:
                    marked_groups[MarkEnum.MAX_TIME][lecturer][day].remove(group)
        class_time_in_day = {day: 0 for day in range(5)}
        for group in [group for group in data[DataEnum.LECTURER_DICT][lecturer]]:
            day = plan[group][1]
            class_time_in_day[day] += data[DataEnum.SUBJECT_DICT][group][0]
        overloaded_days = [day for day in range(5) if class_time_in_day[day] > coeffs_students["max_time_in_one_day"]]
        free_days = [day for day in range(5) if class_time_in_day[day] + 90 < coeffs_students["max_time_in_one_day"]]
        while len(free_days) != 0 and len(overloaded_days) != 0:
            for day in overloaded_days:
                marked_groups[MarkEnum.MAX_TIME][lecturer][day] = sorted(marked_groups[MarkEnum.MAX_TIME][lecturer][day],
                                                                        key=lambda x: data[DataEnum.SUBJECT_DICT][x][0],
                                                                        reverse=True)
                while len(marked_groups[MarkEnum.MAX_TIME][lecturer][day]) != 0:
                    group_to_move = marked_groups[MarkEnum.MAX_TIME][lecturer][day].pop()
                    for free_day in free_days:
                        if_out_of_time = False
                        if class_time_in_day[free_day] + data[DataEnum.SUBJECT_DICT][group_to_move][0] > \
                                coeffs_students["max_time_in_one_day"]:
                            free_days.remove(free_day)
                            continue
                        else:
                            group_not_assigned = True
                            curr_time = 0
                            while group_not_assigned:
                                group_not_assigned, remembered_room = try_to_insert_group(data, group_to_move, plan,
                                                                                          curr_time, free_day)
                                if group_not_assigned:
                                    if_out_of_time, curr_time, free_day = modify_time_and_day(data, group_to_move,
                                                                                              curr_time, free_day,
                                                                                              change_day=False)
                                    if if_out_of_time:
                                        break
                                else:
                                    plan[group_to_move][0] = curr_time
                                    plan[group_to_move][1] = free_day
                                    plan[group_to_move][2] = remembered_room
                                    unmarked_group.append(group_to_move)
                                    class_time_in_day[free_day] += data[DataEnum.SUBJECT_DICT][group_to_move][0]
                                    class_time_in_day[day] -= data[DataEnum.SUBJECT_DICT][group_to_move][0]
                        if if_out_of_time:
                            continue
                else:
                    if len(free_days) != 0:
                        overloaded_days.remove(day)
    return plan, unassigned_groups

def optimize_sol(plan, unassigned_groups, data):
    T = 500
    alpha = 0.999
    T_eps = 0.01
    max_iter = 1000
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




