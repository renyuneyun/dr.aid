#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/25 15:39:02
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from typing import Optional

from rdflib import Literal

from .namespaces import NS


def one(iterator):
    lst = list(iterator)
    assert len(lst) == 1
    return lst[0]


def one_or_none(iterator):
    lst = list(iterator)
    if len(lst) == 0:
        return None
    assert len(lst) == 1
    return lst[0]


def name(graph, subject):
    return one(graph.objects(subject, NS['mine']['name']))


def components(graph):
    return graph.subjects(NS['rdf']['type'], NS['s-prov']['Component'])


def output_ports(graph, component):
    return graph.objects(component, NS['mine']['hasOutPort'])


def input_ports(graph, component):
    return graph.subjects(NS['mine']['inputTo'], component)


def connections(graph, output_port):
    return graph.objects(output_port, NS['mine']['hasConnection'])


def connection_targets(graph, connection):
    return graph.objects(connection, NS['mine']['target'])


def input_to(graph, input_port):
    return one(graph.objects(input_port, NS['mine']['inputTo']))


def rule(graph, output_port) -> Optional[Literal]:
    return one_or_none(graph.objects(output_port, NS['mine']['rule']))

