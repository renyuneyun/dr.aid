# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/03/14 10:38:46
#   License :   Apache 2.0 (See LICENSE)
#

'''
The main entry of the DRAid system. It can be used by a __main__.py, a Jupyter notebook, or anything similar.
'''

import json

from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph

from . import recognizer as rcg
from . import reason as reason
from . import setting as setting
from . import sparql_helper as sh
from . import graph_wrapper as gw
from . import rule_database_helper as rdbh

import logging
logger = logging.getLogger()


def main(service, scheme=None, aio=None, rule_db=None, db_write_to=None):
    if scheme: setting.SCHEME = scheme
    if aio: setting.AIO = aio
    if rule_db: setting.RULE_DB = rule_db
    if db_write_to: setting.DB_WRITE_TO = db_write_to

    rdbh.init_default()

    logger.log(99, "Start")

    if setting.SCHEME == 'CWLPROV':
        results, activated_obligations = propagate_all_cwl(service)
    elif setting.SCHEME == 'SPROV':
        results, activated_obligations = propagate_all_sprov(service)

    draw(results, activated_obligations)


def propagate_common(graph_wrapper):
    obligations = {}

    rcg.apply_flow_rules(graph_wrapper)
    rcg.apply_imported_rules(graph_wrapper)
    rcg.apply_data_rules(graph_wrapper)

    logger.log(99, "Finished Initialization")

    if setting.AIO:
        augmentations, obs = reason.reason_in_total(graph_wrapper)
        obligations.update(obs)
        graph_wrapper.apply_augmentation(augmentations)
    else:
        batches = graph_wrapper.component_to_batches()
        length = sum(len(batch) for batch in batches)
        logger.debug('total number of nodes in batches: %d', length)
        for i, batch in enumerate(batches):
            logger.debug("batch %d: %s", i, batch)
            augmentations, obs = reason.propagate(graph_wrapper, batch)
            logger.debug('augmentations: %s', augmentations)
            obligations.update(obs)
            graph_wrapper.apply_augmentation(augmentations)

    if setting.DB_WRITE_TO:
        rdbh.update_db_default(graph_wrapper)

    return graph_wrapper, obligations


def propagate_all_sprov(service):
    s_helper = sh.SProvHelper(service)

    graphs = list(s_helper.get_wfe_graphs())
    assert graphs

    results = []
    activated_obligations = []
    for i, graph in enumerate(graphs):
        graph_wrapper = gw.GraphWrapper.from_sprov(s_helper, subgraph=graph)
        graph_wrapper, obligations = propagate_common(graph_wrapper)

        a_helper = sh.AugmentedGraphHelper(service)
        a_helper.write_transformed_graph(graph_wrapper)

        results.append(graph_wrapper)

        activated_obligations.append(obligations)

    return results, activated_obligations


def propagate_all_cwl(service):
    s_helper = sh.CWLHelper(service)

    results = []
    activated_obligations = []

    obligations = {}

    graph_wrapper = gw.GraphWrapper.from_cwl(s_helper)
    graph_wrapper, obligations = propagate_common(graph_wrapper)

    a_helper = sh.AugmentedGraphHelper(service)
    a_helper.write_transformed_graph(graph_wrapper)

    results.append(graph_wrapper)

    activated_obligations.append(obligations)

    return results, activated_obligations


def draw(graphs, activated_obligations=[]):
    from draid import visualise as vis
    for i, graph in enumerate(graphs):
        filename = "graph_{}.png".format(i)
        gb = vis.GraphBuilder(graph, activated_obligations[i]) \
                .data_flow() \
                .rules() \
                .obligation() \
                .flow_rules()
        G = gb.build()
        vis.draw_to_file(G, filename)
