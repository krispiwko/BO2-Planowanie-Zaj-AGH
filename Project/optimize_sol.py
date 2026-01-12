#!/usr/bin/python
# -*- coding: utf-8 -*-
from copy import deepcopy
from random import randint, random, randrange

from imgui import DATA_TYPE_FLOAT
from enums import *
import numpy as np
from init_sol import insert_group_without_collision, modify_time_and_day

coeffs_students = {
    "collision_cost": 20,
    "max_time_in_one_day": 360,
    "cost_per_minute_over_limit": 0.01,
    "min_window_length": 90,
    "window_cost": 2,
}
coeffs_lecturers = {
    "collision_cost": 20,
    "max_time_in_one_day": 360,
    "cost_per_minute_over_limit": 0.01,
    "min_window_length": 90,
    "window_cost": 2,
}


def get_max_concurrent(data, subjects):
    subject_data = data[DataEnum.SUBJECT_DICT]
    points = []
    for s in subjects:
        end = s[1] + subject_data[s[0]][0]
        points.append((s[1], +1))
        points.append((end, -1))

    points.sort(key=lambda x: (x[0], x[1]))

    current = 0
    max_overlap = 0

    for _, delta in points:
        current += delta
        max_overlap = max(max_overlap, current)

    return max_overlap

def goal_function(plan, data):

    marked_groups = {MarkEnum.MAX_TIME: {},
                     MarkEnum.WINDOW: {}}
    fun_sum = 0

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

def change_plan(plan, marked_groups, data, change_max_time = True, change_window = True):

## TESTY!!
    students = data[DataEnum.STUDENT_DICT].keys()
    students_data = data[DataEnum.STUDENT_DICT]
    subject_data = data[DataEnum.SUBJECT_DICT]
    problematic = []

    for i in range(5):
        for s in students:
            subjects = [(k,v[0]) for k,v in plan.items() if v[1] == i and k in students_data[s]]
            subjects.sort(key=lambda x: x[1])
            latest_end = 0
            for sub in subjects:
                start = sub[1]
                duration = subject_data[sub[0]][0]

                end = start + duration

                if start < latest_end:
                    if sub[0] not in problematic:
                        problematic.append(sub[0])

                if end > latest_end:
                    latest_end = end
                                    

    index = randrange(len(problematic))
    p = problematic[index]

    sala = plan[p][2]
    plan[p] = [randrange(0,720-90,15), randrange(0,5), sala]


    return plan
## KONIEC


class OptimazeSol(object):
    def __init__(self):
        self.T = 500
        self.start_T = 500
        self.data = None
        self.alpha = 0.99
        self.T_eps = 0.01
        self.max_iter = 100
        self.iter = 0
        self.best_plan = None
        self.best_goal_sum = None

        self.cur_plan = None
        self.cur_goal_func = None
        
        self.goal_log = []


    def setup(self, plan, data):
        self.best_plan = plan

        self.cur_plan = plan

        self.T = self.start_T
        self.data = data
        self.iter = 0
        self.cur_goal_sum, self.cur_marked_groups = goal_function(self.best_plan, self.data)
        self.best_goal_sum = self.cur_goal_sum
        self.goal_log = []

    def step(self):
        new_plan = change_plan(dict(self.cur_plan), self.cur_marked_groups, self.data)
        new_goal_sum, self.cur_marked_groups = goal_function(new_plan, self.data)
        delta = new_goal_sum - self.cur_goal_sum

        random_value = random()

        if new_goal_sum < self.best_goal_sum:
            self.best_plan = new_plan
            self.best_goal_sum = new_goal_sum

            self.cur_plan = new_plan
            self.cur_goal_sum = new_goal_sum

        elif random_value < np.exp(-delta / self.T):
            self.cur_plan = new_plan
            self.cur_goal_sum = new_goal_sum

        self.T *= self.alpha
        self.iter += 1
        self.goal_log.append(self.cur_goal_sum)

        if self.iter >= self.max_iter:
            return False, self.cur_plan
        return True, self.cur_plan

    def run(self):
        should_continue = True
        while should_continue:
            should_continue, _ = self.step()

        return self.best_plan

    def get_result(self):
        return self.best_plan


opt_instance = OptimazeSol()


