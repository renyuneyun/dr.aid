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

from draid.defs.exception import OntologyTypeException

from .utils import import_ontology

base_onto = import_ontology("core.owl")

with base_onto:
    class Obligation(Thing):
        pass


def get_obligation(name: str) -> Obligation:
    #onto = import_ontology(path)
    onto = base_onto
    ob_class = onto[name]
    if isinstance(ob_class, Obligation):
        return ob_class
    if not ob_class:
        raise OntologyTypeException('Expecting Obligation/ObligatedAction, but found nothing. From representation: {}'.format(name))
    raise OntologyTypeException('Expecting Obligation/ObligatedAction, but got {}. From representation: {}'.format(ob_class.__class__, name))
