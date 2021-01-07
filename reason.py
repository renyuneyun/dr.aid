#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/11 12:05:47
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

import logging
from typing import Dict, List, Tuple

from rdflib import Graph, URIRef

from .augmentation import ComponentAugmentation
from .rdf_helper import IMPORT_PORT_NAME
from .rule import DataRuleContainer, ActivatedObligation
from . import rule_handle
from .rule_handle import FlowRuleHandler
from .proto import Stage, Imported
from .graph_wrapper import GraphWrapper
from .setting import virtual_port_for_import


logger = logging.getLogger(__name__)


def on_import(rule: DataRuleContainer) -> List[ActivatedObligation]:
    return on_stage(rule, Imported())


def on_stage(rule: DataRuleContainer, stage: Stage) -> List[ActivatedObligation]:
    return rule.on_stage(stage)


def _flow_rule_handler(graph: GraphWrapper, component: URIRef):
    flow_rule = graph.get_flow_rule(component)
    flow_handler = FlowRuleHandler(flow_rule)
    return flow_handler


def propagate(graph: GraphWrapper, component_list: List[URIRef]) -> Tuple[List[ComponentAugmentation], Dict[URIRef, List[ActivatedObligation]]]:
    augmentations = []
    activated_obligations = {}
    for component in component_list:
        input_rules = graph.get_data_rules(component)

        imported_rule = graph.get_imported_rules(component)
        if imported_rule:
            # assert IMPORT_PORT_NAME not in input_ports
            # input_ports.append(IMPORT_PORT_NAME)
            # input_rules[IMPORT_PORT_NAME] = imported_rule
            # The above lines were used previously. A consensus on the name of ports need to be made in the code.
            input_rules[virtual_port_for_import(component)] = imported_rule
            obs = on_import(imported_rule)
            if obs:
                activated_obligations[component] = obs

        logger.debug("Component %s receives input rules from %d ports", component, len(input_rules))
        flow_handler = _flow_rule_handler(graph, component)
        output_rules = flow_handler.dispatch(input_rules)
        logger.debug("OUTPUT_RULES has %d elements", len(output_rules))
        aug = ComponentAugmentation(component, output_rules)
        augmentations.append(aug)
    return (augmentations, activated_obligations)


def obtain_rules(graph: GraphWrapper, component_list: List[URIRef]) -> Dict[URIRef, Dict[str, DataRuleContainer]]:
    '''
    Get the data rules of all inputs.
    Currently only initial rules
    Return: {Component: {PortURI: DataRule}}
    '''
    component_port_rules = {}
    for component in component_list:
        input_rules = graph.get_data_rules(component)

        imported_rule = graph.get_imported_rules(component)
        if imported_rule:
            input_rules[virtual_port_for_import(component)] = imported_rule
            # obs = on_import(imported_rule)
            # if obs:
            #     activated_obligations[component] = obs
        if input_rules:
            logger.info("Component %s receives input rules from %d ports", component, len(input_rules))
            component_port_rules[component] = input_rules
        else:
            logger.info("Component %s receives no input rules", component)

    return component_port_rules


def reason_in_total(graph: GraphWrapper) -> Tuple[List[ComponentAugmentation], Dict[URIRef, List[ActivatedObligation]]]:
    initial_component_list = graph.initial_components()
    component_list = graph.components()
    component_port_rules = obtain_rules(graph, component_list)
    logger.debug("Read rules: %s", component_port_rules)
    component_flow_rule = {}
    for component in component_list:
        flow_rule = graph.get_flow_rule(component, use_name=False)
        component_flow_rule[component] = flow_rule
    logger.info("%d initial components, %d ported_rules, %d flow_rules", len(initial_component_list), len(component_port_rules), len(component_flow_rule))
    augmentations = []

    graph_output_rules = rule_handle.dispatch_all(graph, component_port_rules, component_flow_rule)
    logger.info("%d graph output rules", len(graph_output_rules))
    for component in component_list:
        output_rules = {}
        for output_port in graph.output_ports(component):  # The output port (IRI) node. Will use its name later
            output_port_name = str(graph.name_of_port(output_port))  # The short name used in the component. The ComponentAugmentation uses the short name.
            output_port = str(output_port)  # The long name, with component ID, etc.
            if output_port in graph_output_rules:
                output_rules[output_port_name] = graph_output_rules[output_port]
        if output_rules:
            aug = ComponentAugmentation(component, output_rules)
            augmentations.append(aug)
    activated_obligations = {}
    return (augmentations, activated_obligations)

