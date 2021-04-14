'''
The wrapper class for the data-flow graph.
Details about prolog_handle and sparql_handle should be hid by this class.
'''

import functools

from dataclasses import dataclass
from networkx import MultiDiGraph
from pprint import pformat
from rdflib import Literal, URIRef
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
from typing import Callable, Dict, Iterable, List, Optional, Union

import logging
logger = logging.getLogger(__name__)

from . import rdf_helper as rh
from . import rule as rs
from . import injection
from . import sparql_helper as sh

from .exception import ForceFailedException, IllegalCaseError, IllegalStateError
from .rdf_helper import one_or_none
from .rule import DataRuleContainer, FlowRule, PortedRules
from .setting import IMPORT_PORT_NAME
from .sparql_helper import ComponentInfo


@dataclass
class ComponentAugmentation:
    id: URIRef
    rules: PortedRules


K_FUNCTION = 'function'


def virtual_port_for_import(component: URIRef, vport_name: Optional[str]) -> str:
    if vport_name is None:
        vport_name = IMPORT_PORT_NAME
    return f"{str(component)}#{vport_name}"


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


def trim_port_name(port_name: str, function: str):
    if port_name.startswith(function):
        port_name = port_name[len(function)+1:]  # The `/` after the function name is also removed
    return port_name


