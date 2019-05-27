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

import unittest

from exp import parser
from exp.rule import Obligation, DataRuleContainer, Property, PropertyCapsule
from exp.activation import WhenImported


class TestDataRuleClass(unittest.TestCase):

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

    def test_property_capsule_clone(self):
        pc1 = self.pc1
        pc2 = self.pc1_2
        self.assertNotEqual(pc1, pc2)
        pc1_1 = pc1.clone()
        self.assertEqual(pc1, pc1_1)
        pc2_1 = pc2.clone()
        self.assertEqual(pc2, pc2_1)

    def test_property_capsule_merge(self):
        pc1 = self.pc1
        pc2 = self.pc1_2
        pc_m0 = self.pc_m
        pc_m, diff = PropertyCapsule.merge(pc1, pc2)
        self.assertEqual(pc_m, pc_m0)
        self.assertEqual(diff, [1, -1, 0])

    def test_obligation_clone(self):
        obs = self.ob1
        for i, ob1 in enumerate(obs):
            for j, ob2 in enumerate(obs):
                if i != j:
                    self.assertNotEqual(ob1, ob2)
        for ob in obs:
            ob_1 = ob.clone()
            self.assertEqual(ob, ob_1)

    def test_data_rule_container_clone(self):
        rule1 = self.rule1
        rule2 = self.rule2
        self.assertNotEqual(rule1, rule2)
        for r in (rule1, rule2):
            r_1 = r.clone()
            self.assertEqual(r, r_1)

    def test_data_rule_container_merge(self):
        rule1 = self.rule1
        rule2 = self.rule2
        rule_m = DataRuleContainer.merge(rule1, rule2)
        rule_m0 = self.rule_m
        self.assertEqual(rule_m, rule_m0)



class TestParser(unittest.TestCase):

    def test_empty_rule(self):
        s = '''rule TestRule begin
        end'''
        rule = DataRuleContainer([], {})
        self.assertEqual(parser.parse_data_rule(s), rule)

    def test_simple_obligations(self):
        s = '''rule TestRule begin
            obligation ob1 .
            obligation ob2 .
        end'''
        rule = DataRuleContainer([Obligation('ob1'), Obligation('ob2')], {})
        self.assertEqual(parser.parse_data_rule(s), rule)

    def test_obligation_with_property(self):
        s = '''rule TestRule begin
            obligation ob1 pr1 .
            property pr1 ddd .
        end'''
        pr1 = PropertyCapsule('pr1', 'ddd')
        pmap = {'pr1': pr1}
        obligations = [Obligation('ob1', ('pr1', 0))]
        rule = DataRuleContainer(obligations, pmap)
        self.assertEqual(parser.parse_data_rule(s), rule)

    def test_space_blank(self):
        s = '''
        rule TestRule  begin

            obligation ob1.

            obligation  ob2 pr1.

            property pr1  www  .

        end'''
        r1 = Obligation('ob1')
        r2 = Obligation('ob2', ('pr1', 0))
        pr = PropertyCapsule('pr1', 'www')
        rule = DataRuleContainer([r1, r2], {'pr1': pr})
        rule2 = parser.parse_data_rule(s)
        self.assertEqual(rule2, rule)

    def test_plural_property(self):
        s = '''rule TestRule begin
            obligation ob1 pr1[0] .
            obligation ob2 pr1[1] .
            property pr1 [1, 2] .
        end
        '''
        pr1 = PropertyCapsule('pr1', ['1', '2'])
        pmap = {'pr1': pr1}
        obligations = [Obligation('ob1', ('pr1', 0)), Obligation('ob2', ('pr1', 1))]
        rule = DataRuleContainer(obligations, pmap)
        rule2 = parser.parse_data_rule(s)
        self.assertEqual(rule2, rule)


class TestRuleSerialise(unittest.TestCase):

    def test_property_serialise(self):
        pr = PropertyCapsule("pr1")
        ps = (Property("a"), Property("b"))
        for p in ps:
            pr.add_property(p)
        s = pr.dump()
        name, content, remaining = parser.read_property(s)
        self.assertFalse(remaining.strip())
        pr2 = PropertyCapsule(name, content)
        self.assertEqual(pr, pr2)

    def test_data_rule_serialise(self):
        r = Obligation('ru1', ('a', 1))
        s = r.dump()
        name, property, activation_condition, remaining = parser.read_obligation(s)
        self.assertFalse(remaining.strip())
        r2 = Obligation(name, property)
        self.assertEqual(r2, r)

    def test_whole_data_rule_serialise(self):
        pr1 = PropertyCapsule('pr1', ['1', '2'])
        pmap = {'pr1': pr1}
        obligations = [Obligation('ob1', ('pr1', 0)), Obligation('ob2', ('pr1', 1))]
        rule = DataRuleContainer(obligations, pmap)
        s = rule.dump()
        rule2 = parser.parse_data_rule(s)
        self.assertEqual(rule2, rule)


if __name__ == '__main__':
    unittest.main()

