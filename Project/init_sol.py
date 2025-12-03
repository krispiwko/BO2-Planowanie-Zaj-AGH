#!/usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np


def init_sol(student_dict, subject_dict, lecturer_dict):

    group_list = []
    for lecturer_groups in list(lecturer_dict.values()):
        group_list += lecturer_groups
    #print(group_list)
    other_student_groups_in_group = {group: set() for group in group_list}
    for student in list(student_dict.keys()):
        for student_group in student_dict[student]:
            for other_student_group in student_dict[student]:
                if other_student_group == student_group:
                    continue
                other_student_groups_in_group[student_group].add(other_student_group)
    #print(other_student_groups_in_group)
    rooms_set = set()
    for group in group_list:
        for room in subject_dict[group][1]:
            rooms_set.add(room)
    groups_that_use_room = {room: set() for room in rooms_set}
    for room in rooms_set:
        for group in group_list:
            if room in subject_dict[group][1]:
                groups_that_use_room[room].add(group)
    #print(groups_that_use_room)
    plan = {group: [np.nan, np.nan, np.nan] for group in group_list}  # Przypisujemy: [godzina, dzień, sala]
    unassigned_groups = [] # Ławka rezerwowych
    for group in group_list:
        curr_time = 0  # 8.00 rano
        day_of_week = 0  # Poniedziałek, 4 oznacza Piątek
        group_not_assigned = True
        while group_not_assigned:
            # Sprawdzamy dla prowadzącego, czy może prowadzić wtedy zajęcia
            lecturer_ok = True
            for lecturer_group in lecturer_dict[subject_dict[group][2]]:
                if lecturer_group == group:
                    continue
                if (plan[lecturer_group][1] == day_of_week and
                        (curr_time - subject_dict[lecturer_group][0]) <= plan[lecturer_group][0] <= (curr_time + subject_dict[group][0]) + 15):
                    lecturer_ok = False
                    break
            # Sprawdzamy dla studentów, czy nie mają wtedy kolizji
            if lecturer_ok:
                student_ok = True
                for student_group in other_student_groups_in_group[group]:
                    if (plan[student_group][1] == day_of_week and
                            (curr_time - subject_dict[student_group][0]) <= plan[student_group][0] <= (curr_time + subject_dict[group][0]) + 15):
                        student_ok = False
                        break
                # Sprawdzamy, czy dostępna jest jakakolwiek sala
                if student_ok:
                    room_ok = False
                    remembered_room = np.nan
                    for room in subject_dict[group][1]:
                        current_room_ok = True
                        for room_group in groups_that_use_room[room]:
                            if room_group == group:
                                continue
                            if (plan[room_group][1] == day_of_week and
                                    (curr_time - subject_dict[room_group][0]) <= plan[room_group][0] <= (curr_time + subject_dict[group][0]) + 15):
                                current_room_ok = False
                                break
                        if current_room_ok:
                            room_ok = True
                            remembered_room = room
                            break
                    if room_ok:
                        plan[group][0] = curr_time
                        plan[group][1] = day_of_week
                        plan[group][2] = remembered_room
                        group_not_assigned = False
            if group_not_assigned:
                curr_time += subject_dict[group][0] + 15
                if curr_time >= 720 - subject_dict[group][0]: # Oznacza że zajęcia skończyłyby się po 20:00
                    curr_time = 0
                    day_of_week += 1
                    if day_of_week > 4: # Oznacza, że nie ma więcej dni w planie
                        unassigned_groups.append(group)
                        break
    return plan, unassigned_groups

