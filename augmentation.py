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
from rdflib import Graph, URIRef, Literal
from typing import Dict, List, Optional
import logging

from namespaces import NS
import rule
from rule import DataRuleWrapper
from sparql_helper import ComponentInfo


logger = logging.getLogger("AUGM")
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.WARNING)


PortedRules = Dict[str, Optional[DataRuleWrapper]]

@dataclass
class ComponentAugmentation:
    id: URIRef
    rules: PortedRules


def is_originator(component_info: ComponentInfo) -> bool:
    if component_info.function == 'Source':
        return True
    return False


def get_rules_of_ports(component_info: ComponentInfo) -> PortedRules:
    port = 'output'
    if is_originator(component_info):
        return {port: rule.TestRule()}
    else:
        return {port: None}


def obtain_component_augmentation(component_info_list: List[ComponentInfo]) -> List[ComponentAugmentation]:
    augmentations = []
    for component_info in component_info_list:
        ported_rules = get_rules_of_ports(component_info)
        logger.info("component: {} rules: {}ported_rules".format(component_info, ported_rules))
        aug = ComponentAugmentation(component_info.id, ported_rules)
        augmentations.append(aug)
    return augmentations


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

