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
import exp.rdf_helper as rh
import exp.reason as reason
import exp.sparql_helper as sh

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)


def main():
    logger.setLevel(logging.DEBUG)

    logger.log(99, "Start")

    service = "http://127.0.0.1:3030/prov"
    # service = "http://localhost:3030/data"

    results, activated_obligations = propagate_all_cwl(service)
    draw(results, activated_obligations)


def import_flow_rules(graph_id, rdf_graph, s_helper):
    components = rh.components(rdf_graph)
    component_info_list = s_helper.get_components_info(components)
    ag.apply_flow_rules(rdf_graph, graph_id, component_info_list)


def import_rules(rdf_graph, s_helper, components):
    component_info_list = s_helper.get_components_info(components)
    imported_rule_list = ag.obtain_imported_rules(component_info_list)
    ag.apply_imported_rules(rdf_graph, imported_rule_list)


def propagate_all(service):
    s_helper = sh.SProvHelper(service)

    graphs = list(s_helper.get_wfe_graphs())
    assert graphs

    results = []
    activated_obligations = []
    for i, graph in enumerate(graphs):

        obligations = {}

        s_helper.set_graph(graph)

        rdf_graph = s_helper.get_graph_dependency_with_port()
        import_flow_rules(graph, rdf_graph, s_helper)

        a_helper = sh.AugmentedGraphHelper(service)

        logger.log(99, "Finished Initialization")

        rdf_component_graph = s_helper.get_graph_component()
        component_graph = rdflib_to_networkx_multidigraph(rdf_component_graph)
        batches = reason.graph_into_batches(component_graph)

        for batch in batches:
            import_rules(rdf_graph, s_helper, batch)
            augmentations, obs = reason.propagate(rdf_graph, batch)
            obligations.update(obs)
            ag.apply_augmentation(rdf_graph, augmentations)

        a_helper.write_transformed_graph(rdf_graph)

        results.append(rdf_graph)

        activated_obligations.append(obligations)

    return results, activated_obligations


def propagate_all_cwl(service):
    s_helper = sh.CWLHelper(service)

    results = []
    activated_obligations = []

    obligations = {}

    graph = ''
    rdf_graph = s_helper.get_graph_dependency_with_port()
    logger.debug('rdf_graph: %s', rdf_graph)
    import_flow_rules(graph, rdf_graph, s_helper)

    a_helper = sh.AugmentedGraphHelper(service)

    logger.log(99, "Finished Initialization")

    rdf_component_graph = s_helper.get_graph_component()
    component_graph = rdflib_to_networkx_multidigraph(rdf_component_graph)
    batches = reason.graph_into_batches(component_graph)

    length = sum(len(batch) for batch in batches)
    logger.debug('total number of nodes in batches: %d', length)

    for batch in batches:
        logger.debug("batch: %s", batch)
        import_rules(rdf_graph, s_helper, batch)
        augmentations, obs = reason.propagate(rdf_graph, batch)
        obligations.update(obs)
        ag.apply_augmentation(rdf_graph, augmentations)

    a_helper.write_transformed_graph(rdf_graph)

    results.append(rdf_graph)

    activated_obligations.append(obligations)

    return results, activated_obligations


def draw(rdf_graphs, activated_obligations=[]):
    from exp import visualise as vis
    for i, rdf_graph in enumerate(rdf_graphs):
        filename = "graph_{}.png".format(i)
        gb = vis.GraphBuilder(rdf_graph, activated_obligations[i]) \
                .data_flow() \
                .rules() \
                .obligation() \
                .flow_rules()
        G = gb.build()
        vis.draw_to_file(G, filename)


if __name__ == '__main__':
    main()
