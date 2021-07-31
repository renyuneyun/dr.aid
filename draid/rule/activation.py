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

from functools import reduce
from typing import Dict, Optional, Tuple

from .stage import (
        Stage,
        stage_mapping,
        )


ACTIVATION_CONDITION_EXPR = Optional[Tuple[str, Tuple[str, Optional[str]]]]


class ActivationCondition:

    @staticmethod
    def from_raw(ac_expr):
        if ac_expr is None:
            return SingleActivationCondition.from_raw(ac_expr)
        if ac_expr[0] in {And, Or, Not}:
            return ac_expr[0](
                *(ActivationCondition.from_raw(ac_e) for ac_e in ac_expr[1:])
                )
        else:
            return SingleActivationCondition.from_raw(ac_expr)

    def dump(self) -> Optional[str]:
        return NotImplemented

    def __eq__(self, o):
        if o is None:
            return False
        if self.__class__ != o.__class__:
            return False
        return True

    def is_met(self, current_stage: Stage,
               function: Optional[str], info: Dict[str, str]) -> bool:
        return NotImplemented


class SingleActivationCondition(ActivationCondition):

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
                    "Invalid syntax for SingleActivationCondition expression")


class Never(SingleActivationCondition):

    def dump(self):
        return None

    def is_met(self, current_stage: Stage,
               function: Optional[str], info: Dict[str, str]) -> bool:
        return False

    def __repr__(self) -> str:
        return 'AC(Never)'


class EqualAC(SingleActivationCondition):

    def __init__(self, slot, value):
        self.slot = slot
        if value == '*':
            self.value = None
        else:
            self.value = value

    def dump(self):
        value = json.dumps(self.value) if self.value is not None else '*'
        return "{} = {}".format(self.slot, value)

    def __eq__(self, o):
        if not super().__eq__(o):
            return False
        return self.slot == o.slot and self.value == o.value

    def is_met(self, current_stage: Stage,
               function: Optional[str], info: Dict[str, str]) -> bool:
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

    def __repr__(self) -> str:
        return f'AC({self.slot} = {self.value})'


class NEqualAC(SingleActivationCondition):

    def __init__(self, slot, value):
        self.slot = slot
        if value == '*':
            self.value = None
        else:
            self.value = value

    def dump(self):
        value = json.dumps(self.value) if self.value is not None else '*'
        return "{} = {}".format(self.slot, value)

    def __eq__(self, o):
        if not super().__eq__(o):
            return False
        return self.slot == o.slot and self.value == o.value

    def is_met(self, current_stage: Stage,
               function: Optional[str], info: Dict[str, str]) -> bool:
        if self.slot == 'action':
            if self.value is not None:
                return function != self.value
            else:
                return function is None
            return False
        elif self.slot == 'stage':
            if self.value is not None:
                return stage_mapping[current_stage.__class__] != self.value
            else:
                return False
        else:
            if self.slot in info:
                if self.value is not None:
                    return info[self.slot] != self.value
                else:  # None for self.value represents "any"
                    return True
        return False

    def __repr__(self) -> str:
        return f'AC({self.slot} != {self.value})'


class Connective(ActivationCondition):

    def __init__(self, *exprs):
        if len(exprs) == 1 and \
                not isinstance(exprs[0], SingleActivationCondition):
            # If passed in without unpacking
            self._expr = tuple(exprs[0])
        else:
            self._expr = exprs

    def __eq__(self, o):
        if not super().__eq__(o):
            return False
        return self._expr == o._expr


class And(Connective):

    def dump(self) -> Optional[str]:
        return '({} and {})'.format(self._expr[0].dump(), self._expr[1].dump())

    def is_met(self, current_stage: Stage,
               function: Optional[str], info: Dict[str, str]) -> bool:
        return reduce(
                lambda a, b: a and b,
                map(
                    lambda ac: ac.is_met(current_stage, function, info),
                    self._expr)
                )

    def __repr__(self) -> str:
        # return f'And({",".join(repr(expr) for expr in self._expr)})'
        return f'And({repr(self._expr[0])},{repr(self._expr[1])})'


class Or(Connective):

    def dump(self) -> Optional[str]:
        return '({} or {})'.format(self._expr[0].dump(), self._expr[1].dump())

    def is_met(self, current_stage: Stage,
               function: Optional[str], info: Dict[str, str]) -> bool:
        return reduce(
                lambda a, b: a or b,
                map(
                    lambda ac: ac.is_met(current_stage, function, info),
                    self._expr)
                )


class Not(Connective):

    def __init__(self, expr):
        self._expr = expr

    def dump(self) -> Optional[str]:
        return '(not {})'.format(self._expr.dump())

    def is_met(self, current_stage: Stage,
               function: Optional[str], info: Dict[str, str]) -> bool:
        return not self._expr.is_met(current_stage, function, info)
