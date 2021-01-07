'''
The wrapper class for the data-flow graph.
Details about prolog_handle and sparql_handle should be hid by this class.
'''


from networkx import MultiDiGraph
from pprint import pformat
from rdflib import Literal, URIRef
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
from typing import Callable, Dict, Iterable, List, Optional, Union

import logging
logger = logging.getLogger(__name__)

from . import rdf_helper as rh
from . import rule as rs
from . import sparql_helper as sh

from .rdf_helper import IMPORT_PORT_NAME
from .rule import DataRuleContainer, FlowRule, PortedRules
from .setting import virtual_port_for_import
from .sparql_helper import ComponentInfo


K_FUNCTION = 'function'


def graph_into_batches(graph: MultiDiGraph) -> List[List[URIRef]]:
    g = graph.copy()
    # for node in nx.algorithms.dag.topological_sort(g):
    ret: List[List[URIRef]] = []
    while g:
        lst = []
        for node in g:
            if g.in_degree(node) == 0:
                lst.append(node)
        for node in lst:
            g.remove_node(node)
        ret.append(lst)
    return ret


class GraphWrapper:

    @classmethod
    def from_cwl(cls, s_helper):
        return cls(s_helper)

    @classmethod
    def from_sprov(cls, s_helper, subgraph):
        return cls(s_helper, subgraph=subgraph)


    def __init__(self, s_helper, subgraph=None):
        self.s_helper = s_helper
        self.subgraph = subgraph
        if subgraph:  # Currently only used by SProvHelper
            self.s_helper.set_graph(subgraph)
        self.rdf_graph = s_helper.get_graph_dependency_with_port()
        logger.debug('rdf_graph: %s', self.rdf_graph)

        # Put all component info into the graph
        components_info = self.s_helper.get_components_info(self.components())
        for component_info in components_info:
            info_dict = component_info.par
            info_dict[K_FUNCTION] = component_info.function
            rh.put_component_info(self.rdf_graph, component_info.id, info_dict)
        logger.debug("all_component_info: %s", pformat(components_info))

    def components(self) -> List[URIRef]:
        return list(rh.components(self.rdf_graph))

    def input_ports(self, component: URIRef) -> List[URIRef]:
        return rh.input_ports(self.rdf_graph, component)

    def output_ports(self, component: URIRef) -> List[URIRef]:
        return rh.output_ports(self.rdf_graph, component)

    def upstream_of_input_port(self, input_port: URIRef) -> List[URIRef]:
        '''
        Retrieve the upstream of the input port `input_port`. Currently the upstream is the output port.
        TODO: Make upstream the data where necessary
        TODO: Make it only one upstream, or handle multiple upstreams in Prolog
        '''
        output_ports = []
        for ci, connection in enumerate(rh.connections_to_port(self.rdf_graph, input_port)):
            output_port = rh.one_or_none(rh.output_ports_with_connection(self.rdf_graph, connection))  # Every connection has exactly one OutputPort (or none)
            if output_port:
                output_ports.append(output_port)
        return output_ports

    def downstream_of_output_port(self, output_port: URIRef) -> List[URIRef]:
        '''
        Similar to `upstream_of_input_port`, but gets the downstream input ports of the `output_port`
        '''
        input_ports = []
        for connection in rh.connections_from_port(self.rdf_graph, output_port):
            input_port = rh.one(rh.connection_targets(self.rdf_graph, connection))
            input_ports.append(input_port)
        return input_ports

    def component_of_input_port(self, input_port: URIRef) -> URIRef:
        return rh.input_to(self.rdf_graph, input_port)

    # def name_of_component(self, component: URIRef) -> str:
    #     pass

    def name_of_port(self, port: URIRef) -> str:
        return str(rh.name(self.rdf_graph, port))

    def component_info(self, components: Optional[Union[URIRef, List[URIRef]]]=None) -> List[ComponentInfo]:
        '''
        Get the specific information of the selected `components`, but not its ports (may subject to change)
        Return a list of `ComponentInfo` of the chosen `components`, otherwise all components.
        '''
        if isinstance(components, URIRef):
            components = [components]
        if not components:
            components = self.components()
        components_info = []
        for component in components:
            info_dict = rh.component_info(self.rdf_graph, component)
            function = info_dict[K_FUNCTION] if K_FUNCTION in info_dict else None
            del info_dict[K_FUNCTION]
            components_info.append(ComponentInfo(component, function, info_dict))
        return components_info

    def component_to_batches(self) -> List[List[URIRef]]:
        rdf_component_graph = self.s_helper.get_graph_component()
        component_graph = rdflib_to_networkx_multidigraph(rdf_component_graph)
        batches = graph_into_batches(component_graph)
        return batches

    def initial_components(self) -> List[URIRef]:
        return self.component_to_batches()[0]

    def set_flow_rules(self, flow_rules: Dict[URIRef, str]) -> None:
        for component, fr in flow_rules.items():
            rh.set_flow_rule(self.rdf_graph, component, Literal(fr))

    def set_imported_rules(self, imported_rules: Dict[URIRef, DataRuleContainer]) -> None:
        for component, dr in imported_rules.items():
            input_ports = self.input_ports(component)
            assert IMPORT_PORT_NAME not in input_ports
            rh.insert_imported_rule(self.rdf_graph, component, dr)

    def get_imported_rules(self, component: URIRef) -> Optional[DataRuleContainer]:
        return rh.imported_rule(self.rdf_graph, component)

    def get_data_rule_of_port(self, port: URIRef) -> Optional[DataRuleContainer]:
        return rh.rule(self.rdf_graph, port)

    def get_data_rules(self, component: URIRef, ports: Optional[List[URIRef]]=None) -> Dict[URIRef, DataRuleContainer]:
        input_rules = {}
        if not ports:
            ports = self.input_ports(component)
        for input_port in ports:
            input_port_name = self.name_of_port(input_port)
            rules = []
            for output_port in self.upstream_of_input_port(input_port):
                rule = self.get_data_rule_of_port(output_port)
                if rule:
                    rules.append(rule)
                    logger.debug("Component %s :: input port %s receives rule, with %s", component, input_port_name, rule.summary())
            if rules:
                merged_rule = DataRuleContainer.merge(rules[0], *rules[1:])
                input_rules[input_port_name] = merged_rule
            else:
                logger.info("Component %s :: input port %s receives no rule", component, input_port_name)
        return input_rules

    def get_flow_rule(self, component: URIRef, add_default=True, use_name=True) -> Optional[FlowRule]:
        '''
        If `add_default` is `True`, the return value will always be a valid FlowRule
        If `use_name` is `True`, the port identifiers in the flow rule will be their names, otherwise will be the string version of the port IRI
        '''
        flow_rule = rh.flow_rule(self.rdf_graph, component)
        if not flow_rule and add_default:
            if use_name:
                fn = self.name_of_port
            else:
                fn = str
            input_ports = list(map(fn, self.input_ports(component)))
            output_ports = list(map(fn, self.output_ports(component)))
            # if has_imported_rule:  # We assume only components which do not have inputs or rules will have imported rules
            # It's no harm to have an extra rule for imported port -- it simply does nothing
            input_ports.append(virtual_port_for_import(component))
            flow_rule = rs.DefaultFlow(input_ports, output_ports)
        return flow_rule


    def apply_augmentation(self, augmentations: Dict[URIRef, PortedRules]):
        for component, ported_rules in augmentations.items():
            logger.debug(f"Augmentation for component {component}: {augmentations}")
            for out_port in rh.output_ports(self.rdf_graph, component):
                port_name = str(rh.name(self.rdf_graph, out_port))
                if port_name in ported_rules:
                    rule = ported_rules[port_name]
                    if rule:
                        rh.insert_rule(self.rdf_graph, out_port, rule)
                else:
                    logger.warning("Augmentation for {} does not contain OutPort {}".format(component, port_name))

