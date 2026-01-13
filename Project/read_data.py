#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import random
from enums import DataEnum

INDEX_TIME = 0
INDEX_ROOMS = 1
INDEX_LECTURER = 2

data_folder = ".\\data\\"

def set_data_folder(path):
    global data_folder
    data_folder = path

def get_student_dict():
    # random.seed(67)
    output_temp = {}
    output = {}

    csv_path = os.path.join(data_folder, "studenci_przedmioty.csv")

    with open(csv_path, "rt") as f:
        lines = f.readlines()
        student_index = 0
        for l in lines:
            split = l.split(';')
            student_type = split[0]
            student_subjects = split[1].split(',')
            student_count = int(split[2])

            for i in range(student_count):
                output_temp[f"student_{student_index}"] = student_subjects
                student_index += 1

    temp_list_students = list(output_temp.keys())
    temp_list_subjects = [v for k,v in output_temp.items()]
    random.shuffle(temp_list_subjects)

    output_temp = {}
    for i, student in enumerate(temp_list_students):
        output_temp[student] = temp_list_subjects[i]
        

    group_student_count = {}
    for k, v in output_temp.items():
        for sub in v:
            if sub not in group_student_count:
                group_student_count[sub] = 1
            else:
                group_student_count[sub] += 1

    students_per_group = {}
    obj, group_counts = get_subject_lecturer()
    for k, v in group_student_count.items():
        students_per_group[k] = v / group_counts[k]

    group_student_count = {}
    for student, sub_array in output_temp.items():
        new_sub_array = [""] * len(sub_array)
        for i, sub in enumerate(sub_array):
            if sub not in group_student_count:
                group_student_count[sub] = 0
            
            new_sub_array[i] = f"{sub}_gr{int(group_student_count[sub] // students_per_group[sub] + 1)}" 

            group_student_count[sub] += 1
        output[student] = new_sub_array

    print(output)

    return output

def get_subject_time():
    output = {}
    csv_path = os.path.join(data_folder, "przedmioty_czas_trwania.csv")
    with open(csv_path, "rt") as f:
        lines = f.readlines()
        for l in lines:
            split = l.split(';')
            output[split[0]] = int(split[1])

    return output

def get_subject_rooms():
    output = {}
    csv_path = os.path.join(data_folder, "przedmioty_sale.csv")
    with open(csv_path, "rt") as f:
        lines = f.readlines()
        for l in lines:
            split = l.split(';')
            output[split[0]] = split[1].split(',')

    return output

def get_subject_lecturer():
    output = {}
    group_counts = {}
    csv_path = os.path.join(data_folder, "przedmioty_prowadzacy.csv")
    with open(csv_path, "rt") as f:
        lines = f.readlines()
        for l in lines:
            split = l.split(';')
            subject = split[0]
            lecturer_split = split[1].split(',')

            total_group_count = 0
            for i in range(len(lecturer_split)//2):
                lecturer = lecturer_split[2 * i]
                group_count = int(lecturer_split[2 * i + 1])

                for j in range(group_count):
                    output[f"{subject}_gr{total_group_count + 1}"] = lecturer
                    total_group_count += 1
            group_counts[subject] = total_group_count

    return output, group_counts


def get_subject_dict():
    time_dict = get_subject_time()
    room_dict = get_subject_rooms()
    lecturer_dict = get_lecturer_dict()

    output = {}

    for k, v in time_dict.items():
        for ki, vi in lecturer_dict.items():
            for sub in vi:
                if sub.startswith(k):
                    output[sub] = [v, room_dict[k], ki]

    return output

def get_lecturer_dict():
    lecturer_dict, _ = get_subject_lecturer()

    output = {}
    for k,lect in lecturer_dict.items():
        if lect not in output:
            output[lect] = [k]
        else:
            arr = output[lect]
            arr.append(k)
            output[lect] = arr

    return output

def initialize_additional_dicts(student_dict, subject_dict):
    other_student_groups_in_group = {group: set() for group in subject_dict.keys()}
    for student in list(student_dict.keys()):
        for student_group in student_dict[student]:
            for other_student_group in student_dict[student]:
                if other_student_group == student_group:
                    continue
                other_student_groups_in_group[student_group].add(other_student_group)
    # print(other_student_groups_in_group)
    rooms_set = set()
    for group in subject_dict.keys():
        for room in subject_dict[group][1]:
            rooms_set.add(room)
    groups_that_use_room = {room: set() for room in rooms_set}
    for room in rooms_set:
        for group in subject_dict.keys():
            if room in subject_dict[group][1]:
                groups_that_use_room[room].add(group)
    # print(groups_that_use_room)
    return other_student_groups_in_group, groups_that_use_room

def create_data():
    student_dict = get_student_dict()
    subject_dict = get_subject_dict()
    lecturer_dict = get_lecturer_dict()
    other_student_groups, room_groups = initialize_additional_dicts(student_dict,subject_dict)
    data = {DataEnum.STUDENT_DICT:student_dict,
            DataEnum.SUBJECT_DICT:subject_dict,
            DataEnum.LECTURER_DICT:lecturer_dict,
            DataEnum.OTHER_STUDENT_GROUPS:other_student_groups,
            DataEnum.ROOM_GROUPS:room_groups}
    return data

def print_dict(dictionary):
    return 
    print()
    for k, v in dictionary.items():
        print(f"{{ '{k}': {v}}}")

def print_data(data):
    return
    for key in data.keys():
        print()
        print(key)
        if type(data[key]) == dict:
            print_dict(data[key])

