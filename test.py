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
from exp.rule import DataRule, DataRuleContainer, Property, PropertyCapsule


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
        rule = DataRuleContainer([DataRule('ob1'), DataRule('ob2')], {})
        self.assertEqual(parser.parse_data_rule(s), rule)

    def test_obligation_with_property(self):
        s = '''rule TestRule begin
            obligation ob1 pr1 .
            property pr1 ddd .
        end'''
        pr1 = PropertyCapsule('pr1', 'ddd')
        pmap = {'pr1': pr1}
        obligations = [DataRule('ob1', ('pr1', 0))]
        rule = DataRuleContainer(obligations, pmap)
        self.assertEqual(parser.parse_data_rule(s), rule)

    def test_space_blank(self):
        s = '''
        rule TestRule  begin

            obligation ob1.

            obligation  ob2 pr1.

            property pr1  www  .

        end'''
        r1 = DataRule('ob1')
        r2 = DataRule('ob2', ('pr1', 0))
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
        obligations = [DataRule('ob1', ('pr1', 0)), DataRule('ob2', ('pr1', 1))]
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
        name, content = parser.read_property(s)
        pr2 = PropertyCapsule(name, content)
        self.assertEqual(pr, pr2)

    def test_data_rule_serialise(self):
        r = DataRule('ru1', ('a', 1))
        s = r.dump()
        name, property = parser.read_obligation(s)
        r2 = DataRule(name, property)
        self.assertEqual(r2, r)

    def test_whole_data_rule_serialise(self):
        pr1 = PropertyCapsule('pr1', ['1', '2'])
        pmap = {'pr1': pr1}
        obligations = [DataRule('ob1', ('pr1', 0)), DataRule('ob2', ('pr1', 1))]
        rule = DataRuleContainer(obligations, pmap)
        s = rule.dump()
        rule2 = parser.parse_data_rule(s)
        self.assertEqual(rule2, rule)


if __name__ == '__main__':
    unittest.main()

