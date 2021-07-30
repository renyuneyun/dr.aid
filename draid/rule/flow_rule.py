#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/05/25 18:08:48
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from draid.defs.exception import IllegalCaseError

from .utils import escaped


class Action:
    def mapped(self, name_map): pass


@dataclass
class Propagate(Action):
    input_port: str
    output_ports: List[str]

    def mapped(self, name_map):
        input_port = FlowRule.map_name(name_map, self.input_port)
        output_ports = [FlowRule.map_name(name_map, port) for port in self.output_ports]
        return Propagate(input_port, output_ports)

@dataclass
class Edit(Action):
    new_type: str
    new_value: str
    input_port: Optional[str] = None
    output_port: Optional[str] = None
    name: Optional[str] = None
    match_type: Optional[str] = None
    match_value: Optional[Union[str, int, float]] = None

    def mapped(self, name_map):
        input_port = FlowRule.map_name(name_map, self.input_port)
        output_port = FlowRule.map_name(name_map, self.output_port)
        return Edit(self.new_type, self.new_value, input_port, output_port, self.name, self.match_type, self.match_value)

@dataclass
class Delete(Action):
    input_port: Optional[str] = None
    output_port: Optional[str] = None
    name: Optional[str] = None
    match_type: Optional[str] = None
    match_value: Optional[Union[str, int, float]] = None

    def mapped(self, name_map):
        input_port = FlowRule.map_name(name_map, self.input_port)
        output_port = FlowRule.map_name(name_map, self.output_port)
        return Delete(input_port, output_port, self.name, self.match_type, self.match_value)


class FlowRule:
    '''
    FlowRule is stateless
    '''

    @staticmethod
    def map_name(name_map, name):
        return name_map[name] if name in name_map else name

    def __init__(self, actions: List[Action]):
        self.actions = actions
        self.name_map = None  # type: Optional[Dict[str, str]]

    def set_name_map(self, name_map: Dict[str, str]):
        self.name_map = name_map

    def mapped_actions(self) -> List[Action]:
        '''
        Returns the actions with name mapped.
        '''
        if not self.name_map:
            return self.actions
        else:
            return [action.mapped(self.name_map) for action in self.actions]

    def dump(self) -> str:
        def optional(s):
            return s or '*'
        s = ''
        for action in self.actions:
            if isinstance(action, Propagate):
                s += f"{action.input_port} -> {', '.join(action.output_ports)}\n"
            elif isinstance(action, Edit):
                s += f"edit({optional(escaped(action.input_port))}, {optional(escaped(action.output_port))}, {optional(action.name)}, {optional(escaped(action.match_type))}, {optional(escaped(action.match_value))}, {escaped(action.new_type)}, {escaped(action.new_value)})\n"
            elif isinstance(action, Delete):
                s += f"delete({optional(escaped(action.input_port))}, {optional(escaped(action.output_port))}, {optional(action.name)}, {optional(escaped(action.match_type))}, {optional(escaped(action.match_value))})\n"
            else:
                raise IllegalCaseError()
        return s

    def __iter__(self):
        return self.mapped_actions().__iter__()

    def __eq__(self, other):
        # TODO: order independent
        if isinstance(other, self.__class__):
            if not self.actions == other.actions:
                return False
            if not self.name_map == other.name_map:
                return False
            return True
        else:
            return NotImplemented


def DefaultFlow(input_ports: List[str], output_ports: List[str]) -> FlowRule:
    actions = []  # type: List[Action]
    for input_port in input_ports:
        pr = Propagate(input_port, output_ports)
        actions.append(pr)
    return FlowRule(actions)
