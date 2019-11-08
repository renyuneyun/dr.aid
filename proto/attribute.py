#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/11/07 18:06:16
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from owlready2 import Thing

from .ontomix import import_ontology

onto = import_ontology("core.owl")

with onto:
    class AttributeValue(Thing):
        def __init__(self, value):
            if isinstance(value, Thing):
                self.valueObject = value
            else:
                self.valueData = value

        def __eq__(self, other) -> bool:
            if isinstance(other, self.__class__):
                if self.value() != other.value():
                    return False
                return True
            else:
                return NotImplemented

        def value(self) -> object:
            return self.valueObject if self.valueObject else self.valueData

        def __repr__(self):
            return f'{self.value()}'

    class Attribute(Thing):
        pass

