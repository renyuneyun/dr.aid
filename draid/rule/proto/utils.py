#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/10/03 23:24:20
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

import os
from owlready2 import onto_path, get_ontology

dir_path = os.path.dirname(os.path.realpath(__file__))
onto_path.append(dir_path)

def import_ontology(name):
    onto = get_ontology(name)
    onto.load()
    return onto
