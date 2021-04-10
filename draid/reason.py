#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/11 12:05:47
#   License :   Apache 2.0 (See LICENSE)
#

'''
This module contains the functions necessary to do the main reasoning -- propagating data rules from input ports to output ports, process the flow rules, and process the whole data-flow graph / workflow.
'''

import logging
from typing import Dict, List, Tuple

from rdflib import Graph, URIRef

from .rule import DataRuleContainer, ActivatedObligation, PortedRules
from . import rule_handle
from .rule_handle import FlowRuleHandler
from .proto import Stage, Imported, Processing
from .graph_wrapper import ComponentAugmentation, GraphWrapper, virtual_port_for_import, K_FUNCTION


logger = logging.getLogger(__name__)


def _flow_rule_handler(graph: GraphWrapper, component: URIRef):
    flow_rule = graph.get_flow_rule(component)
    flow_handler = FlowRuleHandler(flow_rule)
    return flow_handler


def _retract_port_name(graph: GraphWrapper, component: URIRef, ported_rules: 'PortedRules') -> 'PortedRules':
    '''
    Change the names of the ports in `ported_rules` to the original one used internally, i.e. from `GraphWrapper.unique_name_of_port` to `GraphWrapper.name_of_port` This is because when applying the augmentation, the PortedRule is associated with its component URI, and using internal port identifiers is enough.
    '''
    ported_rules_new = {}
    for output_port in graph.output_ports(component):  # The output port (IRI) node. Will use its name later
        output_port_name = graph.name_of_port(output_port)  # The short name used in the component. The ComponentAugmentation uses the short name.
        output_port_unique_name = graph.unique_name_of_port(output_port)  # The long name, with component ID, etc.
        if output_port_unique_name in ported_rules:
            ported_rules_new[output_port_name] = ported_rules[output_port_unique_name]
    return ported_rules_new


def propagate(graph: GraphWrapper, component_list: List[URIRef]) -> Tuple[List[ComponentAugmentation], Dict[URIRef, List[ActivatedObligation]]]:
    augmentations = []
    activated_obligations = {}
    for component in component_list:
        component_info = graph.component_info(component)[0]
        function_name = component_info.function

        info = graph.get_graph_info()
        info.update(graph.info)
        info.update(component_info.par)
        info['processId'] = str(component_info.id)

        input_rules = graph.get_data_rules(component)

        obs = []

        for input_rule in input_rules.values():
            obs.extend(input_rule.on_stage(Processing(), function_name, info))

        imported_rule = graph.get_imported_rules(component)
        if imported_rule:
            input_rules[virtual_port_for_import(component)] = imported_rule
            obs.extend(imported_rule.on_stage(Imported(), function_name, info))

        if obs:
            if component not in activated_obligations:
                activated_obligations[component] = []
            activated_obligations[component].extend(obs)

        logger.debug("Component %s receives input rules from %d ports", component, len(input_rules))
        flow_handler = _flow_rule_handler(graph, component)
        output_rules = flow_handler.dispatch(input_rules)
        logger.debug("OUTPUT_RULES has %d elements", len(output_rules))
        output_rules = _retract_port_name(graph, component, output_rules)
        if output_rules:
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
        flow_rule = graph.get_flow_rule(component, ensure_name_uniqueness=True)
        component_flow_rule[component] = flow_rule
    logger.info("%d initial components, %d ported_rules, %d flow_rules", len(initial_component_list), len(component_port_rules), len(component_flow_rule))
    augmentations = []

    graph_output_rules = rule_handle.dispatch_all(graph, component_port_rules, component_flow_rule)
    logger.info("%d graph output rules", len(graph_output_rules))
    for component in component_list:
        output_rules = _retract_port_name(graph, component, graph_output_rules)
        if output_rules:
            aug = ComponentAugmentation(component, output_rules)
            augmentations.append(aug)
    activated_obligations = {}  # type: Dict[URIRef, List[ActivatedObligation]]
    return (augmentations, activated_obligations)

