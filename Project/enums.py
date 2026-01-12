#!/usr/bin/python
# -*- coding: utf-8 -*-
from enum import Enum

class DataEnum(Enum):
    STUDENT_DICT = 0
    SUBJECT_DICT = 1
    LECTURER_DICT = 2
    OTHER_STUDENT_GROUPS = 3
    ROOM_GROUPS = 4

class MarkEnum(Enum):
    MAX_TIME = 0
    WINDOW = 1
    COLLISION = 2