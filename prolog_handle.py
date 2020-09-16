from collections import defaultdict
import tempfile

from rdflib import Graph, URIRef
from typing import List, Dict, Iterable

from .proto import (
        dump,
        is_ac,
        obtain,
        )
from .rule import Attribute, AttributeCapsule, ObligationDeclaration, DataRuleContainer, FlowRule, PortedRules
from . import rdf_helper as rh

import pyswip

import logging
logger = logging.getLogger('prolog_handle')
logger.setLevel(logging.DEBUG)


PR_DIR = '.'  # Prolog Reasoning directory
prolog = pyswip.Prolog()  # pyswip doesn't support launching multiple Prolog instances (said to be the limition of swi-prolog). So I'm using different initial situations for different ones instead
prolog.consult(f"{PR_DIR}/prolog/flow_rule.pl")
_uniq_counter = 0


IGNORED_PORTS = [
        '_d4p_state'
        ]


def _pl_str(value):
    return f'"{value}"'

def _attr_id_for_prolog(attr_name, attr_ord):
    return f"{attr_name}{attr_ord}"

def dump_data_rule(drc: 'DataRuleContainer', port, situation='s0') -> str:
    s = ''
    for attrcap in drc._attrcaps:
        name = attrcap._name
        for i, attr in enumerate(attrcap._attrs):
            _name = attr.attributeName
            assert name == _name
            t = 'str'
            v = attr.hasValue.valueData or attr.hasValue.valueObject
            attr_id = _attr_id_for_prolog(name, i)
            s += f"attr({_pl_str(name)}, {_pl_str(t)}, {_pl_str(v)}, [{_pl_str(attr_id)}, {_pl_str(port)}], {situation}).\n"
    for ob in drc._rules:
        name = ob._name
        if ob._attribute:
            attr_name, attr_ord = ob._attribute
            attr_repr = "[{}, {}]".format(_pl_str(_attr_id_for_prolog(attr_name, attr_ord)), _pl_str(port))
        else:
            continue # TODO: support obligations without attributes
            attr_repr = 'null'
        ac = dump(ob._ac) or 'null'
        s += f"obligation({_pl_str(name)}, {attr_repr}, {_pl_str(ac)}, {_pl_str(port)}, {situation}).\n"
    return s

# def _dump_flow_rule(flow_rule: 'FlowRule') -> List[str]:
def pl_act_flow_rule(flow_rule: 'FlowRule') -> List[str]:
    lst = []
    for input_port, output_ports in flow_rule._conn.items():
        lst.append(f"pr({_pl_str(input_port)}, [{','.join(map(_pl_str, output_ports))}])")
    output_ports = set()
    for ports in flow_rule._conn.values():
        output_ports.update(ports)
    lst.extend([f"end({_pl_str(output)})" for output in output_ports])
    #TODO: edit and delete
    return lst

def pl_act_inter_process_connection(connections: Dict[str, str]) -> List[str]:
    lst = []
    for output_port, input_port in connections.items():
        lst.append(f"pr({_pl_str(output_port)}, [{_pl_str(input_port)}]):end({_pl_str(input_port)})")
    return lst


def query_of_flow_rule(flow_rule: 'FlowRule', situation_in='s0') -> str:
    situation_out='S1'
    act_seq = pl_act_flow_rule(flow_rule)
    s = f"do({':'.join(act_seq)}, {situation_in}, {situation_out})"
    return s, situation_out

def query_of_graph_flow_rules(rdf_graph: 'Graph', batches: List[List['URIRef']], flow_rules: Dict[URIRef, 'FlowRule'], situation_in='s0') -> str:
    act_seq_list = []
    for i, component_list in enumerate(batches):
        # next_components = batches[i+1]
        inter_process_connections = {}
        for component in component_list:
            act_seq = pl_act_flow_rule(flow_rules[component])
            if act_seq:  # TODO: What if no output?
                act_seq_list.append(act_seq)
            for output_port in rh.output_ports(rdf_graph, component):
                connections = list(rh.connections_from_port(rdf_graph, output_port))
                if len(connections) > 1:
                    logger.warning("Output port %s of component %s has %d (>1) output connections: %s. Connections to `d4p_state` will be discarded, but other unexpected ones will cause problems.", output_port, component, len(connections), connections)
                for connection in connections:
                    input_port = rh.one(rh.connection_targets(rdf_graph, connection))
                    input_name = str(rh.name(rdf_graph, input_port))
                    if input_name in IGNORED_PORTS:
                        continue
                    inter_process_connections[str(output_port)] = str(input_port)
        act_seq_inter_process = pl_act_inter_process_connection(inter_process_connections)
        if act_seq_inter_process:
            act_seq_list.append(act_seq_inter_process)
    logger.debug("Action sequence: %s", act_seq_list)
    s_list = []
    situation_count = 0
    situation_previous = 's0'
    for act_seq in act_seq_list:
        situation_count += 1
        situation_now = 'S' + str(situation_count)
        s = f"do({':'.join(act_seq)}, {situation_previous}, {situation_now})"
        situation_previous = situation_now
        s_list.append(s)
    s = f"{',!,'.join(s_list)}"
    return s, situation_previous

