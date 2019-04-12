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

from augmentation import PortedRules


class _DataRule(object):
    '''
    DataRule is stateful
    '''

    # TODO: states

    @classmethod
    def merge(cls, first, *rest) -> '_DataRule':
        # TODO
        return first

    @classmethod
    def load(cls, data) -> Optional['_DataRule']:
        return _DataRule(data)

    def dump(self) -> str:
        return self.id

    def __init__(self, ID):
        self.id = ID

    def clone(self) -> '_DataRule':
        return _DataRule(self.id)


class DataRuleWrapper(object):

    logger = logging.getLogger('DataRuleWrapper')

    @classmethod
    def merge(cls, first, *rest) -> 'DataRuleWrapper':
        new = first.clone()
        for nxt in rest:
            for nr in nxt._rules.values():
                r = new.find_id(nr.id)
                if r:
                    new.replace(_DataRule.merge(r, nr))
                else:
                    new.add(r)
            #else:
            #    cls.logger.warning('rules have different data. Ignoring for now')
        return new

    @classmethod
    def load(cls, s: str) -> 'DataRuleWrapper':
        rules: List[_DataRule] = []
        for rs in s.split('\n'):
            r = _DataRule.load(rs)
            if r:
                rules.append(r)
            else:
                cls.logger.error("can't parse DataRule: %s", rs)
        return DataRuleWrapper(rules)

    def dump(self) -> str:
        return "\n".join([r.dump() for r in self._rules.values()])

    def __init__(self, rules):
        self._rules = {}
        assert isinstance(rules, list)
        for r in rules:
            self.add(r)

    def clone(self) -> 'DataRuleWrapper':
        rules = [r.clone() for r in self._rules.values()]
        return DataRuleWrapper(rules)

    def add(self, rule: _DataRule) -> None:
        _id = rule.id
        assert _id not in self._rules
        self._rules[_id] = rule

    def find_id(self, ID) -> Optional[_DataRule]:
        return self._rules.get(ID)

    def replace(self, new_rule: _DataRule) -> None:
        _id = new_rule.id
        assert _id in self._rules
        self._rules[_id] = new_rule


def TestRule() -> DataRuleWrapper:
    return DataRuleWrapper.load('TestRule')


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

    def dispatch(self, rules: Dict[str, DataRuleWrapper]) -> PortedRules:
        outs = {}
        for op in self._rule._conn:
            rules_to_merge = [rules[ip] for ip in self._rule._conn[op] if ip in rules]
            if rules_to_merge:
                outs[op] = DataRuleWrapper.merge(*rules_to_merge)
            else:
                outs[op] = None
        return outs


def DefaultFlow(input_ports: List[str], output_ports: List[str]) -> FlowRule:
    connectivity = {}
    for output_port in output_ports:
        connectivity[output_port] = copy.copy(input_ports)
    return FlowRule(connectivity)

