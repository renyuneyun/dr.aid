#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/09 17:21:10
#   License :   Apache 2.0 (See LICENSE)
#

'''
This module contains functions and definitions that are useful for augmenting the original graph.
It used exist because the graph is exposed as an RDF Graph and all interactions are done directly on it. But since the introduction of `graph_wrapper.GraphWrapper`, there may no longer be a need to have some of the contents here.
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


@dataclass
class ImportedRule:
    id: URIRef
    rule: DataRuleContainer


def obtain_imported_rules(component_info_list: List[ComponentInfo]) -> Dict[URIRef, DataRuleContainer]:
    '''
    Recogniser
    '''
    rules = {}
    logger.debug('component_info_list: %s', component_info_list)
    for component_info in component_info_list:
        if component_info.function in setting.INJECTED_IMPORTED_RULE:
            defined_imported_rules = setting.INJECTED_IMPORTED_RULE[component_info.function]
            if isinstance(defined_imported_rules, str):
                irules = defined_imported_rules
            elif callable(defined_imported_rules):
                irules = defined_imported_rules(component_info)
                assert isinstance(irules, str)
            elif not defined_imported_rules:
                irules = rule.RandomRule(True)
            else:
                raise IllegalCaseError()
            rules_obj = parser.parse_data_rule(irules)
            assert rules_obj
            logger.info("component: {} rules: {}ported_rules".format(component_info, rules_obj))
            rules[component_info.id] = rules_obj
    return rules


def apply_imported_rules(graph: GraphWrapper) -> None:
    '''

    Modifies the graph in-place
    '''
    component_info_list = graph.component_info()
    imported_rules = obtain_imported_rules(component_info_list)
    graph.set_imported_rules(imported_rules)


def apply_flow_rules(graph: GraphWrapper) -> None:
    '''

    Modifies the graph in-place
    '''
    g_flow_rules = setting.INJECTED_FLOW_RULE[None]
    pairs = {}
    for component_info in graph.component_info():
        component = component_info.id
        function = component_info.function
        if function in g_flow_rules:
            fr = g_flow_rules[function]
            pairs[component] = fr

    try:
        graph_id = URIRef(graph.graph_id)  # type: ignore
        if graph_id in setting.INJECTED_FLOW_RULE:
            flow_rules = setting.INJECTED_FLOW_RULE[graph_id]
            for component in graph.components():
                if component in flow_rules:
                    fr = flow_rules[component]
                    pairs[component] = fr
    except AttributeError:
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
