#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/05/23 11:37:02
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

import json

from typing import Dict, Optional, Tuple

from .stage import (
        Stage,
        stage_mapping,
        )


ACTIVATION_CONDITION_EXPR = Optional[Tuple[str, Tuple[str, Optional[str]]]]


class ActivationCondition:

    @staticmethod
    def from_raw(ac_expr: ACTIVATION_CONDITION_EXPR):
        if ac_expr is None:
            return Never()
        elif ac_expr[0] == '=':
            return EqualAC(*ac_expr[1])
        elif ac_expr[0] == '!=':
            return NEqualAC(*ac_expr[1])
        else:
            raise SyntaxError(
                    "Invalid syntax for ActivationCondition expression")

    def dump(self) -> Optional[str]:
        return NotImplemented

    def __eq__(self, o):
        if o is None:
            return False
        if self.__class__ != o.__class__:
            return False
        return True

    def is_met(self, current_stage: Stage,
               function: Optional[str], info: Dict[str, str]):
        return NotImplemented


class Never(ActivationCondition):

    def dump(self):
        return None

    def is_met(self, current_stage: Stage,
               function: Optional[str], info: Dict[str, str]):
        return False


class EqualAC(ActivationCondition):

    def __init__(self, slot, value):
        self.slot = slot
        self.value = value

    def dump(self):
        value = json.dumps(self.value) if self.value is not None else '*'
        return "{} = {}".format(self.slot, value)

    def __eq__(self, o):
        if not super().__eq__(o):
            return False
        return self.slot == o.slot and self.value == o.value

    def is_met(self, current_stage: Stage,
               function: Optional[str], info: Dict[str, str]):
        if self.slot == 'action':
            if self.value is not None:
                return function == self.value
            else:
                return function is not None
            return False
        elif self.slot == 'stage':
            if self.value is not None:
                return stage_mapping[current_stage.__class__] == self.value
            else:
                return True
        else:
            if self.slot in info:
                if self.value is not None:
                    return info[self.slot] == self.value
                else:  # None for self.value represents "any"
                    return True
        return False


class NEqualAC(ActivationCondition):

    def __init__(self, slot, value):
        self.slot = slot
        self.value = value

    def dump(self):
        value = json.dumps(self.value) if self.value is not None else '*'
        return "{} = {}".format(self.slot, value)

    def __eq__(self, o):
        if not super().__eq__(o):
            return False
        return self.slot == o.slot and self.value == o.value

    def is_met(self, current_stage: Stage,
               function: Optional[str], info: Dict[str, str]):
        if self.slot == 'action':
            if self.value is not None:
                return function != self.value
            else:
                return function is not None
            return False
        elif self.slot == 'stage':
            if self.value is not None:
                return stage_mapping[current_stage.__class__] != self.value
            else:
                return True
        else:
            if self.slot in info:
                if self.value is not None:
                    return info[self.slot] != self.value
                else:  # None for self.value represents "any"
                    return True
        return False
