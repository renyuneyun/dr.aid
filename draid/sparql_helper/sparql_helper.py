#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/09 18:32:59
#   License :   Apache 2.0 (See LICENSE)
#

'''
This module contains the helper classes for dealing with the RDF endpoint (for provenance) through SPARQL queries.
'''

from dataclasses import dataclass
import logging
import typing
from typing import Dict, List, Optional

from rdflib import Graph, URIRef
from SPARQLWrapper import SPARQLWrapper, JSON, XML, TURTLE

from draid import setting
from draid.names import T_REF
from draid.namespaces import NS

from . import query_sprov
from . import query_cwl

DEFAULT_PORT = ''


if typing.TYPE_CHECKING:
    from draid.graph_wrapper import GraphWrapper


@dataclass
class InitialInfo:
    par: List[str]
    data: Dict[str, List[str]]


@dataclass
class ComponentInfo:
    id: URIRef
    function: Optional[str]
    par: Dict[str, str]


logger = logging.getLogger(__name__)


def _rd(binding, target, safe=False):
    '''
    Read (to str)
    '''
    if not safe:
        return binding[target]['value']
    else:
        if target in binding:
            return binding[target]['value'], True
        else:
            return None, False


def _rdu(binding, target, safe=False):
    '''
    Read (to) URIRef
    '''
    if not safe:
        return URIRef(_rd(binding, target, safe))
    else:
        obj, real = _rd(binding, target, safe)
        if real:
            return URIRef(obj), real
        else:
            return obj, real


class Helper:

    def __init__(self, destination):
        self.sparql = SPARQLWrapper(destination)
        self.graph = None

    def _q(self, query: str) -> Dict:
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        return self.sparql.query().convert()

    def _c(self, query: str, return_format = XML) -> Graph:
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(return_format)
        self.sparql.setOnlyConneg(True)
        return self.sparql.query().convert()


class SProvHelper(Helper):
    q = query_sprov

    def __init__(self, destination):
        super().__init__(destination)

    def set_graph(self, graph: T_REF) -> None:
        self.graph = graph

    def get_wfe_graphs(self):
        ret = []
        results = self._q(self.q.Q(self.q.ALL_WFE_GRAPHS))
        for binding in results['results']['bindings']:
            g = _rdu(binding, 'g')
            ret.append(g)
        return ret

    def get_graph_info(self):
        ret = {}
        results = self._q(self.q.Q(self.q.F_GRAPH_START_TIME(self.graph)))
        for binding in results['results']['bindings']:
            startTime = _rd(binding, 'startTime')
            ret['startTime'] = startTime
        results = self._q(self.q.Q(self.q.F_GRAPH_USER(self.graph)))
        for binding in results['results']['bindings']:
            startTime = _rd(binding, 'user')
            ret['user'] = startTime
        return ret

    def get_initial_components(self):
        ret = []
        results = self._q(self.q.Q(self.q.F_COMPONENT_WITHOUT_INPUT_DATA(self.graph)))
        for binding in results['results']['bindings']:
            component = _rdu(binding, 'component')
            ret.append(component)
        return ret

    def get_components_function(self) -> Dict[URIRef, str]:
        ret = {}
        results = self._q(self.q.Q(self.q.F_COMPONENT_FUNCTION(self.graph)))
        for binding in results['results']['bindings']:
            component = _rdu(binding, 'component')
            f_name, real = _rd(binding, 'function_name', True)
            if not real:
                logger.warning("no function_name for component {}".format(component))
                continue
            ret[component] = f_name
        return ret

    def get_components_info(self, components: List[URIRef]) -> List[ComponentInfo]:
        component_function = self.get_components_function()
        info: Dict[URIRef, Dict[str, str]] = {com: {} for com in components}
        results = self._q(self.q.Q(self.q.F_COMPONENT_PARS_IN(self.graph, components)))
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

    def get_graph_dependency_with_port(self) -> Graph:
        return self._c(self.q.Q(self.q.F_C_DATA_DEPENDENCY_WITH_PORT(self.graph)))

    def get_graph_component(self) -> Graph:
        return self._c(self.q.Q(self.q.F_C_COMPONENT_GRAPH(self.graph)))


class CWLHelper(Helper):
    q = query_cwl

    def __init__(self, destination):
        super().__init__(destination)

    def _c(self, query: str):
        return super()._c(query, return_format=TURTLE)

    def get_graph_info(self):
        ret = {}
        results = self._q(self.q.Q(self.q.Q_GRAPH_START_TIME))
        for binding in results['results']['bindings']:
            startTime = _rd(binding, 'startTime')
            ret['startTime'] = startTime
        return ret


    def get_components_info(self, components: List[URIRef]) -> List[ComponentInfo]:
        def get_components_function(self) -> Dict[URIRef, str]:
            ret = {}
            results = self._q(self.q.Q(self.q.Q_COMPONENT_FUNCTION))
            for binding in results['results']['bindings']:
                component = _rdu(binding, 'component')
                f_name, real = _rd(binding, 'function_name', True)
                if not real:
                    logger.warning("no function_name for component {}".format(component))
                    continue
                ret[component] = f_name
            return ret

        component_function = get_components_function(self)
        info: Dict[URIRef, Dict[str, str]] = {com: {} for com in components}
        results = self._q(self.q.Q(self.q.F_COMPONENT_PARS_IN(self.graph, components)))
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

    def get_graph_dependency_with_port(self) -> Graph:
        results = self._c(self.q.Q(self.q.C_DATA_DEPENDENCY_WITH_PORT(self.graph)))
        g = Graph()
        g.parse(data=results, format="turtle")
        return g

    def get_graph_component(self) -> Graph:
        results = self._c(self.q.Q(self.q.C_COMPONENT_GRAPH(self.graph)))
        g = Graph()
        g.parse(data=results, format="turtle")
        return g


class AugmentedGraphHelper(Helper):

    def __init__(self, destination):
        super().__init__(destination)

    def write_transformed_graph(self, graph: 'GraphWrapper'):
        '''
        Create / Prune a new graph dedicated to store the old graph + initial rules
        '''
        # TODO
        logger.warning("<write_transformed_graph> Not implemented yet")
        for s, p, o in graph.rdf_graph:
            if p == NS['mine']['rule']:
                logger.info("{} {} {}".format(s, p, o))


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


def get_initial_info(sparql) -> Dict[URIRef, InitialInfo]:
    sparql.setQuery(q.Q(q.INITIAL_COMPONENT_AND_DATA_AND_PAR))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    initial_info_map: Dict[URIRef, InitialInfo] = {}
    for binding in results['results']['bindings']:
        component = _rd(binding, 'value')
        if component not in initial_info_map:
            initial_info_map[component] = InitialInfo([], {})
        info = initial_info_map[component]
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
    return initial_info_map

