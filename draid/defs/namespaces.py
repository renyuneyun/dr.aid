#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/01 18:39:45
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from rdflib import Namespace

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
PROV = Namespace('http://www.w3.org/ns/prov#')
S_PROV = Namespace('http://s-prov/ns/#')
MINE = Namespace('http://draid/ns/#')

NS = {
        'rdf': RDF,
        'rdfs': RDFS,
        'prov': PROV,
        's-prov': S_PROV,
        'mine': MINE,
}

