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

from exp.rule import Obligation, DataRuleContainer, PropertyCapsule
from exp.proto import WhenImported


pc1 = PropertyCapsule('pr1', 'a')
pc1_2 = PropertyCapsule('pr1', ['b', 'a', 'c'])
pc_m = PropertyCapsule('pr1', ['a', 'b', 'c'])

pc2 = PropertyCapsule('pr2', ['A', 'B', 'C'])

ob1 = (
        Obligation('ob1'),
        Obligation('ob1', ('pr1', 0)),
        Obligation('ob1', ('pr1', 0), WhenImported()),
        )
ob2 = Obligation('ob2', ('pr2', 0))
ob3 = Obligation('ob2', ('pr2', 1))

rule1 = DataRuleContainer([ob1[0], ob1[1], ob2], {'pr1': pc1, 'pr2': pc2})
rule2 = DataRuleContainer([ob1[0], ob1[1], ob2, ob3], {'pr1': pc1, 'pr2': pc2})
rule_m = DataRuleContainer([ob1[0], ob1[1], ob2, ob3], {'pr1': pc1, 'pr2': pc2})


@pytest.mark.parametrize('pc', [
    pc1,
    pc1_2
    ])
def test_property_capsule_clone(pc):
    pc_clone = pc.clone()
    assert pc_clone == pc


@pytest.mark.parametrize('pc1, pc2, pc_m, diff', [
    (pc1, pc1_2, pc_m, [1, -1, 0])
    ])
def test_property_capsule_merge(pc1, pc2, pc_m, diff):
    pc_merged, diff1 = PropertyCapsule.merge(pc1, pc2)
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

