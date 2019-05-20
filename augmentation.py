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
from .rule import DataRuleContainer, PortedRules
from .sparql_helper import ComponentInfo


logger = logging.getLogger("AUGM")
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.WARNING)


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
        assert 'imported' not in input_ports

        if imported.rule:
            rh.insert_imported_rule(graph, component, imported.rule)


def apply_augmentation(graph: Graph, augmentations: List[ComponentAugmentation]) -> None:
    '''

    Modifies the graph in-place
    '''
    for aug in augmentations:
        component = aug.id
        for out_port in graph.objects(component, NS['mine']['hasOutPort']):
            port_name_ = list(graph.objects(out_port, NS['mine']['name']))
            assert len(port_name_) == 1
            port_name = str(port_name_[0])
            if port_name in aug.rules:
                rule = aug.rules[port_name]
                if rule:
                    graph.add((out_port, NS['mine']['rule'], Literal(rule.dump())))
            else:
                logger.warning("OutPort {} not found in {}".format(port_name, component))

