#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/12 18:53:31
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

import logging
from SPARQLWrapper import SPARQLWrapper, N3, TURTLE, JSON, JSONLD, XML

import augmentation as ag
import reason
import sparql_helper as sh


def main():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    logger.log(99, "Start")

    sparql = SPARQLWrapper("http://localhost:3030/data")
    
    initial_components = list(sh.get_initial_components(sparql))
    
    component_info_list = sh.get_components_info(sparql, initial_components)
    
    component_augmentation_list = ag.obtain_component_augmentation(component_info_list)    
    rdf_graph = sh.get_graph_dependency_with_port(sparql)
    ag.apply_augmentation(rdf_graph, component_augmentation_list)
    sh.write_transformed_graph(sparql, rdf_graph)
    
    logger.log(99, "Finished Initialization")
    
    component_graph = reason.get_component_graph(sparql)
    batches = reason.graph_into_batches(component_graph)
    
    batches = batches[1:]
    for batch in batches:
        augmentations = reason.propagate(rdf_graph, batch)
        ag.apply_augmentation(rdf_graph, augmentations)
    
    sh.write_transformed_graph(sparql, rdf_graph)

    logger.log(99, "Finished")


if __name__ == '__main__':
    main()

