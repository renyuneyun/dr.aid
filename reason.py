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
from typing import List

from networkx import MultiDiGraph
from rdflib import Graph, URIRef

from .augmentation import ComponentAugmentation
from .namespaces import NS
from . import rdf_helper as rh
from . import rule as rs
from .rule import DataRuleContainer


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


def propagate(rdf_graph: Graph, component_list: List[URIRef]) -> List[ComponentAugmentation]:
    import_port_name = 'imported_rule'
    augmentations = []
    for component in component_list:
        input_rules = {}
        input_ports = []
        for input_port in rdf_graph.subjects(NS['mine']['inputTo'], component):
            input_port_name = str(next(rdf_graph.objects(input_port, NS['mine']['name'])))
            input_ports.append(input_port_name)
            rules = []
            for ci, connection in enumerate(rdf_graph.subjects(NS['mine']['target'], input_port)):
                rule = None
                for oi, output_port in enumerate(rdf_graph.subjects(NS['mine']['hasConnection'], connection)):
                    assert oi == 0  # Every connection has exactly one OutputPort
                    incomming_rules = list(rdf_graph.objects(output_port, NS['mine']['rule']))
                    if incomming_rules:
                        assert len(incomming_rules) == 1
                        rule = DataRuleContainer.load(str(incomming_rules[0]))
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
            assert import_port_name not in input_ports
            input_ports.append(import_port_name)
            input_rules[import_port_name] = imported_rule

        output_ports = []
        for output_port in rdf_graph.objects(component, NS['mine']['hasOutPort']):
            out_name = str(next(rdf_graph.objects(output_port, NS['mine']['name'])))
            output_ports.append(out_name)
        logger.debug("%s :IN_RULES: %s", component, input_rules)
        flow_rule = rs.DefaultFlow(input_ports, output_ports)
        flow_handler = rs.FlowRuleHandler(flow_rule)
        output_rules = flow_handler.dispatch(input_rules)
        aug = ComponentAugmentation(component, output_rules)
        augmentations.append(aug)
    return augmentations

