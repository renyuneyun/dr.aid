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


@pytest.mark.parametrize('s, attrcap', [
    ('''attribute pr1 [a, b].''', AttributeCapsule('pr1', ['a', 'b']))
    ])
def test_attribute_capsule_parse(s, attrcap):
    name, attribute_data, line = parser.read_attribute(s)
    attrcap1 = AttributeCapsule(name, attribute_data)
    assert attrcap == attrcap1
    assert not line

@pytest.mark.parametrize('s, rule', [
    ('''rule TestRule begin
end''', DataRuleContainer([], []))
    ])
def test_empty_rule(s, rule):
    assert parser.parse_data_rule(s) == rule


@pytest.mark.parametrize('s, rule', [
    ('''rule TestRule begin
        obligation ob1 .
        obligation ob2 .
    end''', DataRuleContainer([ObligationDeclaration('ob1'), ObligationDeclaration('ob2')], []))
    ])
def test_simple_obligations(s, rule):
    assert parser.parse_data_rule(s) == rule


@pytest.mark.parametrize('s, obligations, amap', [
    ('''rule TestRule begin
        obligation ob1 pr1 .
        attribute pr1 ddd .
    end''', [ObligationDeclaration('ob1', ('pr1', 0))], [AttributeCapsule('pr1', 'ddd')]),

    ('''
    rule TestRule  begin

        obligation ob1.

        obligation  ob2 pr1.

        attribute pr1  www  .

    end''', [ObligationDeclaration('ob1'), ObligationDeclaration('ob2', ('pr1', 0))], [AttributeCapsule('pr1', 'www')]),

    ('''rule TestRule begin
        obligation ob1 pr1[0] .
        obligation ob2 pr1[1] .
        attribute pr1 [1, 2] .
    end
    ''', [ObligationDeclaration('ob1', ('pr1', 0)), ObligationDeclaration('ob2', ('pr1', 1))], [AttributeCapsule('pr1', ['1', '2'])]),
    ])
def test_obligation_with_attribute(s, obligations, amap):
    rule = DataRuleContainer(obligations, amap)
    assert parser.parse_data_rule(s) == rule

