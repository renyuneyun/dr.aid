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

from .synthetic_raw_rules import FLOW_RULES


logger = logging.getLogger("AUGM")
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.WARN)


@dataclass
class ComponentAugmentation:
    id: URIRef
    rules: PortedRules


@dataclass
class ImportedRule:
    id: URIRef
    rule: DataRuleContainer


SOURCE_FUNCTION = {'Source', 'downloadPE', 'Collector', 'COLLECTOR1', 'COLLECTOR2',
                   'NumberProducer'}


def obtain_imported_rules(component_info_list: List[ComponentInfo]) -> List[ImportedRule]:
    '''
    Recogniser
    '''
    def is_originator(component_info: ComponentInfo) -> bool:
        if component_info.function in SOURCE_FUNCTION:
            return True
        return False
        #return True
    rules = []
    for component_info in component_info_list:
        if is_originator(component_info):
            irules = parser.parse_data_rule(rule.RandomRule(True))
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
                logger.warning("OutPort {} not found in {}".format(port_name, component))


def apply_flow_rules(graph: Graph, graph_id: str, component_info_list: List[ComponentInfo]) -> None:
    '''

    Modifies the graph in-place
    '''
    handled = set()

    graph_id = URIRef(graph_id)
    if graph_id in FLOW_RULES:
        flow_rules = FLOW_RULES[graph_id]
        for component in rh.components(graph):
            if component in flow_rules:
                fr = flow_rules[component]
                rh.set_flow_rule(graph, component, Literal(fr))
                handled.add(component)

    g_flow_rules = FLOW_RULES[None]
    for component_info in component_info_list:
        component = component_info.id
        function = component_info.function
        if component in handled:
            continue
        if function in g_flow_rules:
            fr = g_flow_rules[function]
            rh.set_flow_rule(graph, component, Literal(fr))

