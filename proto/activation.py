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

import os
from owlready2 import Thing, ClassAtom
from typing import Optional

from .ontomix import import_ontology
from .stage import Stage, Imported

onto = import_ontology("core.owl")

with onto:
    class ActivationCondition(Thing):
        def is_met(self, current_stage: Stage, function: Optional[str]) -> bool:
            raise NotImplementedError

    class Never(Thing):
        def is_met(self, current_stage: Stage, function: Optional[str]) -> bool:
            return False

    class OnImport(Thing):
        def is_met(self, current_stage: Stage, function: Optional[str]) -> bool:
            return isinstance(current_stage, Imported)

    class OnAsInput(Thing):
        pass

    class WhenImported(OnImport):
        equivalent_to = [OnImport]

    class WhenPublish(Thing):
        def is_met(self, current_stage: Stage, function: Optional[str]) -> bool:
            if function == 'publish':
                return True
            return False

    def eq(a, b) -> bool:
        assert a != None
        assert b != None
        return isinstance(b, a.__class__)

    def is_ac(name: str) -> bool:
        clz = onto[name]
        if clz is None:
            return False
        return ActivationCondition in clz.ancestors()

    def obtain(name: str) -> ActivationCondition:
        return onto[name]()

    def dump(ac: ActivationCondition) -> Optional[str]:
        if isinstance(ac, Never):
            return None
        assert len(ac.is_instance_of) == 1
        clz = ac.is_instance_of[0]
        return ClassAtom.get_name(clz)

