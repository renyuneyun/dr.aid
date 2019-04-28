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

logger = logging.getLogger()


def main():
    logger.setLevel(logging.DEBUG)

    logger.log(99, "Start")

    service = "http://localhost:3030/data"

    results = propagate_all(service)
    draw(results)


def import_rules(rdf_graph, s_helper, components):
    component_info_list = s_helper.get_components_info(components)
    imported_rule_list = ag.obtain_imported_rules(component_info_list)
    ag.apply_imported_rules(rdf_graph, imported_rule_list)


def propagate_all(service):
    s_helper = sh.SProvHelper(service)

    graphs = list(s_helper.get_wfe_graphs())
    assert graphs

    results = []
    for i, graph in enumerate(graphs):

        s_helper.set_graph(graph)

        rdf_graph = s_helper.get_graph_dependency_with_port()

        a_helper = sh.AugmentedGraphHelper(service)

        logger.log(99, "Finished Initialization")

        rdf_component_graph = s_helper.get_graph_component()
        component_graph = rdflib_to_networkx_multidigraph(rdf_component_graph)
        batches = reason.graph_into_batches(component_graph)

        batches = batches
        for batch in batches:
            import_rules(rdf_graph, s_helper, batch)
            augmentations = reason.propagate(rdf_graph, batch)
            ag.apply_augmentation(rdf_graph, augmentations)

        a_helper.write_transformed_graph(rdf_graph)

        results.append(rdf_graph)

    return results


def draw(rdf_graphs):
    from exp import visualise as vis
    for i, rdf_graph in enumerate(rdf_graphs):
        filename = "graph_{}.png".format(i)
        gb = vis.GraphBuilder(rdf_graph)
        G = gb.data_flow().rules().build()
        vis.draw_to_file(G, filename)

    return rdf_graph


if __name__ == '__main__':
    main()

