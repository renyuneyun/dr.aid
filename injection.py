#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/02/04 10:49:31
#   License :   Apache 2.0 (See LICENSE)
#

'''
This module contains the definitions and functions to deal with rule injections. The injection is populated by calling relevant functions in `rule_database_helper`.
'''

from dataclasses import dataclass
from rdflib import URIRef
from typing import Optional

from . import setting


@dataclass
class Link:
    from_graph: Optional[URIRef]
    from_uri: URIRef
    to_graph: Optional[URIRef]
    to_uri: URIRef


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


