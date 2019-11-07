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
from exp.rule import Obligation, DataRuleContainer, PropertyCapsule
from exp.proto import WhenImported


@pytest.mark.parametrize('name, values', [
    ("pr1", ("a", "b")),
    ])
def test_property_serialise(name, values):
    pr = PropertyCapsule(name, values)
    s = pr.dump()
    name, content, remaining = parser.read_property(s)
    assert not remaining.strip()
    pr2 = PropertyCapsule(name, content)
    assert pr == pr2


@pytest.mark.parametrize('name, attribute, activation_condition', [
    ('ru1', ('a', 1), None),
    ('ru1', ('a', 1), WhenImported()),
    ])
def test_data_rule_serialise(name, attribute, activation_condition):
    r = Obligation(name, attribute, activation_condition)
    s = r.dump()
    name, property, activation_condition, remaining = parser.read_obligation(s)
    assert not remaining.strip()
    r2 = Obligation(name, property, activation_condition)
    assert r2 == r


@pytest.mark.parametrize('obligations, pmap', [
    ([Obligation('ob1', ('pr1', 0)), Obligation('ob2', ('pr1', 1))],
        {'pr1': PropertyCapsule('pr1', ['1', '2'])}),
    ])
def test_whole_data_rule_serialise(obligations, pmap):
    rule = DataRuleContainer(obligations, pmap)
    s = rule.dump()
    rule2 = parser.parse_data_rule(s)
    assert rule2 == rule

