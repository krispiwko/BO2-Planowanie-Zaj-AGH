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
        collision_costs[sub] = {CollisionEnum.STUDENT_COST: 0,
                                CollisionEnum.LECTURER_COST: 0,
                                CollisionEnum.ROOM_COST: 0}

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
            collision_costs[sub[0]][collision_enum] += coeffs["collision_cost"]

        if end > latest_end:
            latest_end = end


def goal_function(plan, data, only_collisions=True):

    group_costs = {GroupCostsEnum.COLLISION: {},
                   GroupCostsEnum.MAX_TIME: {},
                   GroupCostsEnum.WINDOW: {}}

    collision_costs = get_collision_costs(plan, data)

    fun_sum = sum(
        cost
        for subject_costs in collision_costs.values()
        for cost in subject_costs.values()
    )
    group_costs[GroupCostsEnum.COLLISION] = collision_costs

    if not only_collisions:
        for student in data[DataEnum.STUDENT_DICT].keys():
            groups_on_day = {day_of_week: [group for group in students_data[student] if plan[group][1] == day_of_week]
                             for day_of_week
                             in range(0, 5)}
            group_costs[GroupCostsEnum.COLLISION][student] = []
            group_costs[GroupCostsEnum.MAX_TIME][student] = [[], [], [], [], []]
            group_costs[GroupCostsEnum.WINDOW][student] = []
            for day_of_week in range(0, 5):
                time_sum = 0
                for group in groups_on_day[day_of_week]:
                    time_sum += data[DataEnum.SUBJECT_DICT][group][0]
                if time_sum > coeffs_students["max_time_in_one_day"]:
                    fun_sum += coeffs_students["cost_per_minute_over_limit"] * (
                            time_sum - coeffs_students["cost_per_minute_over_limit"])
                    group_costs[GroupCostsEnum.MAX_TIME][student][day_of_week] = groups_on_day[day_of_week]
                chronological_groups = sorted(groups_on_day[day_of_week], key=lambda x: plan[x][0])
                group_costs[GroupCostsEnum.WINDOW][student] = []
                for i in range(1, len(chronological_groups)):
                    if plan[chronological_groups[i]][0] - plan[chronological_groups[i - 1]][0] > coeffs_students[
                        "min_window_length"]:
                        fun_sum += coeffs_students["window_cost"]
                        group_costs[GroupCostsEnum.WINDOW][student] += [chronological_groups[i - 1], chronological_groups[i]]
        for lecturer in data[DataEnum.LECTURER_DICT].keys():
            groups_on_day = {day_of_week: [group for group in data[DataEnum.LECTURER_DICT][lecturer] if
                                           plan[group][1] == day_of_week] for day_of_week
                             in range(0, 5)}
            group_costs[GroupCostsEnum.MAX_TIME][lecturer] = [[], [], [], [], []]
            group_costs[GroupCostsEnum.WINDOW][lecturer] = []
            for day_of_week in range(0, 5):
                time_sum = 0
                for group in groups_on_day[day_of_week]:
                    time_sum += data[DataEnum.SUBJECT_DICT][group][0]
                if time_sum > coeffs_lecturers["max_time_in_one_day"]:
                    fun_sum += coeffs_lecturers["cost_per_minute_over_limit"] * (
                            time_sum - coeffs_lecturers["cost_per_minute_over_limit"])
                    group_costs[GroupCostsEnum.MAX_TIME][lecturer][day_of_week] = groups_on_day[day_of_week]
                chronological_groups = sorted(groups_on_day[day_of_week], key=lambda x: plan[x][0])
                for i in range(1, len(chronological_groups)):
                    if plan[chronological_groups[i]][0] - plan[chronological_groups[i - 1]][0] > coeffs_lecturers[
                        "min_window_length"]:
                        fun_sum += coeffs_lecturers["window_cost"]
                        group_costs[GroupCostsEnum.WINDOW][lecturer] += [chronological_groups[i - 1], chronological_groups[i]]

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

def change_plan(plan, group_costs, data):

    collision_costs = group_costs[GroupCostsEnum.COLLISION]
    worst_collision_cost = 0
    worst_collision_type = -1

    changed_subject = None

    for coll_type in CollisionEnum:
        sub_with_max_cost = max(
            collision_costs.keys(),
            key=lambda sub: collision_costs[sub][coll_type]
        )
        max_cost = collision_costs[sub_with_max_cost][coll_type]

        if max_cost > worst_collision_cost:
            worst_collision_cost = max_cost
            worst_collision_type = coll_type
    subject_data = data[DataEnum.SUBJECT_DICT]
    if worst_collision_type != -1:
        bad = [x for x in sorted(collision_costs.keys(),
                                 key=lambda s: collision_costs[s][worst_collision_type],
                                 reverse=True
                                 )[:3] if collision_costs[x][worst_collision_type] != 0]

        most_wanted = choice(bad)
        changed_subject = most_wanted
        changed = True
        if worst_collision_type == CollisionEnum.STUDENT_COST:
            other_groups = data[DataEnum.OTHER_STUDENT_GROUPS][most_wanted]
            changed = change_time_and_day(plan, most_wanted, subject_data, other_groups)
        elif worst_collision_type == CollisionEnum.LECTURER_COST:
            lecturer_data = data[DataEnum.LECTURER_DICT]
            lecturer = subject_data[most_wanted][2]
            other_groups = lecturer_data[lecturer]
            changed = change_time_and_day(plan, most_wanted, subject_data, other_groups)
        elif worst_collision_type == CollisionEnum.ROOM_COST:
            room_data = data[DataEnum.ROOM_GROUPS]
            rooms = subject_data[most_wanted][1]
            room_collision_nums = {r: {} for r in rooms}
            min_collision_nums = {r: 999 for r in rooms}
            for r in rooms:
                other_groups = room_data[r]
                success, collision_num = try_to_change_time_and_day(plan, most_wanted, subject_data, other_groups)
                if collision_num is None and plan[most_wanted][2] == r:
                    changed = False
                    break
                if success:
                    plan[most_wanted][2] = r
                    break
                else:
                    room_collision_nums[r] = collision_num
            else:
                for r in rooms:
                    min_collision_nums[r] = min(room_collision_nums[r].values())
                min_coll_num = min(min_collision_nums.values())
                possible_rooms = [r for r in rooms if min_collision_nums[r] == min_coll_num]
                possible_slots = []
                for r in possible_rooms:
                    possible_slots.extend([(slot_time, slot_day, r) for slot_time, slot_day in room_collision_nums[r]
                                           if room_collision_nums[(slot_time, slot_day)] == min_coll_num])
                slot = choice(possible_slots)
                if plan[most_wanted][0] == slot[0] and plan[most_wanted][1] == slot[1] and plan[most_wanted][2] == slot[2]:
                    changed = False
                else:
                    plan[most_wanted][0] = slot[0]
                    plan[most_wanted][1] = slot[1]
                    plan[most_wanted][2] = slot[2]
        if not changed:
            p = choice(list(subject_data.keys()))
            sala = plan[p][2]
            plan[p] = [randrange(0, 720 - 90, 15), randrange(0, 5), sala]

            changed_subject = p

    return plan, [changed_subject]


class OptimazeSol(object):
    def __init__(self):
        self.T = 0
        self.start_T = 5000
        self.data = None
        self.alpha = 0.99
        self.T_eps = 0.000001
        self.max_iter = 10_000
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

        if self.iter >= self.max_iter or self.T < self.T_eps:
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
