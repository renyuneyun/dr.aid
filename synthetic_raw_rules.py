#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/06/12 17:35:04
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from rdflib import URIRef


_G1 = (
        'http://schema.org#2a3c188f8cd6-19-b9fee0c2-7179-11e9-bd29-0242ac120003',
        {
            '123': '{}',
            }
        )


_GENERAL_FLOW_RULES = {  # functionName: rule
        'NumberProducer': '',
        'Increase': '',
        'Redispatch': '''{'output0': ['input0', 'input1'], 'output1': ['input0', 'input2'], 'output3': ['input1', 'input2']}''',
        }


FLOW_RULES = {
        URIRef(g_id): {URIRef(comp): r for comp, r in rules.items()}
        for g_id, rules in {
            _G1[0]: _G1[1],
            }.items()
        }

FLOW_RULES[None] = _GENERAL_FLOW_RULES

