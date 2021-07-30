#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/05/25 17:15:56
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from typing import Any


class Attribute:
    '''
    Stores the attribute type and value in this container class.
    The checking of types (ontolog matching?) may be implemented as a separate
    function here. Ignored at the moment.
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
