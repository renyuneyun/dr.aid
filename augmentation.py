#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/09 17:21:10
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from dataclasses import dataclass
import logging
from typing import List

from rdflib import Graph, URIRef, Literal

from .namespaces import NS
from . import parser
from . import rule
from . import rdf_helper as rh
from .rdf_helper import IMPORT_PORT_NAME
from .rule import DataRuleContainer, PortedRules, FlowRule
from .sparql_helper import ComponentInfo
from . import setting
from .exception import IllegalCaseError


logger = logging.getLogger(__name__)


@dataclass
class ComponentAugmentation:
    id: URIRef
    rules: PortedRules


@dataclass
class ImportedRule:
    id: URIRef
    rule: DataRuleContainer


def obtain_imported_rules(component_info_list: List[ComponentInfo]) -> List[ImportedRule]:
    '''
    Recogniser
    '''
    rules = []
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
            irules = parser.parse_data_rule(irules)
            assert irules
            logger.info("component: {} rules: {}ported_rules".format(component_info, irules))
            imported = ImportedRule(component_info.id, irules)
            rules.append(imported)
    return rules


def apply_imported_rules(graph: Graph, imported_rules: List[ImportedRule]) -> None:
    '''

    Modifies the graph in-place
    '''
    for imported in imported_rules:
        component = imported.id

        input_ports = rh.input_ports(graph, component)
        assert IMPORT_PORT_NAME not in input_ports

        if imported.rule:
            rh.insert_imported_rule(graph, component, imported.rule)


def apply_flow_rules(graph: Graph, graph_id: str, component_info_list: List[ComponentInfo]) -> None:
    '''

    Modifies the graph in-place
    '''
    g_flow_rules = setting.INJECTED_FLOW_RULE[None]
    for component_info in component_info_list:
        component = component_info.id
        function = component_info.function
        if function in g_flow_rules:
            fr = g_flow_rules[function]
            rh.set_flow_rule(graph, component, Literal(fr))

    graph_id = URIRef(graph_id)
    if graph_id in setting.INJECTED_FLOW_RULE:
        flow_rules = setting.INJECTED_FLOW_RULE[graph_id]
        for component in rh.components(graph):
            if component in flow_rules:
                fr = flow_rules[component]
                rh.set_flow_rule(graph, component, Literal(fr))


def apply_augmentation(graph: Graph, augmentations: List[ComponentAugmentation]) -> None:
    '''

    Modifies the graph in-place
    '''
    logger.debug(f"Augmentation has {len(augmentations)} components")
    for aug in augmentations:
        component = aug.id
        logger.debug(f"Augmentation for component {component}: {augmentations}")
        for out_port in rh.output_ports(graph, component):
            port_name = str(rh.name(graph, out_port))
            if port_name in aug.rules:
                rule = aug.rules[port_name]
                if rule:
                    rh.insert_rule(graph, out_port, rule)
            else:
                logger.warning("Augmentation for {} does not contain OutPort {}".format(component, port_name))
