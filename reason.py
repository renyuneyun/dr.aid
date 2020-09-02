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

from networkx import MultiDiGraph
from rdflib import Graph, URIRef

from .augmentation import ComponentAugmentation
from .namespaces import NS
from . import rdf_helper as rh
from .rdf_helper import IMPORT_PORT_NAME
from . import rule as rs
from .rule import DataRuleContainer, ActivatedObligation
from . import rule_handle
from .rule_handle import FlowRuleHandler
from .proto import Stage, Imported


logger = logging.getLogger("REASONING")
logger.setLevel(logging.WARN)


def graph_into_batches(graph: MultiDiGraph) -> List[List[URIRef]]:
    g = graph.copy()
    # for node in nx.algorithms.dag.topological_sort(g):
    ret: List[List[URIRef]] = []
    while g:
        lst = []
        for node in g:
            if g.in_degree(node) == 0:
                lst.append(node)
        for node in lst:
            g.remove_node(node)
        ret.append(lst)
    return ret


def on_import(rule: DataRuleContainer) -> List[ActivatedObligation]:
    return on_stage(rule, Imported())


def on_stage(rule: DataRuleContainer, stage: Stage) -> List[ActivatedObligation]:
    return rule.on_stage(stage)


def _virtual_port_for_import(component: URIRef) -> str:
    return f"{str(component)}#{IMPORT_PORT_NAME}"


def _get_flow_rule(graph: Graph, component: URIRef, input_ports: List[URIRef], output_ports: List[URIRef]):
    flow_rule = rh.flow_rule(graph, component)
    if not flow_rule:
        input_ports = list(map(str, input_ports))
        output_ports = list(map(str, output_ports))
        # if has_imported_rule:  # We assume only components which do not have inputs or rules will have imported rules
        # It's no harm to have an extra rule for imported port -- it simply does nothing
        input_ports.append(_virtual_port_for_import(component))
        flow_rule = rs.DefaultFlow(input_ports, output_ports)
    return flow_rule


def _flow_rule_handler(graph: Graph, component: URIRef, input_ports: List[URIRef], output_ports: List[URIRef]):
    flow_rule = _get_flow_rule(graph, component, input_ports, output_ports)
    flow_handler = FlowRuleHandler(flow_rule)
    return flow_handler


def propagate(rdf_graph: Graph, component_list: List[URIRef]) -> Tuple[List[ComponentAugmentation], Dict[URIRef, List[ActivatedObligation]]]:
    augmentations = []
    activated_obligations = {}
    for component in component_list:
        input_rules = {}
        input_ports = []
        for input_port in rh.input_ports(rdf_graph, component):
            input_port_name = str(rh.name(rdf_graph, input_port))
            input_ports.append(input_port_name)
            rules = []
            for ci, connection in enumerate(rh.connections_to_port(rdf_graph, input_port)):
                output_port = rh.one_or_none(rh.output_ports_with_connection(rdf_graph, connection))  # Every connection has exactly one OutputPort (or none)
                rule = rh.rule(rdf_graph, output_port) if output_port else None
                if rule:
                    rules.append(rule)
                    logger.debug("Component %s :: input port %s receives rule, with %s", component, input_port_name, rule.summary())
                    # logger.debug("%s :: %s: %s", component, input_port_name, rule)
            if rules:
                merged_rule = DataRuleContainer.merge(rules[0], *rules[1:])
                input_rules[input_port_name] = merged_rule
            else:
                logger.info("Component %s :: input port %s receives no rule", component, input_port_name)

        imported_rule = rh.imported_rule(rdf_graph, component)
        if imported_rule:
            assert IMPORT_PORT_NAME not in input_ports
            input_ports.append(IMPORT_PORT_NAME)
            input_rules[IMPORT_PORT_NAME] = imported_rule
            obs = on_import(imported_rule)
            if obs:
                activated_obligations[component] = obs

        output_ports = []
        for output_port in rh.output_ports(rdf_graph, component):
            out_name = str(rh.name(rdf_graph, output_port))
            output_ports.append(out_name)
        logger.debug("Component %s receives input rules from %d ports", component, len(input_rules))
        flow_handler = _flow_rule_handler(rdf_graph, component, input_ports, output_ports)
        output_rules = flow_handler.dispatch(input_rules)
        logger.debug("OUTPUT_RULES has %d elements", len(output_rules))
        aug = ComponentAugmentation(component, output_rules)
        augmentations.append(aug)
    return (augmentations, activated_obligations)


def obtain_rules(rdf_graph: Graph, component_list: List[URIRef]) -> Dict[URIRef, Dict[str, DataRuleContainer]]:
    '''
    Get the data rules of all inputs.
    Currently only initial rules
    Return: {Component: {PortURI: DataRule}}
    '''
    component_port_rules = {}
    for component in component_list:
        input_rules = {}
        for input_port in rh.input_ports(rdf_graph, component):
            # input_port_name = str(rh.name(rdf_graph, input_port))
            input_port_name = str(input_port)
            rules = []
            for ci, connection in enumerate(rh.connections_to_port(rdf_graph, input_port)):
                output_port = rh.one_or_none(rh.output_ports_with_connection(rdf_graph, connection))  # Every connection has exactly one OutputPort (or none)
                rule = rh.rule(rdf_graph, output_port) if output_port else None
                if rule:
                    rules.append(rule)
                    logger.debug("Component %s :: input port %s receives rule, with %s", component, input_port_name, rule.summary())
            if rules:
                merged_rule = DataRuleContainer.merge(rules[0], *rules[1:])
                input_rules[input_port_name] = merged_rule
            else:
                logger.info("Component %s :: input port %s receives no rule", component, input_port_name)

        imported_rule = rh.imported_rule(rdf_graph, component)
        if imported_rule:
            input_rules[_virtual_port_for_import(component)] = imported_rule
            # obs = on_import(imported_rule)
            # if obs:
            #     activated_obligations[component] = obs
        if input_rules:
            logger.info("Component %s receives input rules from %d ports", component, len(input_rules))
            component_port_rules[component] = input_rules
        else:
            logger.info("Component %s receives no input rules", component)

    return component_port_rules


def reason_in_total(rdf_graph: Graph, batches: List[List['URIRef']], initial_component_list: List[URIRef]) -> Tuple[List[ComponentAugmentation], Dict[URIRef, List[ActivatedObligation]]]:
    component_list = []
    for batch in batches:
        component_list.extend(batch)
    component_port_rules = obtain_rules(rdf_graph, component_list)
    logger.debug("Read rules: %s", component_port_rules)
    component_flow_rule = {}
    for component_list in batches:
        for component in component_list:
            input_ports = list(rh.input_ports(rdf_graph, component))
            output_ports = list(rh.output_ports(rdf_graph, component))
            flow_rule = _get_flow_rule(rdf_graph, component, input_ports, output_ports)
            component_flow_rule[component] = flow_rule
    logger.info("%d initial components, %d ported_rules, %d flow_rules", len(initial_component_list), len(component_port_rules), len(component_flow_rule))

    augmentations = []
    graph_output_rules = rule_handle.dispatch_all(rdf_graph, batches, component_port_rules, component_flow_rule)
    logger.info("{} graph output rules", len(graph_output_rules))
    for component_list in batches:
        for component in component_list:
            output_rules = {}
            for output_port in rh.output_ports(rdf_graph, component):
                output_port = str(output_port)
                if output_port in graph_output_rules:
                    output_rules[output_port] = graph_output_rules[output_port]
            if output_rules:
                aug = ComponentAugmentation(component, output_rules)
                augmentations.append(aug)
    activated_obligations = {}
    return (augmentations, activated_obligations)

