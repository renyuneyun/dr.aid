#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/02/02 15:43:01
#   License :   Apache 2.0 (See LICENSE)
#

'''
This module contains the helper functions for reading and writing to the additional rule database.
'''

import json

from dataclasses import dataclass
from rdflib import URIRef
from typing import Optional

from . import setting

from .exception import ParseError


def init_default():
    '''
    Read the rule database, using the information from setting and write it back (merge it) to setting.
    '''
    for rule_db_filename in setting.RULE_DB:
        try:
            with open(rule_db_filename, 'r') as f:
                extra_rules = json.load(f)
                try:
                    extra_data_rules = _segmented_parse(extra_rules['data_rules'], _parse_data_rule_graph)
                    setting.INJECTED_DATA_RULE = setting.INJECTED_DATA_RULE | extra_data_rules
                except KeyError:
                    pass
                try:
                    extra_imported_rules = _segmented_parse(extra_rules['imported_rules'], _parse_imported_rule_graph)
                    setting.INJECTED_IMPORTED_RULE = setting.INJECTED_IMPORTED_RULE | extra_imported_rules
                except KeyError:
                    pass
                try:
                    extra_flow_rules = _segmented_parse(extra_rules['flow_rules'], _parse_flow_rule_graph)
                    setting.INJECTED_FLOW_RULE = setting.INJECTED_FLOW_RULE | extra_flow_rules
                except KeyError:
                    pass

                try:
                    links = _parse_link(extra_rules['link'])
                    setting.LINK.extend(links)
                except KeyError:
                    pass
        except FileNotFoundError:
            pass

def _segmented_parse(section, f_parse_graph):
    rules = {}
    try:
        try:
            rules[None] = f_parse_graph(section[''])
        except KeyError:
            pass
        for graph in filter(lambda k: k != '', section.keys()):
            try:
                rules[URIRef(graph)] = f_parse_graph(section[graph])
            except KeyError:
                pass
    except Exception as e:
        raise ParseError(e)
    return rules

def _parse_data_rule_graph(section_graph):
    rules = {}
    try:
        section_graph_uri = section_graph['uri']
        for uri, data_rule_str in section_graph_uri.items():
            rules[URIRef(uri)] = data_rule_str
    except KeyError:
        pass
    return rules

def _parse_imported_rule_graph(section_graph):
    rules = {}
    try:
        section_graph_uri = section_graph['uri']
        for uri, data_rule_str in section_graph_uri.items():
            rules[URIRef(uri)] = data_rule_str
    except KeyError:
        pass
    try:
        section_graph_function = section_graph['function']
        for function, data_rule_str in section_graph_function.items():
            rules[function] = data_rule_str
    except KeyError:
        pass
    return rules

_parse_flow_rule_graph = _parse_imported_rule_graph  # It works fine because imported rules and flow rules share the same schema, and we are not parsing the rules themselves.


@dataclass
class Link:
    from_graph: Optional[URIRef]
    from_uri: URIRef
    to_graph: Optional[URIRef]
    to_uri: URIRef

    def new(from_graph, from_uri, to_graph, to_uri):
        from_graph = URIRef(from_graph) if from_graph else None
        from_uri = URIRef(from_uri)
        to_graph = URIRef(to_graph) if to_graph else None
        to_uri = URIRef(to_uri)
        return Link(from_graph, from_uri, to_graph, to_uri)


def _parse_link(section):
    links = []
    for from_graph, sec1 in section.items():
        for from_uri, to_section in sec1.items():
            assert len(to_section) == 1
            for to_graph, to_uri in to_section.items():
                links.append(Link.new(from_graph, from_uri, to_graph, to_uri))
    return links


def find_upstream_in_link(to_graph, to_uri):
    best_match = None
    for link in setting.LINK:
        if link.to_uri == to_uri:
            if link.to_graph:
                if link.to_graph == to_graph:
                    best_match = link
                else:
                    continue
            else:
                if not best_match:
                    best_match = link
    return best_match

def get_rule_from_link(to_graph, to_uri):
    link = find_upstream_in_link(to_graph, to_uri)
    if link:
        try:
            if link.from_graph in setting.INJECTED_DATA_RULE:
                return setting.INJECTED_DATA_RULE[link.from_graph][link.from_uri]
        except KeyError:
            try:
                return setting.INJECTED_DATA_RULE[None][link.from_uri]
            except KeyError:
                pass
    return None


def update_db_default(graph: 'GraphWrapper') -> None:
    '''
    Update the database with the new data rules obtained from the reasoner. Note this should be called after performing the reasoning.
    TODO: Handle data-streaming too.
    '''
    if setting.DB_WRITE_TO is None:
        return

    data_rules = {}
    for data in graph.data():
        data_rule = graph.get_data_rule(data)
        if data_rule:
            data_rules[str(data)] = data_rule.dump()

    out_db_filename = setting.RULE_DB[-1] if setting.DB_WRITE_TO == True else setting.DB_WRITE_TO
    db_rules = {}
    try:
        with open(out_db_filename, 'r') as f:
            db_rules = json.load(f)
    except FileNotFoundError:
        pass
    if 'data_rules' not in db_rules:
        db_rules['data_rules'] = {}
    if '' not in db_rules['data_rules']:
        db_rules['data_rules'][''] = {}
    db_rules['data_rules'][''].update(data_rules)
    with open(out_db_filename, 'w') as f:
        f.write(json.dumps(db_rules, indent=4))

