#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/09 17:26:15
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''


import copy
import logging
from typing import Dict, List, Optional
from random import randint

PortedRules = Dict[str, Optional['DataRuleContainer']]


class DataRule(object):
    '''
    DataRule is stateful
    '''

    # TODO: states

    @classmethod
    def merge(cls, first, *rest) -> 'DataRule':
        # TODO
        return first

    @classmethod
    def load(cls, data) -> Optional['DataRule']:
        return DataRule(data)

    def dump(self) -> str:
        return self.id

    def __init__(self, ID):
        self.id = ID

    def clone(self) -> 'DataRule':
        return DataRule(self.id)


class DataRuleContainer(object):

    logger = logging.getLogger('DataRuleContainer')

    @classmethod
    def merge(cls, first: 'DataRuleContainer', *rest: 'DataRuleContainer') -> 'DataRuleContainer':
        new = first.clone()
        for nxt in rest:
            for nr in nxt._rules.values():
                r = new.find_id(nr.id)
                if r:
                    new.replace(DataRule.merge(r, nr))
                else:
                    new.add(nr)
        return new

    @classmethod
    def load(cls, s: str) -> 'DataRuleContainer':
        rules: List[DataRule] = []
        for rs in s.split('\n'):
            r = DataRule.load(rs)
            if r:
                rules.append(r)
            else:
                cls.logger.error("can't parse DataRule: %s", rs)
        return DataRuleContainer(rules)

    def dump(self) -> str:
        return "\n".join([r.dump() for r in self._rules.values()])

    def __init__(self, rules):
        self._rules = {}
        assert isinstance(rules, list)
        for r in rules:
            self.add(r)

    def clone(self) -> 'DataRuleContainer':
        rules = [r.clone() for r in self._rules.values()]
        return DataRuleContainer(rules)

    def add(self, rule: DataRule) -> None:
        _id = rule.id
        assert _id not in self._rules
        self._rules[_id] = rule

    def find_id(self, ID) -> Optional[DataRule]:
        return self._rules.get(ID)

    def replace(self, new_rule: DataRule) -> None:
        _id = new_rule.id
        assert _id in self._rules
        self._rules[_id] = new_rule


def TestRule() -> DataRuleContainer:
    return DataRuleContainer.load('TestRule')

def RandomRule() -> DataRuleContainer:
    return DataRuleContainer.load("TestRule{}".format(randint(0, 20)))


class FlowRule(object):
    '''
    FlowRule is stateless
    '''

    # TODO: def __init__(self, connectivity, input_ports, output_ports):
    def __init__(self, connectivity):
        self._conn = connectivity


class FlowRuleHandler(object):

    def __init__(self, flow_rule: FlowRule):
        self._rule = flow_rule

    def dispatch(self, rules: Dict[str, DataRuleContainer]) -> PortedRules:
        outs: 'PortedRules' = {}
        for op in self._rule._conn:
            rules_to_merge = [rules[ip] for ip in self._rule._conn[op] if ip in rules]
            if rules_to_merge:
                outs[op] = DataRuleContainer.merge(*rules_to_merge)
            else:
                outs[op] = None
        return outs


def DefaultFlow(input_ports: List[str], output_ports: List[str]) -> FlowRule:
    connectivity = {}
    for output_port in output_ports:
        connectivity[output_port] = copy.copy(input_ports)
    return FlowRule(connectivity)

