#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

INDEX_TIME = 0
INDEX_ROOMS = 1
INDEX_LECTURER = 2

def get_student_dict():
    output_temp = {}
    output = {}

    with open(".\\data\\studenci_przedmioty.csv", "rt") as f:
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

    return output

def get_subject_time():
    output = {}
    with open(".\\data\\przedmioty_czas_trwania.csv", "rt") as f:
        lines = f.readlines()
        for l in lines:
            split = l.split(';')
            output[split[0]] = int(split[1])

    return output

def get_subject_rooms():
    output = {}
    with open(".\\data\\przedmioty_sale.csv", "rt") as f:
        lines = f.readlines()
        for l in lines:
            split = l.split(';')
            output[split[0]] = split[1].split(',')

    return output

def get_subject_lecturer():
    output = {}
    group_counts = {}
    with open(".\\data\\przedmioty_prowadzacy.csv", "rt") as f:
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

