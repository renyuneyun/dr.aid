#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/09 17:21:10
#   License :   Apache 2.0 (See LICENSE)
#

'''
This module corresponds to the recogniser. This module contains functions and definitions that are useful for augmenting the original graph.
It used to exist because the graph is exposed as an RDF Graph and all interactions are done directly on it. But since the introduction of `graph_wrapper.GraphWrapper`, there may no longer be a need to have some of the contents here.
'''

from dataclasses import dataclass
import logging
from typing import Dict, List

from rdflib import Graph, URIRef, Literal

from . import parser
from . import rule
from .rule import DataRuleContainer, PortedRules, FlowRule
from .sparql_helper import ComponentInfo
from . import setting
from .exception import IllegalCaseError
from .graph_wrapper import GraphWrapper


logger = logging.getLogger(__name__)


@dataclass
class ComponentAugmentation:
    id: URIRef
    rules: PortedRules


# @dataclass
# class ImportedRule:
#     id: URIRef
#     rule: DataRuleContainer


def apply_imported_rules(graph: GraphWrapper) -> None:
    '''

    Modifies the graph in-place
    '''
    def translate_rule_injection(component_info, defined_injected_rule):
        if isinstance(defined_injected_rule, str):
            irules = defined_injected_rule
        elif callable(defined_injected_rule):
            irules = defined_injected_rule(component_info)
            assert isinstance(irules, str)
        elif not defined_injected_rule:
            irules = rule.RandomRule(True)
        else:
            raise IllegalCaseError('Injected rule should be any of str, function, or None')
        rules_obj = parser.parse_data_rule(irules)
        return rules_obj

    def obtain_rules(component_info_list: List[ComponentInfo], injected_imported_rule_graph) -> Dict[URIRef, DataRuleContainer]:
        rules = {}
        for component_info in component_info_list:
            component_id = component_info.id
            function = component_info.function
            if component_id in injected_imported_rule_graph:
                defined_imported_rules = injected_imported_rule_graph[component_id]
            elif function in injected_imported_rule_graph:
                defined_imported_rules = injected_imported_rule_graph[function]
            else:
                continue
            rules_obj = translate_rule_injection(component_info, defined_imported_rules)
            assert rules_obj
            logger.info("component: {} rules: {}ported_rules".format(component_info, rules_obj))
            rules[component_id] = rules_obj
        return rules

    component_info_list = graph.component_info()
    logger.debug('component_info_list: %s', component_info_list)
    imported_rules = {}
    try:
        imported_rules.update(obtain_rules(component_info_list, setting.INJECTED_IMPORTED_RULE[None]))
    except KeyError:
        pass
    try:
        graph_id = URIRef(graph.graph_id)
    except AttributeError:
        pass
    else:
        try:
            imported_rules.update(obtain_rules(component_info_list, setting.INJECTED_IMPORTED_RULE[graph_id]))
        except KeyError:
            pass
    graph.set_imported_rules(imported_rules)


def apply_flow_rules(graph: GraphWrapper) -> None:
    '''

    Modifies the graph in-place
    '''
    def obtain_rule(component_info_list, injected_rule_graph):
        rules = {}
        logger.debug("injected_flow_rule (graph or maybe not): %s", injected_rule_graph)
        for component_info in component_info_list:
            component = component_info.id
            function = component_info.function
            if function in injected_rule_graph:
                fr = injected_rule_graph[function]
                rules[component] = fr
            if component in injected_rule_graph:
                fr = injected_rule_graph[component]
                rules[component] = fr
        return rules


    pairs = {}
    component_info_list = graph.component_info()

    try:
        pairs.update(obtain_rule(component_info_list, setting.INJECTED_FLOW_RULE[None]))
    except KeyError:
        pass

    try:
        graph_id = URIRef(graph.graph_id)
    except AttributeError:
        pass
    else:
        try:
            pairs.update(obtain_rule(component_info_list, setting.INJECTED_FLOW_RULE[graph_id]))
        except KeyError:
            pass

    graph.set_flow_rules(pairs)


def apply_augmentation(graph: GraphWrapper, augmentations: List[ComponentAugmentation]) -> None:
    '''

    Modifies the graph in-place
    '''
    logger.debug(f"Augmentation has {len(augmentations)} components")
    augmentation_dict = {}
    for aug in augmentations:
        component = aug.id
        augmentation_dict[component] = aug.rules
    graph.apply_augmentation(augmentation_dict)
