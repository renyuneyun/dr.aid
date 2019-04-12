#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/09 18:32:59
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from dataclasses import dataclass
from rdflib import Graph, URIRef
from SPARQLWrapper import SPARQLWrapper, JSON, XML
from typing import Optional, List, Tuple, Dict
import logging

import queries as q
from namespaces import NS

from collections import namedtuple

InitialInfo = namedtuple('InitialInfo', ['par', 'data'])

DEFAULT_PORT = None


@dataclass
class ComponentInfo:
    id: URIRef
    function: str
    par: Dict[str, str]


logger = logging.getLogger('HELPER')
logger.setLevel(logging.INFO)


def _q(sparql: SPARQLWrapper, query: str) -> Dict:
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def _rd(binding, target, safe=False):
    if not safe:
        return binding[target]['value']
    else:
        if target in binding:
            return binding[target]['value'], True
        else:
            return None, False


def _rdu(binding, target, safe=False):
    if not safe:
        return URIRef(_rd(binding, target, safe))
    else:
        obj, real = _rd(binding, target, safe)
        if real:
            return URIRef(obj), real
        else:
            return obj, real


def get_initial_components(sparql):
    sparql.setQuery(q.Q(q.COMPONENT_WITHOUT_INPUT_DATA))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for binding in results['results']['bindings']:
        component = binding['component']
        value = component['value']
        yield value


def get_initial_components_and_output(sparql):
    ret = {}
    results = _q(sparql, q.Q(q.INITIAL_COMPONENT_AND_DATA))
    for binding in results['results']['bindings']:
        component = _rd(binding, 'component')
        if component not in ret:
            ret[component] = []
        data = _rd(binding, 'data_out')
        ret[component].append(data)
    return ret


def get_graph_component(sparql:SPARQLWrapper) -> Graph:
    sparql.setQuery(q.Q(q.C_COMPONENT_GRAPH))
    sparql.setReturnFormat(XML)
    return sparql.query().convert()


def get_graph_dependency_with_port(sparql: SPARQLWrapper) -> Graph:
    sparql.setQuery(q.Q(q.C_DATA_DEPENDENCY_WITH_PORT))
    sparql.setReturnFormat(XML)
    return sparql.query().convert()


def get_initial_info(sparql) -> Dict[URIRef, InitialInfo]:
    sparql.setQuery(q.Q(q.INITIAL_COMPONENT_AND_DATA_AND_PAR))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    initial_info: Dict[URIRef, InitialInfo] = {}
    for binding in results['results']['bindings']:
        component = _rd(binding, 'value')
        if component not in initial_info:
            initial_info[component] = InitialInfo([], {})
        info = initial_info[component]
        par, real = _rd(binding, 'par', True)
        if real:
            info.par.append(par)
        data, real = _rd(binding, 'data_out', True)
        if real:
            port = binding['port_out']['value'] if 'port_out' in binding else DEFAULT_PORT
            if port in info.data:
                info.data[port].append(data)
            else:
                info.data[port] = [data]
    return initial_info


def get_components_function(sparql: SPARQLWrapper) -> Dict[URIRef, str]:
    ret = {}
    results = _q(sparql, q.Q(q.COMPONENT_FUNCTION))
    for binding in results['results']['bindings']:
        component = _rdu(binding, 'component')
        f_name, real = _rd(binding, 'function_name', True)
        if not real:
            logger.warning("no function_name for component {}".format(component))
            continue
        ret[component] = f_name
    return ret


def get_components_info(sparql: SPARQLWrapper, components: List[URIRef]) -> List[ComponentInfo]:
    component_function = get_components_function(sparql)
    info: Dict[URIRef, Dict[str, str]] = {}
    #results = _q(sparql, q.Q(q.COMPONENT_PARS))
    query = q.Q(q.COMPONENT_PARS_IN(components))
    results = _q(sparql, query)
    for binding in results['results']['bindings']:
        component = _rdu(binding, 'component')
        if component not in info:
            info[component] = {}
        par = _rd(binding, 'par')
        pred = _rd(binding, 'pred')
        obj = _rd(binding, 'obj')
        info[component][pred] = obj
    ret = []
    for component, par in info.items():
        function_name = component_function[component]
        component_info = ComponentInfo(component, function_name, par)
        ret.append(component_info)
    return ret


def write_transformed_graph(sparql: SPARQLWrapper, graph: Graph):
    '''
    Create / Prune a new graph dedicated to store the old graph + initial rules
    '''
    # TODO
    for s, p, o in graph:
        if p == NS['mine']['rule']:
            logger.error("{} {} {}".format(s, p, o))

