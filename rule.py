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
from typing import Dict, List, Optional, Tuple, Union
from random import randint

PortedRules = Dict[str, Optional['DataRuleContainer']]


class Property(object):
    '''
    '''

    def __init__(self, value):
        self._v = value

    def value(self):
        return self._v

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self._v != other._v:
                return False
            return True
        else:
            return NotImplemented


class PropertyCapsule:

    @staticmethod
    def merge(first: 'PropertyCapsule', second: 'PropertyCapsule') -> Tuple['PropertyCapsule', List[int]]:
        assert first._name == second._name
        new = first.clone()
        diff = []
        for i, pr in enumerate(second._prs):
            try:
                index = new._prs.index(pr)
            except ValueError:
                index = len(new._prs)
                new._prs.append(pr)
            diff.append(index - i)
        return new, diff

    def __init__(self, name: str, property: Optional[Union[str, List[str]]] = None):
        self._name = name
        self._prs: List[Property] = []
        if property:
            if isinstance(property, str):
                self._prs.append(Property(property))
            else:
                self._prs.extend([Property(pr) for pr in property])

    def clone(self) -> 'PropertyCapsule':
        new = PropertyCapsule(self._name)
        for pr in self._prs:
            new.add_property(pr)
        return new

    def add_property(self, pr: Property):
        self._prs.append(pr)

    def dump(self) -> str:
        s = "property {}".format(self._name)
        ss = " {}".format(self._prs[0].value())
        if len(self._prs) >= 1:
            for pr in self._prs[1:]:
                ss += ", {}".format(pr._v)
        return "{} [{}] .".format(s, ss)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self._name != other._name:
                return False
            if self._prs != other._prs:
                return False
            return True
        else:
            return NotImplemented


class DataRule(object):
    '''
    DataRule is not stateful itself, but activated data rules are.
    There is no grouping of data rules, so it makes no sense to "merge" two data rules: two data rules that are exactly the same should have one removed. However, it makes sense to merge two activated data rules.
    '''

    # TODO: activated data rules

    def dump(self) -> str:
        s = "obligation {}".format(self._name)
        if self._property:
            s = "{} {}[{}]".format(s, self._property[0], self._property[1])
        s += " ."
        return s

    def __init__(self, name: str, property: Optional[Tuple[str, int]] = None):
        self._name = name
        self._property = property

    def clone(self, dmap={}) -> 'DataRule':
        if self._property:
            index = self._property[1]
            if dmap and self._property[0] in dmap:
                index += dmap[self._property[0]]
            new_property = (self._property[0], index)
            return DataRule(self._name, new_property)
        return DataRule(self._name)

    def name(self):
        return self._name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self._name != other._name:
                return False
            if self._property != other._property:
                return False
            return True
        else:
            return NotImplemented


class DataRuleContainer(object):

    @classmethod
    def merge(cls, first: 'DataRuleContainer', *rest: 'DataRuleContainer') -> 'DataRuleContainer':
        new = first.clone()
        for nxt in rest:
            dmap = {}
            for pname, pr in nxt._pmap.items():
                if pname in new._pmap:
                    pr, diff = PropertyCapsule.merge(new._pmap[pname], pr)
                else:
                    diff = None  # type: ignore
                new._pmap[pname] = pr
                if diff is not None:
                    dmap[pname] = diff
            for r in nxt._rules:
                if r in new._rules:
                    continue
                r = r.clone(dmap)
                new._rules.append(r)
        return new

    def dump(self) -> str:
        skeleton = """rule {} begin
        {}
        end
        """
        name = ''
        s_ob = "\n".join([r.dump() for r in self._rules])
        s_pr = "\n".join([pr.dump() for pr in self._pmap.values()])
        s = s_ob
        if s_pr:
            s += '\n' + s_pr
        return skeleton.format(name, s)

    def __init__(self, rules: List[DataRule], property_map: Dict[str, PropertyCapsule]):
        self._rules: List[DataRule] = [r for r in rules]
        self._pmap = property_map

    def clone(self) -> 'DataRuleContainer':
        pmap: Dict[str, PropertyCapsule] = copy.deepcopy(self._pmap)
        rules = [r.clone() for r in self._rules]
        return DataRuleContainer(rules, pmap)

    def __eq__(self, other):
        # TODO: order independent
        if isinstance(other, self.__class__):
            if not self._rules == other._rules:
                return False
            if not self._pmap == other._pmap:
                return False
            return True
        else:
            return NotImplemented


def RandomRule(must=False) -> str:
    return random_rule(str(randint(0, 20)), must)


def random_rule(suffix='', must=False) -> str:
    if must:
        rint = randint(1, 2)
    else:
        rint = randint(0, 2)
    if not rint:
        return ""
    else:
        if rint == 1:
            return rule_acknowledge(suffix)
        else:
            return rule_account(suffix)


def rule_acknowledge(source: str, suffix='') -> str:
    return f'''
    rule Rule0
        obligation Acknowledge{suffix} source_name .
        property source_name {source} .
    end
    '''


def rule_account(suffix='') -> str:
    return f'''
    rule Rule1
        obligation Account{suffix} .
    end
    '''


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
            rules_to_merge = [rules[ip]
                              for ip in self._rule._conn[op] if ip in rules]
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
