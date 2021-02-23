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
from typing import Any, Dict, List, Optional, Tuple, Union

from .ontomix import import_ontology

onto = import_ontology("core.owl")

with onto:
    class AttributeValue(Thing):

        # pylint: disable=protected-access
        @staticmethod
        def instantiate(value):
            obj = AttributeValue()
            obj._init(value)
            return obj

        def _init(self, value):
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
            return f'AttributeValue({self.value()})'

        def clone(self) -> 'AttributeValue':
            return self

    class Attribute(Thing):

        # pylint: disable=protected-access
        @staticmethod
        def instantiate(name: str, raw_attribute: Optional[str] = None, attribute: Optional[AttributeValue] = None):
            obj = Attribute()
            obj._init(name, raw_attribute, attribute)
            return obj

        def _init(self, name: str, raw_attribute: Optional[str] = None, attribute: Optional[AttributeValue] = None):
            self.attributeName = name
            if attribute:
                self.hasValue = attribute
            elif raw_attribute:
                self.hasValue = AttributeValue.instantiate(raw_attribute)

        def __repr__(self):
            return "{}({} {})".format(self.get_name(), self.attributeName, self.hasValue)

        def __eq__(self, other):
            if isinstance(other, self.__class__):
                if self.attributeName != other.attributeName:
                    return False
                if self.hasValue != other.hasValue:
                    return False
                return True
            else:
                return NotImplemented

        def clone(self) -> 'Attribute':
            new = Attribute.instantiate(self.attributeName, attribute=self.hasValue.clone())
            return new

        def get(self) -> AttributeValue:
            return self.hasValue

# Overrides the definition above. Possibly the definition above is obsolete now.
class Attribute:
    '''
    Stores the attribute type and value in this container class.
    The checking of types (ontolog matching?) may be implemented as a separate function here. Ignored at the moment.
    '''
    def __init__(self, name: str, a_type: str, a_value: Any):
        self.name = name
        self.type = a_type
        self.value = a_value

    def clone(self):
        return Attribute(self.name, self.type, self.value)

    def __repr__(self):
        return "{}({} {})".format(self.name, self.type, self.value)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if not self.name == other.name:
                return False
            if not self.type == other.type:
                return False
            if not self.value == other.value:
                return False
            return True
        else:
            return NotImplemented
