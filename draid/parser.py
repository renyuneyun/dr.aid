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
from functools import partial
import json
from lark import Lark, Transformer
import re
from typing import Dict, List, Optional, Union, Tuple, Type

from .rule import FlowRule, Propagate, Edit, Delete, ObligationDeclaration, DataRuleContainer, AttributeCapsule
from .proto import ActivationCondition, is_ac, obtain


class MalformedRuleException(Exception):
    pass


DATA_RULE_GRAMMAR = r'''
data_rule : "begin" data_rule_stmt* "end"
data_rule_stmt : obligation_decl
                   | attribute_decl
obligation_decl : "obligation" "(" obligated_action "," validity_binding "," activation_condition ")" "."
attribute_decl : "attribute" "(" attribute_name "," attribute_value_field ")" "."
obligated_action : action_ref action_spec
validity_binding : "[" attribute_reference ( "," attribute_reference )* "]" | "["  "]"
activation_condition : activation_condition_expr | NULL
attribute_name : identifier
attribute_value_field : attribute_value_expr
                          | "[" attribute_value_expr ("," attribute_value_expr)* "]"
action_ref : external_identifier
action_spec : attribute_reference*
attribute_reference : attribute_name [ "[" INT "]" ]
activation_condition_expr : AC_TARGET OPERATOR ac_value
identifier : CNAME
attribute_value_expr : attribute_type attribute_value
NULL : "null"
external_identifier : identifier | STRING
AC_TARGET : "action" | "stage" | "user" | "date" | "processId" | "purpose"
OPERATOR : "=" | "!="
ac_value : value | ANY
attribute_type : external_identifier
attribute_value : value
value : INT | NUMBER | STRING
ANY : "*"

%import common.ESCAPED_STRING   -> STRING
%import common.CNAME            -> CNAME
%import common.INT              -> INT
%import common.SIGNED_NUMBER    -> NUMBER
%import common.WS
%ignore WS
'''


FLOW_RULE_GRAMMAR = r'''
flow_rule : flow_rule_stmt*
flow_rule_stmt : propagate_stmt
                 | edit_stmt
                 | delete_stmt
propagate_stmt : input_port "->" output_port ([","] output_port)*
edit_stmt : "edit" "(" port_matcher "," attr_matcher "," attr_data_new ")"
delete_stmt : "delete" "(" port_matcher "," attr_matcher ")"
input_port : port
output_port : port
port_matcher : input_port_may "," output_port_may
attr_matcher : attr_name_may "," attr_type_may "," attr_value_may
attr_data_new : attr_type "," attr_value
port : identifier | STRING
input_port_may : input_port | SYM_ANY
output_port_may : output_port | SYM_ANY
attr_name_may : attr_name | SYM_ANY
attr_type_may : attr_type | SYM_ANY
attr_value_may : attr_value | SYM_ANY
attr_type : STRING
attr_value : value
identifier : CNAME
attr_name : identifier
value : INT | NUMBER | STRING

SYM_ANY : "*"

%import common.ESCAPED_STRING   -> STRING
%import common.CNAME            -> CNAME
%import common.INT              -> INT
%import common.SIGNED_NUMBER    -> NUMBER
%import common.WS
%ignore WS
'''


class TreeToDataRuleContent(Transformer):
    def _only(self, item):
        (item,) = item
        return item

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
        if item == "null":
            return None
        return item
    def activation_condition_expr(self, items):
        ac_target, operator, ac_value = items
        return (operator, (ac_target, ac_value))
    def AC_TARGET(self, s):
        return str(s)
    def OPERATOR(self, s):
        return str(s)
    ac_value = _only
    def ANY(self, s):
        return None

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
        return s[1:-1]
    def NUMBER(self, n):
        return float(n)
    def INT(self, n):
        return int(n)


class TreeToFlowRuleContent(Transformer):
    def _only(self, item):
        (item,) = item
        return item
    def _multi(self, items):
        return tuple(items)
    
    def flow_rule(self, stmts):
        return list(stmts)
    
    flow_rule_stmt = _only
    
    def propagate_stmt(self, items):
        input_port, output_ports = items[0], items[1:]
        return (1, (input_port, output_ports))
    
    def edit_stmt(self, items):
        flatterned_items = [i for lst in items for i in lst]
        return (2, flatterned_items)
    
    def delete_stmt(self, items):
        flatterned_items = [i for lst in items for i in lst]
        return (3, flatterned_items)
    
    port_matcher = _multi
    input_port_may = _only
    output_port_may = _only
    
    input_port = _only
    output_port = _only
    port = _only
    
    attr_matcher = _multi
    attr_data_new = _multi
    
    attr_name_may = _only
    attr_type_may = _only
    attr_value_may = _only
    attr_name = _only
    attr_type = _only
    attr_value = _only
    
    identifier = _only
    value = _only

    def SYM_ANY(self, s):
        return None

    def CNAME(self, s):
        return s[:]
    def STRING(self, s):
        return s[1:-1]
    def NUMBER(self, n):
        return float(n)
    def INT(self, n):
        return int(n)


class TreeToFlowRuleObject(TreeToFlowRuleContent):
    
    def flow_rule(self, stmts):
        return FlowRule(list(stmts))
    
    def propagate_stmt(self, items):
        input_port, output_ports = items[0], items[1:]
        return Propagate(input_port, output_ports)
    
    def edit_stmt(self, items):
        input_port, output_port, name, type_old, value_old, type_new, value_new = [i for lst in items for i in lst]
        return Edit(type_new, value_new, input_port, output_port, name, type_old, value_old)
    
    def delete_stmt(self, items):
        input_port, output_port, name, type, value = [i for lst in items for i in lst]
        return Delete(input_port, output_port, name, type, value)


def make_parser_call_template(grammar: str, transformer: Type[Transformer]):
    def call_parser(rule: str, part: str):
        data_rule_parser = Lark(grammar, start=part)
        tree = data_rule_parser.parse(rule)
        return transformer().transform(tree)
    return call_parser


def call_parser_data_rule(rule: str, part: str = 'data_rule'):
    return make_parser_call_template(DATA_RULE_GRAMMAR, TreeToDataRuleContent)(rule, part)


def call_parser_flow_rule(rule: str, part: str = 'flow_rule'):
    return make_parser_call_template(FLOW_RULE_GRAMMAR, TreeToFlowRuleContent)(rule, part)


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


def parse_flow_rule(flow_rule: Optional[str]) -> Optional[FlowRule]:
    if flow_rule is None:
        return None
    return make_parser_call_template(FLOW_RULE_GRAMMAR, TreeToFlowRuleObject)(flow_rule, 'flow_rule')

