#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/25 15:15:44
#   License :   Apache 2.0 (See LICENSE)
#

'''
This module contains useful utils to visualise the graph
'''

import pygraphviz as pgv

from . import rdf_helper as rh


def _clean_name(ref):
    name = str(ref)
    name = name[name.find('#')+1:]
    name = name[:name.find('_orfeus-as')]
    name = name[:name.find('_taastrup')]
    return name


class _NameId(object):

    def __init__(self):
        self.counter = 0
        self.map = {}

    def __getitem__(self, *name):
        assert len(name) > 0
        name = str(name)
        if name not in self.map:
            self.map[name] = self.counter
            self.counter += 1
        return self.map[name]


class GraphBuilder(object):

    def __init__(self, rdf_graph):
        self._rdf_graph = rdf_graph

        self.G = pgv.AGraph(directed=True, rankdir='LR')

        self._ni = _NameId()
        self._nm = {}

        self._components()

    def _components(self):
        for component in rh.components(self._rdf_graph):
            cid = self._ni[component]
            cluster_name = "cluster{}".format(cid)
            sg = self.G.add_subgraph(name=cluster_name, label=_clean_name(component))
            self._nm[component] = sg
            isg = sg.add_subgraph(rank='same')
            iports = []
            for input_port in rh.input_ports(self._rdf_graph, component):
                iportName = rh.name(self._rdf_graph, input_port)
                isg.add_node(self._ni[component, iportName], label=iportName)
                iports.append(iportName)
            oports = []
            osg = sg.add_subgraph(rank='same')
            for output_port in rh.output_ports(self._rdf_graph, component):
                oportName = rh.name(self._rdf_graph, output_port)
                osg.add_node(self._ni[component, oportName], label=oportName)
                oports.append(oportName)
            if iports and oports:
                sg.add_edge(self._ni[component, iports[0]], self._ni[component, oports[0]], style = 'invis')
        return self

    def data_flow(self):
        for component in rh.components(self._rdf_graph):
            sg = self._nm[component]
            for output_port in rh.output_ports(self._rdf_graph, component):
                oportName = rh.name(self._rdf_graph, output_port)
                oportNode = sg.get_node(self._ni[component, oportName])
                for connection in rh.connections(self._rdf_graph, output_port):
                    for input_port in rh.connection_targets(self._rdf_graph, connection):
                        iportName = rh.name(self._rdf_graph, input_port)
                        tcomponent = rh.input_to(self._rdf_graph, input_port)
                        tsg = self._nm[tcomponent]
                        iportNode = tsg.get_node(self._ni[tcomponent, iportName])
                        self.G.add_edge(oportNode, iportNode)
        return self

    def rules(self):
        for component in rh.components(self._rdf_graph):
            sg = self._nm[component]
            for output_port in rh.output_ports(self._rdf_graph, component):
                oportName = rh.name(self._rdf_graph, output_port)
                oportNode = sg.get_node(self._ni[component, oportName])
                rule = rh.rule(self._rdf_graph, output_port)
                if rule:
                    ruleNode = self._ni[component, oportName, rule]
                    sg.add_node(ruleNode, label=str(rule))
                    self.G.add_edge(oportNode, ruleNode)
            imported_rule = rh.imported_rule(self._rdf_graph, component)
            if imported_rule:
                ruleNode = self._ni[component, 'imported_rule_data']
                self.G.add_node(ruleNode, label=imported_rule.dump())
                connectedNode = self._ni[component, 'imported_rule']
                sg.add_node(connectedNode, label='imported')
                self.G.add_edge(ruleNode, connectedNode)
        return self

    def build(self):
        return self.G


def draw_to_file(G, filename):
    G.layout('dot')
    G.draw(filename)

