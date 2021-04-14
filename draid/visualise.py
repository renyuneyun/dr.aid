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

from pprint import pformat

from .exception import ForceFailedException
from .graph_wrapper import GraphWrapper, trim_port_name

logger = logging.getLogger(__name__)


def _clean_name(ref):
    name = str(ref)
    name = name[name.find('#')+1:]
    name = name[:name.find('_orfeus-as')]
    name = name[:name.find('_taastrup')]
    return name

def _function_name(graph, ref):
    return graph.component_info(ref)[0].function

def _component_label(graph, ref):
    function = _function_name(graph, ref)
    clean_name = _clean_name(ref)
    if not function:
        return clean_name
    else:
        return f"{clean_name}\\n[{function}]"


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
            function_name = _function_name(self._graph, component)
            sg = self.G.add_subgraph(name=cluster_name, label=_component_label(self._graph, component), style='striped')
            self._nm[component] = sg
            isg = sg.add_subgraph(rank='source')
            iports = []
            for input_port in self._graph.input_ports(component):
                iportName = self._graph.name_of_port(input_port)
                isg.add_node(self._ni[component, iportName], label=trim_port_name(iportName, function_name))
                iports.append(iportName)
            oports = []
            osg = sg.add_subgraph(rank='sink')
            for output_port in self._graph.output_ports(component):
                oportName = self._graph.name_of_port(output_port)
                osg.add_node(self._ni[component, oportName], label=trim_port_name(oportName, function_name))
                oports.append(oportName)
            if iports and oports:
                sg.add_edge(self._ni[component, iports[0]], self._ni[component, oports[0]], style = 'invis')
        return self

    def _get_node_port(self, port_uri, component=None):
        port_name = self._graph.name_of_port(port_uri)
        if not component:
            component = self._graph.component_of_port(port_uri)
        sg = self._nm[component]  # SubGraph
        return sg.get_node(self._ni[component, port_name])

    def data_flow(self):
        if self._graph.is_data_streaming():
            data_list = []
            data_list.extend(self._graph.data_without_derive(bundled=True))  # The initial data
            data_list.extend(self._graph.data_without_consume(bundled=True))  # The final output data
        else:
            data_list = self._graph.data()
        for data in data_list:
            dataNode = self._ni[data]
            node = self.G.add_node(dataNode, label=str(data), shape='oval')
            output_port = self._graph.data_from(data)
            if output_port:
                portNode = self._get_node_port(output_port)
                self.G.add_edge(portNode, dataNode)
            for input_port in self._graph.data_to(data):
                portNode = self._get_node_port(input_port)
                self.G.add_edge(dataNode, portNode)

        if self._graph.is_data_streaming():
            # Draw direct links from component A's output port to component B's input port -- this happens when there is no explicit data between them.
            for component in self._graph.components():
                sg = self._nm[component]
                for output_port in self._graph.output_ports(component):
                    oportName = self._graph.name_of_port(output_port)
                    oportNode = sg.get_node(self._ni[component, oportName])
                    for input_port in self._graph.downstream_of_output_port(output_port):
                    # for input_port in self._graph.downstream_port(output_port):
                        iportName = self._graph.name_of_port(input_port)
                        tcomponent = self._graph.component_of_port(input_port)
                        tsg = self._nm[tcomponent]
                        iportNode = tsg.get_node(self._ni[tcomponent, iportName])
                        self.G.add_edge(oportNode, iportNode)

        return self

    def rules(self):
        for component in self._graph.components():
            sg = self._nm[component]

            # Rules from output ports. This will effectively only annotate data-streaming provenance.
            for output_port in self._graph.output_ports(component):
                oportName = self._graph.name_of_port(output_port)
                oportNode = sg.get_node(self._ni[component, oportName])
                rule = self._graph.get_data_rule_of_port(output_port)
                if rule:  # If file-oriented, `rule` will be None
                    ruleNode = self._ni[component, oportName, rule]
                    self.G.add_node(ruleNode, label=rule.dump().replace('\n', '\\l'), shape='note')
                    self.G.add_edge(oportNode, ruleNode, arrowhead='none')

            imported_rules = self._graph.get_imported_rules(component)
            for vport_name, imported_rule in imported_rules.items():
                ruleNode = self._ni[component, 'imported_rule_data', vport_name]
                self.G.add_node(ruleNode, label=imported_rule.dump().replace('\n', '\\l'), shape='note')
                connectedNode = self._ni[component, 'imported_rule', vport_name]
                sg.add_node(connectedNode, label=vport_name, style='dashed', shape='egg')
                self.G.add_edge(ruleNode, connectedNode, style='tapered', penwidth=7, arrowtail='none', dir='forward', arrowhead='none')

        for data in self._graph.data():
            rule = self._graph.get_data_rule_of_data(data)
            # if not rule:  # Temporary until sorted out associating data rules with data
            #     output_port = self._graph.data_from(data)
            #     if output_port:
            #         rule = self._graph.get_data_rule_of_port(output_port)
            if rule:
                dataNode = self._ni[data]
                ruleNode = self._ni[component, data, rule]
                self.G.add_node(ruleNode, label=rule.dump().replace('\n', '\\l'), shape='note')
                self.G.add_edge(dataNode, ruleNode, arrowhead='none')

        return self

    def obligation(self):
        for component in self._graph.components():
            obs = self._acob.get(component)
            if obs:
                sg = self._nm[component]
                obNode = self._ni[sg, 'obligation']
                sg.add_node(obNode, label=pformat(obs).replace('\n', '\\l'), shape='folder')
        return self

    def flow_rules(self):
        for component in self._graph.components():
            try:
                rule = self._graph.get_flow_rule(component, force=True)
                sg = self._nm[component]
                frNodeId = self._ni[component, 'flowRule']
                sg.add_node(frNodeId, label=rule.dump().replace('\n', '\\n'), shape='cds')
            except ForceFailedException:  # We set `force=True`, so raising this exception means the component does not have explicit flow rule associated
                pass
        return self

    def build(self):
        return self.G


def draw_to_file(G, filename):
    G.layout('dot')
    G.draw(filename)

