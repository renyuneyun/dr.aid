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
from typing import Dict, List, Optional, Tuple, Union

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
        def instantiate(name: str, raw_attribute: Optional[Union[str, List[str]]] = None, attribute: Optional[Union[AttributeValue, List[AttributeValue]]] = None):
            obj = Attribute()
            obj._init(name, raw_attribute, attribute)
            return obj

        @staticmethod
        def merge(first: 'Attribute', second: 'Attribute') -> Tuple['Attribute', List[int]]:
            assert first.attributeName == second.attributeName
            new = first.clone()
            diff = []
            for i, pr in enumerate(second.hasValue):
                try:
                    index = new.hasValue.index(pr)
                except ValueError:
                    index = len(new.hasValue)
                    new.hasValue.append(pr)
                diff.append(index - i)
            return new, diff

        def _init(self, name: str, raw_attribute: Optional[Union[str, List[str]]] = None, attribute: Optional[Union[AttributeValue, List[AttributeValue]]] = None):
            self.attributeName = name
            if attribute:
                if isinstance(attribute, AttributeValue):
                    self.hasValue.append(attribute)
                else:
                    self.hasValue.extend(attribute)
            elif raw_attribute:
                if isinstance(raw_attribute, str):
                    self.hasValue.append(AttributeValue.instantiate(raw_attribute))
                else:
                    self.hasValue.extend([AttributeValue.instantiate(at) for at in raw_attribute])

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

        def dump(self) -> str:
            s = "attribute {}".format(self.attributeName)
            ss = " {}".format(self.hasValue[0].value())
            if len(self.hasValue) >= 1:
                for pr in self.hasValue[1:]:
                    ss += ", {}".format(pr.value())
            return "{} [{}] .".format(s, ss)

        def clone(self) -> 'Attribute':
            new = Attribute.instantiate(self.attributeName, attribute=[v.clone() for v in self.hasValue])
            return new

        def get(self, index: int) -> AttributeValue:
            return self.hasValue[index]

