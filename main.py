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
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph

import exp.augmentation as ag
import exp.reason as reason
import exp.sparql_helper as sh


def main():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    logger.log(99, "Start")

    service = "http://localhost:3030/data"
    s_helper = sh.SProvHelper(service)

    graphs = list(s_helper.get_wfe_graphs())
    assert len(graphs) == 1
    graph = 'http://schema.org#debbf0e323c8-18-1a15ad5e-5629-11e9-9864-0242ac120003'
    assert str(graphs[0]) == graph

    s_helper.set_graph(graph)

    initial_components = s_helper.get_initial_components()
    component_info_list = s_helper.get_components_info(initial_components)
    component_augmentation_list = ag.obtain_component_augmentation(component_info_list)    

    rdf_graph = s_helper.get_graph_dependency_with_port()

    ag.apply_augmentation(rdf_graph, component_augmentation_list)

    a_helper = sh.AugmentedGraphHelper(service)

    a_helper.write_transformed_graph(rdf_graph)

    logger.log(99, "Finished Initialization")

    rdf_component_graph = s_helper.get_graph_component()
    component_graph = rdflib_to_networkx_multidigraph(rdf_component_graph)
    batches = reason.graph_into_batches(component_graph)

    batches = batches[1:]
    for batch in batches:
        augmentations = reason.propagate(rdf_graph, batch)
        ag.apply_augmentation(rdf_graph, augmentations)

    a_helper.write_transformed_graph(rdf_graph)


if __name__ == '__main__':
    main()

