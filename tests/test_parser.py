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


@pytest.mark.parametrize('s, obligations, pmap', [
    ('''rule TestRule begin
        obligation ob1 pr1 .
        property pr1 ddd .
    end''', [Obligation('ob1', ('pr1', 0))], {'pr1': PropertyCapsule('pr1', 'ddd')}),

    ('''
    rule TestRule  begin

        obligation ob1.

        obligation  ob2 pr1.

        property pr1  www  .

    end''', [Obligation('ob1'), Obligation('ob2', ('pr1', 0))], {'pr1': PropertyCapsule('pr1', 'www')}),

    ('''rule TestRule begin
        obligation ob1 pr1[0] .
        obligation ob2 pr1[1] .
        property pr1 [1, 2] .
    end
    ''', [Obligation('ob1', ('pr1', 0)), Obligation('ob2', ('pr1', 1))], {'pr1': PropertyCapsule('pr1', ['1', '2'])}),
    ])
def test_obligation_with_property(s, obligations, pmap):
    rule = DataRuleContainer(obligations, pmap)
    assert parser.parse_data_rule(s) == rule

