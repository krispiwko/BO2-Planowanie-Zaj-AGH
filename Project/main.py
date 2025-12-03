#!/usr/bin/python
# -*- coding: utf-8 -*-

from read_data import *
from init_sol import init_sol

def main():
    student_dict = get_student_dict()
    subject_dict = get_subject_dict()
    lecturer_dict = get_lecturer_dict()

    for k,v in subject_dict.items():
        print(f"{{ '{k}': {v}}}")

    print("\n\n")

    for k,v in student_dict.items():
        print(f"{{ '{k}': {v}}}")

    print("\n\n")

    for k,v in lecturer_dict.items():
        print(f"{{ '{k}': {v}}}")

    starting_plan, unassigned_groups = init_sol(student_dict, subject_dict, lecturer_dict)
    for k, v in starting_plan.items():
        print(f"{{ '{k}': {v}}}")
    print(unassigned_groups)
    return

if __name__ == "__main__":
    main()