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

from rdflib import URIRef

from . import setting

from .exception import ParseError


def init_default():
    '''
    Read the rule database, using the information from setting and write it back (merge it) to setting.
    '''
    try:
        with open(setting.RULE_DB, 'r') as f:
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

