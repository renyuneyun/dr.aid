#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/06/29 11:53:44
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from typing import Optional

from draid.defs.exception import IllegalCaseError

from .proto import Thing, Obligation, get_obligation

class OntologiableString:
    def __init__(self, s: str):
        self._s = s
        parts = s.split(':')
        if len(parts) == 1:
            self.prefix = None
            self.name = parts[0]
            self._onto = self._get_from_ontology(self.prefix, self.name)
        elif len(parts) == 2:
            self.prefix = parts[0] + ':'
            self.name = parts[1]
            self._onto = self._get_from_ontology(self.prefix, self.name)
        else:
            raise IllegalCaseError("String is neither a normal string nor an ontology reference")

    def _get_from_ontology(self, prefix: Optional[str], name: str) -> Thing:
        return NotImplemented

    def get(self) -> Thing:
        return self._onto

    def dump(self) -> str:
        return self._s
        # if self.prefix:
        #     return self.prefix + self.name
        # else:
        #     return self.name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self._s != other._s:
                return False
            return True
        else:
            return NotImplemented

    def __repr__(self):
        if self.prefix:
            return f'{self.prefix}{self.name}'
        else:
            return f'{self._s}'


class ObligationOntoString(OntologiableString):
    def _get_from_ontology(self, prefix: Optional[str], name: str) -> Obligation:
        return get_obligation(name)
