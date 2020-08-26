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
from .rule_handle import FlowRuleHandler
from .proto import Stage, Imported


logger = logging.getLogger("REASONING")
logger.setLevel(logging.WARNING)


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


def _flow_rule_handler(graph: Graph, component: URIRef, input_ports: List[URIRef], output_ports: List[URIRef]):
    flow_rule = rh.flow_rule(graph, component)
    if not flow_rule:
        flow_rule = rs.DefaultFlow(input_ports, output_ports)
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
                    logger.debug("%s :: %s: %s", component, input_port_name, rule)
            if rules:
                merged_rule = DataRuleContainer.merge(rules[0], *rules[1:])
                input_rules[input_port_name] = merged_rule
            else:
                logger.info("InputPort %s of %s has no rules", input_port_name, component)

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
        logger.debug("%s :IN_RULES: %s", component, input_rules)
        flow_handler = _flow_rule_handler(rdf_graph, component, input_ports, output_ports)
        output_rules = flow_handler.dispatch(input_rules)
        aug = ComponentAugmentation(component, output_rules)
        augmentations.append(aug)
    return (augmentations, activated_obligations)

