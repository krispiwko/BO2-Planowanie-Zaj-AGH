#!/usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
from enums import *

def try_to_insert_group(data, group, plan, curr_time, day_of_week):
    # Sprawdzamy dla prowadzącego, czy może prowadzić wtedy zajęcia
    remembered_room = None
    groop_not_assigned = True
    lecturer_ok = True
    for lecturer_group in data[DataEnum.LECTURER_DICT][data[DataEnum.SUBJECT_DICT][group][2]]:
        if lecturer_group == group:
            continue
        if (plan[lecturer_group][1] == day_of_week and
                (curr_time - data[DataEnum.SUBJECT_DICT][lecturer_group][0]) <= plan[lecturer_group][0] <= (
                        curr_time + data[DataEnum.SUBJECT_DICT][group][0]) + 15):
            lecturer_ok = False
            break
    # Sprawdzamy dla studentów, czy nie mają wtedy kolizji
    if lecturer_ok:
        student_ok = True
        for student_group in data[DataEnum.OTHER_STUDENT_GROUPS][group]:
            if (plan[student_group][1] == day_of_week and
                    (curr_time - data[DataEnum.SUBJECT_DICT][student_group][0]) <= plan[student_group][0] <= (
                            curr_time + data[DataEnum.SUBJECT_DICT][group][0]) + 15):
                student_ok = False
                break
        # Sprawdzamy, czy dostępna jest jakakolwiek sala
        if student_ok:
            room_ok = False
            remembered_room = np.nan
            for room in data[DataEnum.SUBJECT_DICT][group][1]:
                current_room_ok = True
                for room_group in data[DataEnum.ROOM_GROUPS][room]:
                    if room_group == group:
                        continue
                    if (plan[room_group][1] == day_of_week and
                            (curr_time - data[DataEnum.SUBJECT_DICT][room_group][0]) <= plan[room_group][0] <= (
                                    curr_time + data[DataEnum.SUBJECT_DICT][group][0]) + 15):
                        current_room_ok = False
                        break
                if current_room_ok:
                    room_ok = True
                    remembered_room = room
                    break
            if room_ok:
                groop_not_assigned = False
    return groop_not_assigned, remembered_room

def modify_time_and_day(data, group, curr_time, day_of_week, change_day = True):
    if_out_of_time = False
    if_changed_day = False
    curr_time += data[DataEnum.SUBJECT_DICT][group][0] + 15
    if curr_time >= 720 - data[DataEnum.SUBJECT_DICT][group][0]:  # Oznacza że zajęcia skończyłyby się po 20:00
        curr_time = 0
        if change_day:
            day_of_week += 1
            if day_of_week > 4:  # Oznacza, że nie ma więcej dni w planie
                if_out_of_time = True
        else:
            if_out_of_time = True
    return if_out_of_time, curr_time, day_of_week

def init_sol(data):
    plan = {group: [np.nan, np.nan, np.nan] for group in data[DataEnum.SUBJECT_DICT].keys()}  # Przypisujemy: [godzina, dzień, sala]
    unassigned_groups = [] # Ławka rezerwowych
    for group in data[DataEnum.SUBJECT_DICT].keys():
        group_not_assigned = True
        curr_time = 0  # 8.00 rano
        day_of_week = 0  # Poniedziałek, 4 oznacza Piątek
        while group_not_assigned:
            if day_of_week > 4:
                unassigned_groups.append(group)
                break

            group_not_assigned, remembered_room = try_to_insert_group(data, group, plan, curr_time, day_of_week)
            if group_not_assigned:
                if_out_of_time, curr_time, day_of_week = modify_time_and_day(data, group, curr_time, day_of_week)
                if if_out_of_time:
                    unassigned_groups.append(group)
                    break
            else:
                plan[group][0] = curr_time
                plan[group][1] = day_of_week
                plan[group][2] = remembered_room
    return plan, unassigned_groups



