#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/25 15:15:44
#   License :   Apache 2.0 (See LICENSE)
#

'''
This module contains useful utils to visualise the graph.
'''

import logging
import pygraphviz as pgv

from .exception import ForceFailedException
from .graph_wrapper import GraphWrapper

logger = logging.getLogger(__name__)


def _clean_name(ref):
    name = str(ref)
    name = name[name.find('#')+1:]
    name = name[:name.find('_orfeus-as')]
    name = name[:name.find('_taastrup')]
    return name

def _component_label(graph, ref):
    function = graph.component_info(ref)[0].function
    clean_name = _clean_name(ref)
    if not function:
        return clean_name
    else:
        return f"{clean_name}\n[{function}]"


class _NameId:

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


class GraphBuilder:

    def __init__(self, graph, activated_obligations={}):
        self._graph = graph
        self._acob = activated_obligations

        self.G = pgv.AGraph(directed=True, rankdir='LR')

        self._ni = _NameId()  # convert from keys to a unique identifier
        self._nm = {}  # map from keys to nodes (objects) in graph

        self._components()

    def _components(self):
        for component in self._graph.components():
            logger.debug('adding component %s as cluster', component)
            cid = self._ni[component] # Cluster ID
            cluster_name = "cluster{}".format(cid)
            sg = self.G.add_subgraph(name=cluster_name, label=_component_label(self._graph, component), style='striped')
            self._nm[component] = sg
            isg = sg.add_subgraph(rank='source')
            iports = []
            for input_port in self._graph.input_ports(component):
                iportName = self._graph.name_of_port(input_port)
                isg.add_node(self._ni[component, iportName], label=iportName)
                iports.append(iportName)
            oports = []
            osg = sg.add_subgraph(rank='sink')
            for output_port in self._graph.output_ports(component):
                oportName = self._graph.name_of_port(output_port)
                osg.add_node(self._ni[component, oportName], label=oportName)
                oports.append(oportName)
            if iports and oports:
                sg.add_edge(self._ni[component, iports[0]], self._ni[component, oports[0]], style = 'invis')
        return self

    def data_flow(self):
        for component in self._graph.components():
            sg = self._nm[component]
            for output_port in self._graph.output_ports(component):
                oportName = self._graph.name_of_port(output_port)
                oportNode = sg.get_node(self._ni[component, oportName])
                for input_port in self._graph.downstream_of_output_port(output_port):
                        iportName = self._graph.name_of_port(input_port)
                        tcomponent = self._graph.component_of_port(input_port)
                        tsg = self._nm[tcomponent]
                        iportNode = tsg.get_node(self._ni[tcomponent, iportName])
                        self.G.add_edge(oportNode, iportNode)
        return self

    def rules(self):
        for component in self._graph.components():
            sg = self._nm[component]
            for output_port in self._graph.output_ports(component):
                oportName = self._graph.name_of_port(output_port)
                oportNode = sg.get_node(self._ni[component, oportName])
                rule = self._graph.get_data_rule_of_port(output_port)
                if rule:
                    ruleNode = self._ni[component, oportName, rule]
                    self.G.add_node(ruleNode, label=rule.dump(), shape='note')
                    self.G.add_edge(oportNode, ruleNode, arrowhead='none')
            imported_rule = self._graph.get_imported_rules(component)
            if imported_rule:
                ruleNode = self._ni[component, 'imported_rule_data']
                self.G.add_node(ruleNode, label=imported_rule.dump(), shape='note')
                connectedNode = self._ni[component, 'imported_rule']
                sg.add_node(connectedNode, label='imported', style='dashed', shape='egg')
                self.G.add_edge(ruleNode, connectedNode, style='tapered', penwidth=7, arrowtail='none', dir='forward', arrowhead='none')
        return self

    def obligation(self):
        for component in self._graph.components():
            obs = self._acob.get(component)
            if obs:
                sg = self._nm[component]
                obNode = self._ni[sg, 'obligation']
                sg.add_node(obNode, label=str(obs), shape='folder')
        return self

    def flow_rules(self):
        for component in self._graph.components():
            try:
                rule = self._graph.get_flow_rule(component, force=True)
                sg = self._nm[component]
                frNodeId = self._ni[component, 'flowRule']
                sg.add_node(frNodeId, label=rule.dump(), shape='cds')
            except ForceFailedException:  # We set `force=True`, so raising this exception means the component does not have explicit flow rule associated
                pass
        return self

    def build(self):
        return self.G


def draw_to_file(G, filename):
    G.layout('dot')
    G.draw(filename)

