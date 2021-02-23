#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/05/09 15:38:09
#   License :   Apache 2.0 (See LICENSE)
#

'''
This file contains the parser of the rules (both data rules and flow rules) -- from human-friendly string representation to binary formats / objects.
The serialiser is defined in the classes.
'''

from dataclasses import dataclass
import json
from lark import Lark, Transformer
import re
from typing import Dict, List, Optional, Tuple, Union

from .rule import FlowRule, ObligationDeclaration, DataRuleContainer, AttributeCapsule
from .proto import ActivationCondition, is_ac, obtain


class MalformedRuleException(Exception):
    pass


DATA_RULE_SYNTAX = r'''
data_rule : "begin" data_rule_stmt* "end"
data_rule_stmt : obligation_decl
                   | attribute_decl
obligation_decl : "obligation" "(" obligated_action "," validity_binding "," activation_condition ")" "."
attribute_decl : "attribute" "(" attribute_name "," attribute_value_field ")" "."
obligated_action : action_ref action_spec
validity_binding : "[" attribute_reference ( "," attribute_reference )* "]" | "["  "]"
activation_condition : activation_condition_ref
attribute_name : identifier
attribute_value_field : attribute_value_expr
                          | "[" attribute_value_expr ("," attribute_value_expr)* "]"
action_ref : external_identifier
action_spec : attribute_reference*
attribute_reference : attribute_name [ "[" INT "]" ]
activation_condition_ref : external_identifier | "null"
identifier : CNAME
attribute_value_expr : attribute_type attribute_value
external_identifier : identifier | STRING
attribute_type : external_identifier
attribute_value : value
value : INT | NUMBER | STRING

%import common.ESCAPED_STRING   -> STRING
%import common.CNAME            -> CNAME
%import common.INT              -> INT
%import common.SIGNED_NUMBER    -> NUMBER
%import common.WS
%ignore WS
'''


class TreeToDataRuleContent(Transformer):
    def data_rule(self, stmts):
        obs = []
        attrs = []
        for stmt in stmts:
            if stmt[0] == 1:
                obs.append(stmt[1])
            elif stmt[0] == 2:
                attrs.append(stmt[1])
        return obs, attrs
    def data_rule_stmt(self, stmt):
        (stmt,) = stmt
        return stmt
    def obligation_decl(self, items):
        return (1, items)
    def attribute_decl(self, items):
        return (2, items)
    
    def obligated_action(self, items):
        action = items[0]
        if len(items) > 1:
            attrs = items[1]
        else:
            attrs = []
        return (action, attrs)
    def validity_binding(self, items):
        return list(items)
    def activation_condition(self, items):
        (item,) = items
        return item

    def attribute_name(self, items):
        return items[0]
    def attribute_value_field(self, items):
        return items
    def attribute_value_expr(self, items):
        return tuple(items)
    def attribute_type(self, items):
        return items[0]
    def attribute_value(self, items):
        return items[0]
    
    def action_ref(self, ref):
        (ref,) = ref
        return ref
    def action_spec(self, items):
        return list(items)
    def attribute_reference(self, items):
        attr_name = items[0]
        if len(items) == 1:
            attr_index = 0
        else:
            attr_index = items[1]
        return (attr_name, attr_index)
    def activation_condition_ref(self, ref):
        if not ref:
            return None
        else:
            (ref,) = ref
            return ref
    
    def identifier(self, s):
        (s,) = s
        return s
    def external_identifier(self, s):
        (s,) = s
        return s
    def value(self, value):
        (value,) = value
        return value
    
    def CNAME(self, s):
        return s[:]
    def STRING(self, s):
        return json.loads(s)
    def NUMBER(self, n):
        return float(n)
    def INT(self, n):
        return int(n)


def call_parser_data_rule(rule: str, part: str = 'data_rule'):
    data_rule_parser = Lark(DATA_RULE_SYNTAX, start=part)
    tree = data_rule_parser.parse(rule)
    return TreeToDataRuleContent().transform(tree)


def parse_data_rule(data_rule: str) -> Optional[DataRuleContainer]:
    obs, attrs = call_parser_data_rule(data_rule, part='data_rule')

    obligations = []
    attribute_capsules = []

    for attr in attrs:
        name, attribute_data = attr
        attribute_capsules.append(AttributeCapsule.from_raw(name, attribute_data))

    for pack in obs:
        ob = ObligationDeclaration.from_raw(*pack)
        obligations.append(ob)

    return DataRuleContainer(obligations, attribute_capsules)


Propagate = FlowRule.Propagate
Edit = FlowRule.Edit
Delete = FlowRule.Delete

def parse_flow_rule(flow_rule: Optional[str]) -> Optional[FlowRule]:
    if flow_rule is None:
        return None
    try:
        connectivity = eval(flow_rule)
    except Exception as e:
        raise MalformedRuleException(e)
    return FlowRule(connectivity)

