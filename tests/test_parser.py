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
from exp.rule import Obligation, DataRuleContainer, Attribute


@pytest.mark.parametrize('s, rule', [
    ('''rule TestRule begin
end''', DataRuleContainer([], {}))
    ])
def test_empty_rule(s, rule):
    assert parser.parse_data_rule(s) == rule


@pytest.mark.parametrize('s, rule', [
    ('''rule TestRule begin
        obligation ob1 .
        obligation ob2 .
    end''', DataRuleContainer([Obligation('ob1'), Obligation('ob2')], {}))
    ])
def test_simple_obligations(s, rule):
    assert parser.parse_data_rule(s) == rule


@pytest.mark.parametrize('s, obligations, amap', [
    ('''rule TestRule begin
        obligation ob1 pr1 .
        attribute pr1 ddd .
    end''', [Obligation('ob1', ('pr1', 0))], {'pr1': Attribute.instantiate('pr1', 'ddd')}),

    ('''
    rule TestRule  begin

        obligation ob1.

        obligation  ob2 pr1.

        attribute pr1  www  .

    end''', [Obligation('ob1'), Obligation('ob2', ('pr1', 0))], {'pr1': Attribute.instantiate('pr1', 'www')}),

    ('''rule TestRule begin
        obligation ob1 pr1[0] .
        obligation ob2 pr1[1] .
        attribute pr1 [1, 2] .
    end
    ''', [Obligation('ob1', ('pr1', 0)), Obligation('ob2', ('pr1', 1))], {'pr1': Attribute.instantiate('pr1', ['1', '2'])}),
    ])
def test_obligation_with_attribute(s, obligations, amap):
    rule = DataRuleContainer(obligations, amap)
    assert parser.parse_data_rule(s) == rule

