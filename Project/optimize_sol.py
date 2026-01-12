#!/usr/bin/python
# -*- coding: utf-8 -*-
from copy import deepcopy
from random import randint, random, randrange, choice

from imgui import DATA_TYPE_FLOAT
from enums import *
import numpy as np
from init_sol import insert_group_without_collision, modify_time_and_day

coeffs_students = {
    "collision_cost": 5,
    "max_time_in_one_day": 360,
    "cost_per_minute_over_limit": 0.01,
    "min_window_length": 90,
    "window_cost": 2,
}
coeffs_lecturers = {
    "collision_cost": 100,
    "max_time_in_one_day": 360,
    "cost_per_minute_over_limit": 0.01,
    "min_window_length": 90,
    "window_cost": 2,
}
coeffs_rooms = {
    "collision_cost": 100
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


def get_collision_costs(plan, data):
    student_data = data[DataEnum.STUDENT_DICT]
    students = student_data.keys()
    lecturer_data = data[DataEnum.LECTURER_DICT]
    lecturers = lecturer_data.keys()
    room_groups = data[DataEnum.ROOM_GROUPS]
    rooms = room_groups.keys()
    subject_data = data[DataEnum.SUBJECT_DICT]
    subjects = subject_data.keys()
    collision_costs = {}
    for sub in subjects:
        collision_costs[sub] = 0

    for i in range(5):
        for s in students:
            add_collisions(plan, collision_costs,
                           s, student_data,
                           subject_data, i,
                           CollisionEnum.STUDENT_COST, coeffs_students)
        for le in lecturers:
            add_collisions(plan, collision_costs,
                           le, lecturer_data,
                           subject_data, i,
                           CollisionEnum.LECTURER_COST, coeffs_lecturers)
        for r in rooms:
            add_collisions(plan, collision_costs,
                           r, room_groups,
                           subject_data, i,
                           CollisionEnum.ROOM_COST, coeffs_rooms)
    return collision_costs


def add_collisions(plan, collision_costs, x, x_data, subject_data, day, collision_enum, coeffs):
    subjects = [(k, plan[k][0]) for k in x_data[x] if plan[k][1] == day]
    subjects.sort(key=lambda x: x[1])
    latest_end = 0
    for sub in subjects:
        start = sub[1]
        duration = subject_data[sub[0]][0]

        end = start + duration

        if start < latest_end:
            collision_costs[sub[0]] += coeffs["collision_cost"]

        if end > latest_end:
            latest_end = end


def goal_function(plan, data):

    group_costs = {GroupCostsEnum.COLLISION: {}}

    collision_costs = get_collision_costs(plan, data)

    fun_sum = sum(
        cost
        for cost in collision_costs.values()
    )
    group_costs[GroupCostsEnum.COLLISION] = collision_costs

    return fun_sum, group_costs, collision_costs

def try_to_change_time_and_day(plan, most_wanted, subject_data, other_groups):
    curr_time = 0
    curr_day = 0
    # g1_day = plan[most_wanted][1]
    # g1_time = plan[most_wanted][0]
    g1_duration = subject_data[most_wanted][0]
    collision_num = {slot: 0 for slot in
                     ((time, day) for day in range(5) for time in range(0, 720 - g1_duration + 15, 15))}
    while curr_day != 5:
        curr_slot = (curr_time, curr_day)
        for g in other_groups:
            if most_wanted == g:
                continue
            g2_day = plan[g][1]
            g2_time = plan[g][0]
            g2_duration = subject_data[g][0]
            if curr_day == g2_day and curr_time - g2_duration - 15 < g2_time < curr_time + g1_duration + 15:
                collision_num[curr_slot] += 1
        if collision_num[curr_slot] == 0:
            if plan[most_wanted][0] == curr_time and plan[most_wanted][1] == curr_day:
                return False, None
            plan[most_wanted][0] = curr_time
            plan[most_wanted][1] = curr_day
            return True, collision_num
        curr_time += 15
        if curr_time > 720 - g1_duration:
            curr_time = 0
            curr_day += 1

    return False, collision_num


def change_time_and_day(plan, most_wanted, subject_data, other_groups):
    success, collision_num = try_to_change_time_and_day(plan, most_wanted, subject_data, other_groups)
    if collision_num is None:
        return False
    if not success:
        slots = sorted(collision_num.keys(),
                       key=lambda slot: collision_num[slot]
                       )[:1]
        best_slot = choice(slots)
        if plan[most_wanted][0] == best_slot[0] and plan[most_wanted][1] == best_slot[1]:
            return False
        plan[most_wanted][0] = best_slot[0]
        plan[most_wanted][1] = best_slot[1]
        return True



def change_randomly(data, plan):

    subject_data = data[DataEnum.SUBJECT_DICT]

    p = choice(list(subject_data.keys()))

    sala = choice(subject_data[p][1])
    plan[p] = [randrange(0, 720 - 90, 15), randrange(0, 5), sala]
    return p


def change_plan(plan, group_costs, data):

    collision_costs = group_costs[GroupCostsEnum.COLLISION]
    bad = [x for x in sorted(collision_costs.keys(), key=lambda sub: collision_costs[sub], reverse=True)
           if collision_costs[x] != 0]
    changed = False
    changed_subject = None
    for most_wanted in bad:
        subject_data = data[DataEnum.SUBJECT_DICT]
        other_groups_student = data[DataEnum.OTHER_STUDENT_GROUPS][most_wanted]
        other_groups_lecturer = data[DataEnum.LECTURER_DICT][subject_data[most_wanted][2]]
        other_groups_room = data[DataEnum.ROOM_GROUPS][plan[most_wanted][2]]
        other_groups = list(other_groups_student) + list(other_groups_lecturer) + list(other_groups_room)
        other_groups = set(other_groups)
        changed = change_time_and_day(plan, most_wanted, subject_data, other_groups)
        if changed:
            changed_subject = most_wanted
            break
    if not changed:
        changed_subject = change_randomly(data, plan)
    return plan, [changed_subject]

class OptimazeSol(object):
    def __init__(self):
        self.stagnation = 0
        self.prev_goal_sum = None
        self.T = 0
        self.start_T = 500
        self.data = None
        self.alpha = 0.999
        self.T_eps = 0.0001
        self.max_iter = np.inf

        self.iter = 0
        self.best_plan = None
        self.best_goal_sum = None

        self.cur_plan = None
        self.cur_goal_func = None
        self.last_changed = []

        self.goal_log = []

    def setup(self, plan, data):
        self.best_plan = plan

        self.cur_plan = plan

        self.T = self.start_T
        self.data = data
        self.iter = 0
        self.cur_goal_sum, self.cur_marked_groups, _ = goal_function(self.best_plan, self.data)
        self.best_goal_sum = self.cur_goal_sum
        self.goal_log = []

    def step(self):
        if self.prev_goal_sum == self.cur_goal_sum:
            self.stagnation += 1
            if self.stagnation > 10:
                change_randomly(self.data, self.cur_plan)
                self.cur_goal_sum, self.cur_marked_groups, _ = goal_function(self.cur_plan, self.data)
                self.stagnation = 0
        self.prev_goal_sum = self.cur_goal_sum

        new_plan, self.last_changed = change_plan(deepcopy(self.cur_plan), self.cur_marked_groups, self.data)
        new_goal_sum, self.cur_marked_groups, _= goal_function(new_plan, self.data)
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
        else:
            self.last_changed = []

        self.T *= self.alpha
        self.iter += 1
        self.goal_log.append(self.cur_goal_sum)

        if self.iter >= self.max_iter or self.T < self.T_eps or self.cur_goal_sum == 0:
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

if __name__ == "__main__":
    print([x for x in range(0, 720 - 90 + 15, 15)])
