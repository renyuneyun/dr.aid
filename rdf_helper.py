#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/25 15:39:02
#   License :   Apache 2.0 (See LICENSE)
#

'''
This module contains the helper functions for dealing with the underlying RDF Graph. Users should use `graph_wrapper.GraphWrapper` instead of directly using the functions provided in this module.
'''

import json
from rdflib import Graph, Literal, URIRef
from typing import Dict, Iterable, Optional, Tuple

from .namespaces import NS
from . import parser
from .rule import DataRuleContainer, FlowRule


def one(iterator):
    lst = list(iterator)
    assert len(lst) == 1
    return lst[0]


def one_or_none(iterator):
    lst = list(iterator)
    if len(lst) == 0:
        return None
    assert len(lst) == 1
    return lst[0]


def name(graph: Graph, subject: URIRef) -> URIRef:
    return one(graph.objects(subject, NS['mine']['name']))


def components(graph: Graph) -> Iterable[URIRef]:
    return graph.subjects(NS['rdf']['type'], NS['s-prov']['Component'])


def output_ports(graph: Graph, component: URIRef) -> Iterable[URIRef]:
    return graph.objects(component, NS['mine']['hasOutPort'])


def input_ports(graph: Graph, component: URIRef) -> Iterable[URIRef]:
    return graph.subjects(NS['mine']['inputTo'], component)


def connections_to_port(graph: Graph, input_port: URIRef) -> Iterable[URIRef]:
    return graph.subjects(NS['mine']['target'], input_port)


def connections_from_port(graph: Graph, output_port: URIRef) -> Iterable[URIRef]:
    return graph.objects(output_port, NS['mine']['hasConnection'])


def connection_targets(graph: Graph, connection: URIRef) -> Iterable[URIRef]:
    return graph.objects(connection, NS['mine']['target'])


def output_ports_with_connection(graph: Graph, connection: URIRef) -> Iterable[URIRef]:
    return graph.subjects(NS['mine']['hasConnection'], connection)


def is_input_port(graph: Graph, node: URIRef) -> bool:
    return (node, NS['rdf']['type'], NS['mine']['InputPort']) in graph


def is_output_port(graph: Graph, node: URIRef) -> bool:
    return (node, NS['rdf']['type'], NS['mine']['OutputPort']) in graph


def input_to(graph: Graph, input_port: URIRef) -> URIRef:
    return one(graph.objects(input_port, NS['mine']['inputTo']))


def output_from(graph: Graph, output_port: URIRef) -> URIRef:
    return one(graph.subjects(NS['mine']['hasOutPort'], output_port))


def component_info(graph: Graph, component: URIRef) -> Dict[str, str]:
    info_repr = one(graph.objects(component, NS['mine']['info'])).toPython()
    return json.loads(info_repr)


def put_component_info(graph: Graph, component: URIRef, info: Dict[str, str]) -> None:
    info_repr = json.dumps(info)
    graph.add((component, NS['mine']['info'], Literal(info_repr)))


def rule_literal(graph: Graph, output_port: URIRef) -> Optional[Literal]:
    return one_or_none(graph.objects(output_port, NS['mine']['rule']))


def rule(graph: Graph, output_port: URIRef) -> Optional[DataRuleContainer]:
    literal = rule_literal(graph, output_port)
    return parser.parse_data_rule(literal) if literal else None


def imported_rule(graph: Graph, component: URIRef) -> Optional[DataRuleContainer]:
    imported_rule_literal = one_or_none(graph.objects(component, NS['mine']['importedRule']))
    return parser.parse_data_rule(imported_rule_literal) if imported_rule_literal else None


def flow_rule(graph: Graph, component: URIRef) -> Optional[FlowRule]:
    flow_rule_literal = one_or_none(graph.objects(component, NS['mine']['flowRule']))
    flow_rule_str = str(flow_rule_literal) if flow_rule_literal else None
    return parser.parse_flow_rule(flow_rule_str)


def insert_imported_rule(graph: Graph, component: URIRef, rule: DataRuleContainer) -> None:
    graph.add((component, NS['mine']['importedRule'], Literal(rule.dump())))


def insert_rule(graph: Graph, component: URIRef, rule: DataRuleContainer) -> None:
    graph.add((component, NS['mine']['rule'], Literal(rule.dump())))


def set_flow_rule(graph: Graph, component: URIRef, flow_rule: str) -> None:
    graph.add((component, NS['mine']['flowRule'], flow_rule))