class GraphWrapper:

    @classmethod
    def from_cwl(cls, s_helper):
        return cls(s_helper, streaming=False)

    @classmethod
    def from_sprov(cls, s_helper, subgraph):
        return cls(s_helper, subgraph=subgraph)


    def require_data(f):
        '''
        Indicates and checks the function {f} requires data to be explicitly represented
        '''
        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            if self._data_streaming:
                raise IllegalStateError('This function requires data to be explicitly represented.')
            ret = f(self, *args, **kwargs)
            return ret
        return wrapper


    def __init__(self, s_helper, subgraph=None, streaming=True):
        self.s_helper = s_helper
        self.subgraph = subgraph
        if subgraph:  # Currently only used by SProvHelper
            self.s_helper.set_graph(subgraph)
        self._data_streaming = streaming
        self.rdf_graph = s_helper.get_graph_dependency_with_port()
        logger.debug('rdf_graph: %s', self.rdf_graph)

        # Put all component info into the graph
        components_info = self.s_helper.get_components_info(self.components())
        for component_info in components_info:
            info_dict = component_info.par
            info_dict[K_FUNCTION] = component_info.function
            rh.put_component_info(self.rdf_graph, component_info.id, info_dict)
        logger.debug("all_component_info: %s", pformat(components_info))

        self._virtual_process = []
        self.info = {}

    def is_data_streaming(self) -> bool:
        return self._data_streaming

    def components(self) -> List[URIRef]:
        return list(rh.components(self.rdf_graph))

    def data(self) -> List[URIRef]:
        return list(rh.data(self.rdf_graph))

    def data_without_derive(self, bundled=False) -> List[URIRef]:
        '''
        @param bundled: If set to True, when multiple data belong to the same "bundle" (from the same source to the same target), then only one of them is kept in the result.
        '''
        lst = []
        for d in self.data():
            if self.data_from(d) is None:
                lst.append(d)
        if bundled:
            mapped = {}
            for d in lst:
                targets = set(self.data_to(d))
                if targets in mapped:
                    continue
                mapped[targets] = d
            lst = list(mapped.values())
        return lst

    def data_without_consume(self, bundled=False) -> List[URIRef]:
        lst = []
        for d in self.data():
            if len(self.data_to(d)) == 0:
                lst.append(d)
        if bundled:
            mapped = {}
            for d in lst:
                source = self.data_from(d)
                assert source
                if source in mapped:
                    continue
                mapped[source] = d
            lst = list(mapped.values())
        return lst

    def port_without_consume(self) -> List[URIRef]:
        '''
        Similar to data_without_consume, but only ports. This is normally useful only for data-streaming workflows.
        '''
        lst = []
        for component in self.components():
            for port in self.output_ports(component):
                if len(self.downstream_of_output_port(port)) == 0:
                    lst.append(port)
        return lst

    def input_ports(self, component: URIRef) -> List[URIRef]:
        return list(rh.input_ports(self.rdf_graph, component))

    def output_ports(self, component: URIRef) -> List[URIRef]:
        return list(rh.output_ports(self.rdf_graph, component))

    def data_from(self, data: URIRef) -> Optional[URIRef]:
        return rh.data_output_from(self.rdf_graph, data, self._data_streaming)

    def data_to(self, data: URIRef) -> List[URIRef]:
        return list(rh.data_input_to(self.rdf_graph, data, self._data_streaming))

    def upstream_of_input_port(self, input_port: URIRef) -> List[URIRef]:
        '''
        Retrieve the upstream of the input port `input_port`, may be port if data-streaming, or data if file-oriented.
        TODO: Make it only one upstream, or handle multiple upstreams in Prolog
        '''
        if self._data_streaming:
            return self.upstream_port(input_port)
        else:
            return self.upstream_data(input_port)

    def downstream_of_output_port(self, output_port: URIRef) -> List[URIRef]:
        '''
        Similar to `upstream_of_input_port`, but gets the downstream of the `output_port`
        For file-oriented workflows (e.g. CWLProv), the downstream list contains either 0 or 1 elements.
        '''
        if self._data_streaming:
            return self.downstream_port(output_port)
        else:
            return [self.downstream_data(output_port)]

    def upstream_port(self, input_port: URIRef) -> List[URIRef]:
        '''
        Retrieve the upstream port of the input port `input_port`. Currently it assumes data streaming.
        TODO: Go back to the ports which produced the data (may not be needed)
        TODO: Make it only one upstream, or handle multiple upstreams in Prolog
        '''
        output_ports = []
        for ci, connection in enumerate(rh.connections_to_port(self.rdf_graph, input_port)):
            output_port = rh.one_or_none(rh.output_ports_with_connection(self.rdf_graph, connection))  # Every connection has exactly one OutputPort (or none)
            if output_port:
                output_ports.append(output_port)
        return output_ports

    def downstream_port(self, output_port: URIRef) -> List[URIRef]:
        '''
        Similar to `upstream_port`, but gets the downstream input ports of the `output_port`
        '''
        input_ports = []
        for connection in rh.connections_from_port(self.rdf_graph, output_port):
            input_port = rh.one_or_none(rh.connection_targets(self.rdf_graph, connection))
            if input_port:
                input_ports.append(input_port)
        return input_ports

    def upstream_data(self, input_port: URIRef) -> List[URIRef]:
        return list(rh.data_to_port(self.rdf_graph, input_port, self._data_streaming))

    def downstream_data(self, output_port: URIRef) -> Optional[URIRef]:
        return rh.data_from_port(self.rdf_graph, output_port, self._data_streaming)

    def component_of_port(self, port: URIRef) -> URIRef:
        if rh.is_input_port(self.rdf_graph, port):
            return rh.input_to(self.rdf_graph, port)
        elif rh.is_output_port(self.rdf_graph, port):
            return rh.output_from(self.rdf_graph, port)
        else:
            raise IllegalCaseError('The URI {} is neither input port or output port.'.format(port))

    # def name_of_component(self, component: URIRef) -> str:
    #     pass

    def name_of_port(self, port: URIRef) -> str:
        return str(rh.name(self.rdf_graph, port))

    def unique_name_of_port(self, port: URIRef) -> str:
        component = self.component_of_port(port)
        return f"{str(component)}#{self.name_of_port(port)}"

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
        if not batches:
            batches = [self.components()]
        if self._virtual_process:
            batches.append(self._virtual_process)
        return batches

    def initial_components(self) -> List[URIRef]:
        return self.component_to_batches()[0]

    def set_flow_rules(self, flow_rules: Dict[URIRef, str]) -> None:
        for component, fr in flow_rules.items():
            rh.set_flow_rule(self.rdf_graph, component, Literal(fr))

    def set_data_rules(self, data_rules: Dict[URIRef, DataRuleContainer]) -> None:
        for node, data_rule in data_rules.items():
            rh.insert_rule(self.rdf_graph, node, data_rule)

    def set_imported_rules(self, imported_rules: Dict[URIRef, Dict[str, DataRuleContainer]]) -> None:
        for component, dr_dic in imported_rules.items():
            input_ports = self.input_ports(component)
            for port, dr in dr_dic.items():
                if not port:
                    assert IMPORT_PORT_NAME not in input_ports
                else:
                    assert port not in input_ports
            rh.insert_imported_rule(self.rdf_graph, component, dr_dic)

    def get_imported_rules(self, component: URIRef) -> Dict[str, DataRuleContainer]:
        return rh.imported_rule(self.rdf_graph, component)

    def get_data_rule_of_port(self, port: URIRef) -> Optional[DataRuleContainer]:
        '''
        May be redundant with other get_data_rule_.
        '''
        return rh.rule(self.rdf_graph, port)

    def get_data_rule_of_data(self, data: URIRef) -> Optional[DataRuleContainer]:
        '''
        May be redundant with other get_data_rule_.
        '''
        rule = rh.rule(self.rdf_graph, data)
        if rule:
            return rule
        graph_id = URIRef(self.subgraph) if self.subgraph else None
        return injection.get_rule_from_link(graph_id, data)

    def get_data_rule(self, node: URIRef) -> Optional[DataRuleContainer]:
        '''
        @param node: It may be a data item or a port. Currently no exceptions is raised if otherwise.
        '''
        if rh.is_data(self.rdf_graph, node):
            return self.get_data_rule_of_data(node)
        else:
            return self.get_data_rule_of_port(node)

    def get_data_rules(self, component: URIRef, ports: Optional[List[URIRef]]=None, ensure_name_uniqueness=True) -> Dict[URIRef, DataRuleContainer]:
        '''
        Obtains the data rules for every input port of the component. This information is then used to do flow rule reasoning.
        @param ensure_name_uniqueness: See also `get_flow_rule`
        '''
        input_rules = {}
        if not ports:
            ports = self.input_ports(component)
        for input_port in ports:
            input_port_name = self.unique_name_of_port(input_port) if ensure_name_uniqueness else self.name_of_port(input_port)
            rules = []
            for upstream in self.upstream_of_input_port(input_port):
                rule = self.get_data_rule(upstream)
                if rule:
                    rules.append(rule)
                    logger.debug("Component %s :: input port %s receives rule, with %s", component, input_port_name, rule.summary())
            if rules:
                merged_rule = DataRuleContainer.merge(rules[0], *rules[1:])
                input_rules[input_port_name] = merged_rule
            else:
                logger.info("Component %s :: input port %s receives no rule", component, input_port_name)

        return input_rules

    def get_flow_rule(self, component: URIRef, force=False, ensure_name_uniqueness=True) -> FlowRule:
        '''
        If `force` is `True` and if the specified `component` does not have flow rule defined, an exception will be raised. If `force` is `False` and if the specified `component` does not have flow rule defined, the default flow will be composed and returned.
        If `ensure_name_uniqueness` is `True`, the port identifiers will be converted to the corresponding (graph-globally) unique identifiers. It is no harm to use it everywhere, with the only drawback of (minor) reduced performance.
        '''
        flow_rule = rh.flow_rule(self.rdf_graph, component)
        if not flow_rule:
            if force: raise ForceFailedException()
            input_ports = list(map(self.unique_name_of_port, self.input_ports(component)))
            output_ports = list(map(self.unique_name_of_port, self.output_ports(component)))
            # if has_imported_rule:  # We assume only components which do not have inputs or rules will have imported rules
            # It's no harm to have an extra rule for imported port -- it simply does nothing
            for vport_name in self.get_imported_rules(component):  # See comment two lines above
                input_ports.append(virtual_port_for_import(component, vport_name))
            flow_rule = rs.DefaultFlow(input_ports, output_ports)
        if flow_rule:
            component_info = one_or_none(self.component_info(component))
            function_name = component_info.function if component_info else None
            name_map = {}  # Here we assume local uniqueness of port names. TODO: local-uniqueness of input ports and output ports only
            for port in self.input_ports(component) + self.output_ports(component):
                name = self.name_of_port(port)
                long_name = self.unique_name_of_port(port)
                name_map[name] = long_name
                if function_name:
                    short_name = trim_port_name(name, function_name)
                    name_map[short_name] = long_name
            for vport_name in self.get_imported_rules(component):
                internal_name = virtual_port_for_import(component, vport_name)
                name_map[vport_name] = internal_name
            flow_rule.set_name_map(name_map)
        return flow_rule

    def add_virtual(self, action: str):
        nodes = []
        if self.is_data_streaming():
            for port in self.port_without_consume():
                node = rh.insert_virtual_process(self.rdf_graph, port, action)
                nodes.append(node)
        else:
            for data in self.data_without_consume():
                port = self.data_from(data)
                assert port is not None
                node = rh.insert_virtual_process(self.rdf_graph, port, action, via_data=data)
                nodes.append(node)
        self._virtual_process.extend(nodes)

    def set_purpose(self, purpose: str):
        self.info['purpose'] = purpose

    def get_graph_info(self) -> Dict[str, str]:
        return self.s_helper.get_graph_info()


    def apply_augmentation(self, augmentations: List[ComponentAugmentation]) -> None:
        logger.debug(f"Augmentation has {len(augmentations)} components")
        augmentation_dict = {}
        for aug in augmentations:
            component = aug.id
            augmentation_dict[component] = aug.rules
        self._apply_augmentation(augmentation_dict)

    def _apply_augmentation(self, augmentations: Dict[URIRef, PortedRules]) -> None:
        '''
        @param ensure_name_uniqueness: See `get_flow_rule`
        '''
        for component, ported_rules in augmentations.items():
            logger.debug(f"Augmentation for component {component}: {ported_rules}")
            for out_port in self.output_ports(component):
                port_name = self.name_of_port(out_port)
                if port_name in ported_rules:
                    rule = ported_rules[port_name]
                    if rule:
                        if self._data_streaming:
                            self.set_data_rules({out_port: rule})
                        else:
                            data = self.downstream_data(out_port)
                            if data:
                                self.set_data_rules({data: rule})
                else:
                    logger.warning("Augmentation for {} does not contain OutPort {}".format(component, port_name))

