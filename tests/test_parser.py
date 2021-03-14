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

from draid import parser
from draid.rule import ObligationDeclaration, DataRuleContainer, AttributeCapsule, FlowRule, Propagate, Edit, Delete


@pytest.mark.parametrize('s, attrcap', [
    ('''attribute(pr1, ["str" "a", "str" "b"]).''', AttributeCapsule.from_raw('pr1', [('str', 'a'), ('str', 'b')]))
    ])
def test_attribute_capsule_parse(s, attrcap):
    _, (name, value) = parser.call_parser_data_rule(s, 'attribute_decl')
    attrcap1 = AttributeCapsule.from_raw(name, value)
    assert attrcap == attrcap1

@pytest.mark.parametrize('s, rule', [
    ('''begin
end''', DataRuleContainer([], []))
    ])
def test_empty_rule(s, rule):
    assert parser.parse_data_rule(s) == rule


@pytest.mark.parametrize('s, rule', [
    ('''begin
        obligation(ob1, [], null).
        obligation(ob2, [], null).
    end''', DataRuleContainer([ObligationDeclaration('ob1'), ObligationDeclaration('ob2')], []))
    ])
def test_simple_obligations(s, rule):
    assert parser.parse_data_rule(s) == rule


@pytest.mark.parametrize('s, obligations, amap', [
    ('''begin
        obligation(ob1, [pr1], null).
        attribute(pr1, "str" "ddd").
    end''', [ObligationDeclaration('ob1', [('pr1', 0)])], [AttributeCapsule.from_raw('pr1', [('str', 'ddd')])]),

    ('''
    begin

        obligation (ob1, [], null).

        obligation ( ob2, [pr1], null).

        attribute (pr1, "str" "www")  .

    end''', [ObligationDeclaration('ob1'), ObligationDeclaration('ob2', [('pr1', 0)])], [AttributeCapsule.from_raw('pr1', [('str', 'www')])]),

    ('''begin
        obligation (ob1, [pr1[0]], null) .
        obligation (ob2, [pr1[1]], null) .
        attribute (pr1, ["str" 1, "str" 2]) .
    end
    ''', [ObligationDeclaration('ob1', [('pr1', 0)]), ObligationDeclaration('ob2', [('pr1', 1)])], [AttributeCapsule.from_raw('pr1', [('str', 1), ('str', 2)])]),
    ])
def test_obligation_with_attribute(s, obligations, amap):
    rule = DataRuleContainer(obligations, amap)
    assert parser.parse_data_rule(s) == rule


@pytest.mark.parametrize('s, flow_rule_items', [
    ('''
    "input1" -> "output1", "output2"
    "input2" -> "output2"
    edit("input1", "output1", dummy, "str", "111", "str", "222")
    delete("input2", *, dummy2, *, *)
    ''', [Propagate("input1", ["output1", "output2"]), Propagate("input2", ["output2"]), Edit("str", "222", "input1", "output1", "dummy", "str", "111"), Delete("input2", None, "dummy2", None, None)]),
    ('''
    "input1" -> "output1", "output2"
    "input2" -> "output2"
    edit("input1", "output1", dummy, "int", 111, "int", 222)
    delete("input2", *, dummy2, *, *)
    ''', [Propagate("input1", ["output1", "output2"]), Propagate("input2", ["output2"]), Edit("int", 222, "input1", "output1", "dummy", "int", 111), Delete("input2", None, "dummy2", None, None)]),

    ])
def test_flow_rule(s, flow_rule_items):
    rule = FlowRule(flow_rule_items)
    assert parser.parse_flow_rule(s) == rule
