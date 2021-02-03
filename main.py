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

import logging, coloredlogs
import logging.config

logging.basicConfig()
coloredlogs.install(level='DEBUG')
logger = logging.getLogger()

import argparse
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
import yaml
from pprint import pformat
import json

import exp.augmentation as ag
import exp.reason as reason
import exp.setting as setting
import exp.sparql_helper as sh
import exp.graph_wrapper as gw
import exp.rule_database_helper as rdbh


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='The URL to the service (SPARQL endpoint), e.g. http://127.0.0.1:3030/prov')
    parser.add_argument('scheme', choices=['SPROV', 'CWLPROV'],
            default=setting.SCHEME, nargs='?',
            help='Set what scheme the target is using. Currently "SPROV" and "CWLPROV" are supported.')
    parser.add_argument('--aio', action='store_true',
            help='Perform ALl-In-One reasoning, rather than reason about one component at a time.')
    parser.set_defaults(aio=False)
    parser.add_argument('--rule-db',
            default=setting.RULE_DB,
            help='The database where the data rules and flow rules are stored. It should be a JSON file.')
    parser.add_argument("-v", "--verbosity", action="count", default=0,
            help='Increase the verbosity of messages. Overrides "logging.yml"')
    args = parser.parse_args()

    with open('logging.yml','rt') as f:
        config=yaml.safe_load(f.read())
    logging.config.dictConfig(config)
    if args.verbosity:
        logging_level = logging.DEBUG
        if args.verbosity == 1:
            logging_level = logging.CRITICAL
        elif args.verbosity == 2:
            logging_level = logging.ERROR
        elif args.verbosity == 3:
            logging_level = logging.WARN
        elif args.verbosity == 4:
            logging_level = logging.INFO
        elif args.verbosity == 5:
            logging_level = logging.DEBUG
        for handler in logging.getLogger().handlers:
            handler.setLevel(logging_level)
        logger.setLevel(logging_level)
        for logger_name in config['loggers']:
            logging.getLogger(logger_name).setLevel(logging_level)

    service = args.url
    setting.SCHEME = args.scheme
    setting.AIO = args.aio
    setting.RULE_DB = args.rule_db

    rdbh.init_default()

    logger.log(99, "Start")

    if setting.SCHEME == 'CWLPROV':
        results, activated_obligations = propagate_all_cwl(service)
    elif setting.SCHEME == 'SPROV':
        results, activated_obligations = propagate_all_sprov(service)

    draw(results, activated_obligations)


def propagate_common(graph_wrapper):
    obligations = {}

    ag.apply_flow_rules(graph_wrapper)
    ag.apply_imported_rules(graph_wrapper)

    logger.log(99, "Finished Initialization")

    if setting.AIO:
        augmentations, obs = reason.reason_in_total(graph_wrapper)
        obligations.update(obs)
        ag.apply_augmentation(graph_wrapper, augmentations)
    else:
        batches = graph_wrapper.component_to_batches()
        length = sum(len(batch) for batch in batches)
        logger.debug('total number of nodes in batches: %d', length)
        for i, batch in enumerate(batches):
            logger.debug("batch %d: %s", i, batch)
            augmentations, obs = reason.propagate(graph_wrapper, batch)
            logger.debug('augmentations: %s', augmentations)
            obligations.update(obs)
            ag.apply_augmentation(graph_wrapper, augmentations)

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
    from exp import visualise as vis
    for i, graph in enumerate(graphs):
        filename = "graph_{}.png".format(i)
        gb = vis.GraphBuilder(graph, activated_obligations[i]) \
                .data_flow() \
                .rules() \
                .obligation() \
                .flow_rules()
        G = gb.build()
        vis.draw_to_file(G, filename)


if __name__ == '__main__':
    main()
