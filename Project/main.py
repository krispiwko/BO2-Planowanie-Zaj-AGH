#!/usr/bin/python
# -*- coding: utf-8 -*-

from read_data import *
from init_sol import *
from write_load_csv import *
from optimize_sol import *

def main():
    data = create_data()
    print_data(data)

    starting_plan, unassigned_groups = init_sol(data)
    print("\n\n")
    print("STARTING_PLAN")
    print_dict(starting_plan)

    print(unassigned_groups)

    print("\n\n")

    write_plan_to_csv(starting_plan)

    loaded_plan = load_plan_from_csv()

    print_dict(loaded_plan)

    identical = True
    for group in starting_plan.keys():
        if starting_plan[group] != loaded_plan[group]:
            identical = False
            print(starting_plan[group], loaded_plan[group])
    print(identical)

    print("\n\n")
    goal_fun_sum, marked_groups = goal_function(starting_plan, unassigned_groups, data)

    print("STARTOWA WARTOŚĆ FUNKCJI CELU:")
    print(goal_fun_sum)

    opt_plan, opt_unassigned_groups, opt_goal_function = optimize_sol(starting_plan, unassigned_groups, data)

    print("KOŃCOWA WARTOŚĆ FUNKCJI CELU:")
    print(opt_goal_function)
    return


if __name__ == "__main__":
    main()