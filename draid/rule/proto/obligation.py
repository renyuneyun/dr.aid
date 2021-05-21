#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/11/07 18:14:07
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from owlready2 import Thing

from .ontomix import import_ontology

onto = import_ontology("core.owl")

with onto:
    class Obligation(Thing):
        pass

