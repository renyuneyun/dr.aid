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

from draid.rule import ObligationDeclaration, DataRuleContainer, AttributeCapsule
from draid.rule import EqualAC


WhenImported = EqualAC('stage', 'import')


pc1 = AttributeCapsule.from_raw('pr1', [('str', 'a')])
pc1_2 = AttributeCapsule.from_raw('pr1', [('str', 'b'), ('str', 'a'), ('str', 'c')])
pc_m = AttributeCapsule.from_raw('pr1', [('str', 'a'), ('str', 'b'), ('str', 'c')])

pc2 = AttributeCapsule.from_raw('pr2', [('str', 'A'), ('str', 'B'), ('str', 'C')])

ob1 = (
        ObligationDeclaration('ob1'),
        ObligationDeclaration('ob1', [('pr1', 0)]),
        ObligationDeclaration('ob1', [('pr1', 0)], WhenImported),
        )
ob2 = ObligationDeclaration('ob2', [('pr2', 0)])
ob3 = ObligationDeclaration('ob2', [('pr2', 1)])

rule1 = DataRuleContainer([ob1[0], ob1[1], ob2], [pc1, pc2])
rule2 = DataRuleContainer([ob1[0], ob1[1], ob2, ob3], [pc1, pc2])
rule_m = DataRuleContainer([ob1[0], ob1[1], ob2, ob3], [pc1, pc2])


@pytest.mark.parametrize('pc', [
    pc1,
    pc1_2
    ])
def test_attribute_capsule_clone(pc):
    pc_clone = pc.clone()
    assert pc_clone == pc


@pytest.mark.parametrize('pc1, pc2, pc_m, diff', [
    (pc1, pc1_2, pc_m, [1, -1, 0])
    ])
def test_attribute_capsule_merge(pc1, pc2, pc_m, diff):
    pc_merged, diff1 = AttributeCapsule.merge(pc1, pc2)
    assert pc_merged == pc_m
    assert tuple(diff1) == tuple(diff)


@pytest.mark.parametrize('ob', ob1)
def test_obligation_clone(ob):
    ob_cloned = ob.clone()
    assert ob == ob_cloned


@pytest.mark.parametrize('rule', [
    rule1,
    rule2
    ])
def test_data_rule_container_clone(rule):
    rule_cloned = rule.clone()
    assert rule_cloned == rule


@pytest.mark.parametrize('rule1, rule2, rule_m', [
    (rule1, rule2, rule_m)
    ])
def test_data_rule_container_merge(rule1, rule2, rule_m):
    rule_merged = DataRuleContainer.merge(rule1, rule2)
    assert rule_m == rule_merged

