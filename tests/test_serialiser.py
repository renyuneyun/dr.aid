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

from draid.rule import parser
from draid.rule import ObligationDeclaration, DataRuleContainer, AttributeCapsule, FlowRule, Propagate, Edit, Delete
from draid.rule import EqualAC, NEqualAC, Never
from draid.rule import And, Or, Not


on_publish = EqualAC('action', 'publish')
when_imported = EqualAC('stage', 'import')


NAMESPACES = {
        '': 'test.owl',
        'test': 'test.owl',
        }


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
    (':ru1', [('a', 1)], None),
    ('test:ru1', [('a', 1)], None),
    ('test:ru1', [('a', 1)], when_imported),
    ('test:ru1', [('a', 1)], on_publish),
    ('test:ru1', [('a', 1)], And(on_publish, when_imported)),
    ('test:ru1', [('a', 1)], Or(on_publish, when_imported)),
    ('test:ru1', [('a', 1)], Not(on_publish)),
    ])
def test_data_rule_serialise(name, validity_binding, activation_condition):
    r = ObligationDeclaration(name, validity_binding, activation_condition, namespaces=NAMESPACES)
    s = r.dump()
    print(s)
    _, (obligated_action, validity_binding, activation_condition_ref) = parser.call_parser_data_rule(s, 'obligation_decl')
    r2 = ObligationDeclaration.from_raw(obligated_action, validity_binding, activation_condition_ref, namespaces=NAMESPACES)
    assert r2 == r


@pytest.mark.parametrize('obligations, amap', [
    ([ObligationDeclaration('test:ob1', [('pr1', 0)], namespaces=NAMESPACES), ObligationDeclaration('test:ob2', [('pr1', 1)])],
        [AttributeCapsule.from_raw('pr1', [('str', '1'), ('str', '2')])]),
    ])
def test_whole_data_rule_serialise(obligations, amap):
    rule = DataRuleContainer(obligations, amap)
    s = rule.dump()
    print(f"serialised: {s}")
    rule2 = parser.parse_data_rule(s)
    assert rule2 == rule


@pytest.mark.parametrize('flow_rule_items', [
    [Propagate("input", ["output"])],
    [Propagate("input", ["output1", "output2"])],
    [Propagate("input", ["output1", "output2"]), Propagate("input2", ["output1"])],
    [Propagate("input", ["output1", "output2"]), Edit("str", "bbb", "input", "output1", "attr_name", "str", "aaa")],
    [Propagate("input", ["output1", "output2"]), Edit("str", "bbb", None, None, None, None, None)],
    [Propagate("input", ["output1", "output2"]), Delete("input", "output1", "attr_name", "str", "aaa")],
    [Propagate("input", ["output1", "output2"]), Delete(None, None, None, None, None)],
    [Propagate("input", ["output1", "output2"]), Edit("str", "bbb", "input", "output1", "attr_name", "str", "aaa"), Delete("input", "output1", "attr_name", "str", "aaa")],
    [Propagate("input", ["output1", "output2"]), Delete("input", "output1", "attr_name", "str", "aaa"), Edit("str", "bbb", "input", "output1", "attr_name", "str", "aaa")],
    [Edit("int", 222, "input", "output1", "attr_name", "int", 111), Delete("input", "output1", "attr_name", "int", 333)],
    ])
def test_flow_rule_serialise(flow_rule_items):
    rule = FlowRule(flow_rule_items)
    s = rule.dump()
    print(f"serialised: {s}")
    rule2 = parser.parse_flow_rule(s)
    assert rule2 == rule
