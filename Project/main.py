#!/usr/bin/python
# -*- coding: utf-8 -*-

from read_data import *
from init_sol import *
from write_load_csv import *

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

    print("\n\n")

    for k, v in starting_plan.items():
        print(f"{{ '{k}': {v}}}")

    print("\n\n")

    print(unassigned_groups)

    print("\n\n")

    write_plan_to_csv(starting_plan)

    loaded_plan = load_plan_from_csv()

    print("\n\n")

    for k, v in loaded_plan.items():
        print(f"{{ '{k}': {v}}}")

    print("\n\n")

    identical = True
    for group in starting_plan.keys():
        if starting_plan[group] != loaded_plan[group]:
            identical = False
            print(starting_plan[group], loaded_plan[group])
    print(identical)
    return

if __name__ == "__main__":
    main()