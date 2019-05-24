#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/05/23 17:20:34
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from .stage import Stage, Imported


class ActivationCondition:

    def is_met(self, current_stage: Stage) -> bool:
        raise NotImplementedError


class Never(ActivationCondition):

    def is_met(self, current_stage: Stage) -> bool:
        return False


class WhenImported(ActivationCondition):

    def is_met(self, current_stage: Stage) -> bool:
        return isinstance(current_stage, Imported)
