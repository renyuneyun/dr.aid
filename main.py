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
import exp.rdf_helper as rh
import exp.reason as reason
import exp.setting as setting
import exp.sparql_helper as sh


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

    # Read the rule database. Not actually used yet, but it should work.
    try:
        with open(setting.RULE_DB, 'r') as f:
            extra_rules = json.load(f)
            extra_data_rules = extra_rules['data_rules']
            extra_flow_rules = extra_rules['flow_rules']
            setting.INJECTED_DATA_RULE = setting.INJECTED_DATA_RULE + extra_data_rules
            setting.INJECTED_FLOW_RULE = setting.INJECTED_FLOW_RULE + extra_flow_rules
    except FileNotFoundError:
        pass

    logger.log(99, "Start")

    if setting.SCHEME == 'CWLPROV':
        results, activated_obligations = propagate_all_cwl(service)
    elif setting.SCHEME == 'SPROV':
        results, activated_obligations = propagate_all(service)

    draw(results, activated_obligations)


def inject_flow_rules(graph_id, rdf_graph, s_helper):
    components = rh.components(rdf_graph)
    component_info_list = s_helper.get_components_info(components)
    logger.debug("component_info: %s", pformat(component_info_list))
    ag.apply_flow_rules(rdf_graph, graph_id, component_info_list)


def inject_imported_rules(rdf_graph, s_helper, components):
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
        logger.debug('rdf_graph: %s', rdf_graph)
        inject_flow_rules(graph, rdf_graph, s_helper)

        a_helper = sh.AugmentedGraphHelper(service)

        logger.log(99, "Finished Initialization")

        rdf_component_graph = s_helper.get_graph_component()
        component_graph = rdflib_to_networkx_multidigraph(rdf_component_graph)
        batches = reason.graph_into_batches(component_graph)

        if setting.AIO:
            for batch in batches:
                inject_imported_rules(rdf_graph, s_helper, batch)
            augmentations, obs = reason.reason_in_total(rdf_graph, batches, batches[0])
            obligations.update(obs)
            ag.apply_augmentation(rdf_graph, augmentations)
        else:
            for batch in batches:
                inject_imported_rules(rdf_graph, s_helper, batch)
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
    inject_flow_rules(graph, rdf_graph, s_helper)

    a_helper = sh.AugmentedGraphHelper(service)

    logger.log(99, "Finished Initialization")

    rdf_component_graph = s_helper.get_graph_component()
    component_graph = rdflib_to_networkx_multidigraph(rdf_component_graph)
    batches = reason.graph_into_batches(component_graph)

    length = sum(len(batch) for batch in batches)
    logger.debug('total number of nodes in batches: %d', length)

    if setting.AIO:
        for batch in batches:
            inject_imported_rules(rdf_graph, s_helper, batch)
        augmentations, obs = reason.reason_in_total(rdf_graph, batches, batches[0])
        obligations.update(obs)
        ag.apply_augmentation(rdf_graph, augmentations)
    else:
        for i, batch in enumerate(batches):
            logger.debug("batch %d: %s", i, batch)
            inject_imported_rules(rdf_graph, s_helper, batch)
            augmentations, obs = reason.propagate(rdf_graph, batch)
            logger.debug('augmentations: %s', augmentations)
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
