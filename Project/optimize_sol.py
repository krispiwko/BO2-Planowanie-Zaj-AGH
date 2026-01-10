#!/usr/bin/python
# -*- coding: utf-8 -*-
from copy import deepcopy
from random import randint, random, randrange

from imgui import DATA_TYPE_FLOAT
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

def change_plan(plan, unassigned_groups, marked_groups, data, change_max_time = True, change_window = True):

    #   Sytuacja: za dużo godzin w jednym dniu dla konkretnego studenta
    #   Jak naprawić? Przestawić na inny dzień, na którym ma mało zajęć
    #   Jakie mogą być skutki? -> Zajęcia mogą być przestawione na dzień, w którym wiele innych
    # studentów ma dużo zajęć, co sprawi że plan będzie gorszy
    # ALBO: Zajęcia będą przestawione i będą przeszkadzały mniejszej ilości studentów
    # O tym zdecyduje FUNKCJA OCENY!!! -> my robimy zmianę na chybił trafił
    # Ile zmian zrobić? -> najlepiej rozważyć każdy przedmiot, który został odnotowany
    # w marked_groups[MarkEnum.MAX_TIME]

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


    return plan, unassigned_groups
## KONIEC


    unmarked_group = []
    if change_max_time:
        for student in [x for x in data[DataEnum.STUDENT_DICT].keys() if marked_groups[MarkEnum.MAX_TIME][x] != [[], [], [], [], []]]:
            for day in range(5):
                for group in marked_groups[MarkEnum.MAX_TIME][student][day]:
                    if group in unmarked_group:
                        marked_groups[MarkEnum.MAX_TIME][student][day].remove(group)
            class_time_in_day = {day: 0 for day in range(5)}
            for group in [group for group in data[DataEnum.STUDENT_DICT][student] if not np.isnan(plan[group][0])]:
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
            for group in [group for group in data[DataEnum.LECTURER_DICT][lecturer] if not np.isnan(plan[group][0])]:
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
    if change_window:
        pass

    for unassigned_group in unassigned_groups:
        group_not_assigned = True
        curr_time = 0  # 8.00 rano
        day_of_week = 0  # Poniedziałek, 4 oznacza Piątek
        while group_not_assigned:
            group_not_assigned, remembered_room = try_to_insert_group(data, unassigned_group, plan, curr_time, day_of_week)
            if group_not_assigned:
                if_out_of_time, curr_time, day_of_week = modify_time_and_day(data, unassigned_group, curr_time, day_of_week)
                if if_out_of_time:
                    break
            else:
                plan[unassigned_group][0] = curr_time
                plan[unassigned_group][1] = day_of_week
                plan[unassigned_group][2] = remembered_room
                unassigned_groups.remove(unassigned_group)

    return plan, unassigned_groups

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
        self.best_unassigned_groups = None
        self.best_goal_sum = None

        self.cur_plan = None
        self.cur_unassigned_groups = None
        self.cur_goal_func = None
        
        self.goal_log = []


    def setup(self, plan, unassigned_groups, data):
        self.best_plan = plan
        self.best_unassigned_groups = unassigned_groups

        self.cur_plan = plan
        self.cur_unassigned_groups = unassigned_groups

        self.T = self.start_T
        self.data = data
        self.iter = 0
        self.cur_goal_sum, self.cur_marked_groups = goal_function(self.best_plan, self.cur_unassigned_groups, self.data)
        self.best_goal_sum = self.cur_goal_sum
        self.goal_log = []

    def step(self):
        new_plan, new_unassigned_groups = change_plan(dict(self.cur_plan), self.cur_unassigned_groups, self.cur_marked_groups, self.data)
        new_goal_sum, self.cur_marked_groups = goal_function(new_plan, new_unassigned_groups, self.data)
        delta = new_goal_sum - self.cur_goal_sum

        random_value = random()

        if new_goal_sum < self.best_goal_sum:
            self.best_plan = new_plan
            self.best_unassigned_groups = new_unassigned_groups
            self.best_goal_sum = new_goal_sum

            self.cur_plan = new_plan
            self.cur_unassigned_groups = new_unassigned_groups
            self.cur_goal_sum = new_goal_sum

        elif random_value < np.exp(-delta / self.T):
            self.cur_plan = new_plan
            self.cur_unassigned_groups = new_unassigned_groups
            self.cur_goal_sum = new_goal_sum

        self.T *= self.alpha
        self.iter += 1
        self.goal_log.append(self.cur_goal_sum)

        if self.iter >= self.max_iter:
            return False, self.cur_plan, self.cur_unassigned_groups
        return True, self.cur_plan, self.cur_unassigned_groups

    def run(self):
        should_continue = True
        while should_continue:
            should_continue, _6, _7 = self.step()

        return self.best_plan, self.best_unassigned_groups

    def get_result(self):
        return self.best_plan, self.best_unassigned_groups


opt_instance = OptimazeSol()