def query_of_attribute(situation_out='S1'):
    return f"attr(N, T, V, H, {situation_out})"

def query_of_obligation(situation_out='S1'):
    return f"obligation(Ob, Attr, Ac, P, {situation_out})"


def _parse_attribute(res_iter):
    attr_hist = {}
    ported_attrs = defaultdict(lambda : defaultdict(list))
    for r_attr in res_iter:
        hist = r_attr['H']
        port = hist[-1].decode()
        name = r_attr['N'].decode()
        attr = Attribute.instantiate(name, raw_attribute=r_attr['V'].decode())
        index = len(ported_attrs[port][name])
        ported_attrs[port][name].append(attr)
        t_hist = tuple(hist)
        if t_hist in attr_hist:
            logger.error("Attribute with history %s already existed. Previous value: %s :: New value: %s. Overriding.", t_hist, attr_hist[t_hist], (name, index))
        attr_hist[t_hist] = (name, index)
    logger.debug("Retrieved attributes from %d ports. Summary ({PORT: {ATTR-NAME: #-OF-ATTR}}): %s", len(ported_attrs), { port: {name: len(attrs[name]) for name in attrs} for port, attrs in ported_attrs.items() })
    # logger.debug("Attribute history: %s", attr_hist)
    return ported_attrs, attr_hist

def _parse_obligation(res_iter, attr_hist):
    ported_obs = defaultdict(list)
    for r_ob in res_iter:
        port = r_ob['P'].decode()
        ob = r_ob['Ob'].decode()
        attr = attr_hist[tuple(r_ob['Attr'])]
        ac = r_ob['Ac'].decode()
        if is_ac(ac):
            ac = obtain(ac)
        else:
            assert ac == 'null'
            ac = None
        ob = ObligationDeclaration(ob, attr, ac)
        ported_obs[port].append(ob)
    logger.debug("Retrieved obligations in %d ports. Summary ({PORT: #-OF-OBLIGATIONS}): %s", len(ported_obs), { port: len(obs) for port, obs in ported_obs.items() })
    return ported_obs

def _parse_result(prolog, q_sit, situation_out):
    q_attr = f"{q_sit}, !, {query_of_attribute(situation_out)}"
    q_ob = f"{q_sit}, !, {query_of_obligation(situation_out)}"
    ported_attrs, attr_hist = _parse_attribute(prolog.query(q_attr))
    ported_obs = _parse_obligation(prolog.query(q_ob), attr_hist)
    ported_drs = {}
    for port in set(ported_attrs) & set(ported_obs):
        obs = [ob for ob in ported_obs[port] if isinstance(ob, ObligationDeclaration)]
        attrs = [AttributeCapsule(name, attribute=attrs) for name, attrs in ported_attrs[port].items()]
        data_rule = DataRuleContainer(obs, attrs)
        ported_drs[port] = data_rule
    logger.debug("Recomposed data rules has %d elements", len(ported_drs))
    return ported_drs

def _do_prolog_common(data_rules_facts, q_sit, situation_out):
    global prolog

    tmp_dir = tempfile.mkdtemp()
    # with tempfile.TemporaryDirectory() as tmp_dir:
    reason_file = f"{tmp_dir}/reason_facts.pl"

    with open(reason_file, 'w') as f:
        f.write(data_rules_facts)
    prolog.consult(reason_file)

    with open(f"{tmp_dir}/query.pl", 'w') as f:
        f.write(q_sit)
        f.write('\n')
    logger.info("Prolog facts and query are recorded in: %s", tmp_dir)
    logger.debug("Rule facts:\n%s", data_rules_facts)
    logger.debug("Action sequence: %s", q_sit)

    ported_drs = _parse_result(prolog, q_sit, situation_out)
    return ported_drs

def dispatch(data_rules: 'Dict[str, DataRuleContainer]', flow_rule: 'FlowRule') -> 'PortedRules':
    global _uniq_counter
    s0 = f"s{_uniq_counter}"
    _uniq_counter += 1

    data_rule_facts = ''
    for port, data_rule in data_rules.items():
        s = dump_data_rule(data_rule, port, situation=s0)
        data_rule_facts += s

    q_sit, situation_out = query_of_flow_rule(flow_rule, situation_in=s0)

    ported_drs = _do_prolog_common(data_rule_facts, q_sit, situation_out)
    return ported_drs

def dispatch_all(rdf_graph: Graph, batches: List[List[URIRef]], component_data_rules: Dict[URIRef, Dict[str, DataRuleContainer]], flow_rules: Dict[str, FlowRule]) -> PortedRules:
    global _uniq_counter
    s0 = f"s{_uniq_counter}"
    _uniq_counter += 1

    data_rule_facts = ''
    for component, data_rules in component_data_rules.items():
        for port, data_rule in data_rules.items():
            s = dump_data_rule(data_rule, port, situation=s0)
            data_rule_facts += s

    q_sit, situation_out = query_of_graph_flow_rules(rdf_graph, batches, flow_rules, situation_in=s0)
    ported_drs = _do_prolog_common(data_rule_facts, q_sit, situation_out)
    return ported_drs

