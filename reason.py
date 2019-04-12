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
import networkx as nx
from networkx import MultiDiGraph
from rdflib import Graph, URIRef
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
from SPARQLWrapper import SPARQLWrapper
from typing import Dict, List

import augmentation as ag
from augmentation import ComponentAugmentation
from namespaces import NS
import rule as rs
from rule import DataRuleWrapper
import sparql_helper as sh


logger = logging.getLogger("REASONING")
logger.setLevel(logging.INFO)


def get_component_graph(sparql: SPARQLWrapper) -> MultiDiGraph:
    rdf_graph = sh.get_graph_component(sparql)
    graph = rdflib_to_networkx_multidigraph(rdf_graph)
    return graph


def graph_into_batches(graph: MultiDiGraph) -> List[List[URIRef]]:
    g = graph.copy()
    # for node in nx.algorithms.dag.topological_sort(g):
    lst: List[List[URIRef]] = []
    while g:
        l = []
        for node in g:
            if g.in_degree(node) == 0:
                l.append(node)
        for node in l:
            g.remove_node(node)
        lst.append(l)
    return lst


def propagate(rdf_graph: Graph, component_list: List[URIRef]) -> List[ComponentAugmentation]:
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
                    output_rules = list(rdf_graph.objects(output_port, NS['mine']['rule']))
                    if output_rules:
                        assert len(output_rules) == 1
                        rule = DataRuleWrapper.load(str(output_rules[0]))
                if rule:
                    rules.append(rule)
                    logger.debug("%s :: %s: %s", component, input_port_name, rule)
            if rules:
                merged_rule = DataRuleWrapper.merge(*rules)
                input_rules[input_port_name] = merged_rule
            else:
                logger.info("InputPort %s of %s has no rules", input_port_name, component)
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
        




