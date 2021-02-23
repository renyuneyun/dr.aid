#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/05/14 11:20:04
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

import pytest

from exp import parser
from exp.rule import ObligationDeclaration, DataRuleContainer, AttributeCapsule
from exp.proto import WhenImported


@pytest.mark.parametrize('name, values', [
    ("pr1", (('str', "a"), ('str', "b"))),
    ])
def test_attribute_serialise(name, values):
    pr = AttributeCapsule.from_raw(name, values)
    s = pr.dump()
    _, (name, value) = parser.call_parser_data_rule(s, 'attribute_decl')
    attr_re = AttributeCapsule.from_raw(name, value)
    assert pr == attr_re


@pytest.mark.parametrize('name, validity_binding, activation_condition', [
    ('ru1', [('a', 1)], None),
    ('"ru1"', [('a', 1)], None),
    ('"ru1"', [('a', 1)], WhenImported()),
    ])
def test_data_rule_serialise(name, validity_binding, activation_condition):
    r = ObligationDeclaration(name, validity_binding, activation_condition)
    s = r.dump()
    _, (obligated_action, validity_binding, activation_condition_ref) = parser.call_parser_data_rule(s, 'obligation_decl')
    r2 = ObligationDeclaration.from_raw(obligated_action, validity_binding, activation_condition_ref)
    assert r2 == r


@pytest.mark.parametrize('obligations, amap', [
    ([ObligationDeclaration('ob1', [('pr1', 0)]), ObligationDeclaration('ob2', [('pr1', 1)])],
        [AttributeCapsule.from_raw('pr1', [('str', '1'), ('str', '2')])]),
    ])
def test_whole_data_rule_serialise(obligations, amap):
    rule = DataRuleContainer(obligations, amap)
    s = rule.dump()
    print(f"serialised: {s}")
    rule2 = parser.parse_data_rule(s)
    assert rule2 == rule

