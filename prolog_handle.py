from collections import defaultdict
import tempfile

from typing import List

from .proto import (
        dump,
        is_ac,
        obtain,
        )
from .rule import Attribute, AttributeCapsule, ObligationDeclaration, DataRuleContainer

from pyswip import Prolog


PR_DIR = '.'  # Prolog Reasoning directory


def _pl_str(value):
    return f'"{value}"'

def _attr_id_for_prolog(attr_name, attr_ord):
    return f"{attr_name}{attr_ord}"

def dump_data_rule(drc: 'DataRuleContainer', port, situation='s0') -> str:
    s = ''
    for attrcap in drc._attrcaps:
        name = attrcap._name
        for i, attr in enumerate(attrcap._attrs):
            name = attr.attributeName
            t = 'str'
            v = attr.hasValue.valueData or attr.hasValue.valueObject
            attr_id = _attr_id_for_prolog(name, i)
            s += f"attr({_pl_str(name)}, {_pl_str(t)}, {_pl_str(v)}, [{_pl_str(attr_id)}, {port}], {situation}).\n"
    for ob in drc._rules:
        name = ob._name
        if ob._attribute:
            attr_name, attr_ord = ob._attribute
            attr = "[{}, {}]".format(_pl_str(_attr_id_for_prolog(attr_name, attr_ord)), port)
        else:
            continue # TODO: support obligations without attributes
            attr = 'null'
        ac = dump(ob._ac) or 'null'
        s += f"obligation({_pl_str(name)}, {attr}, {_pl_str(ac)}, {port}, {situation}).\n"
    return s

# def _dump_flow_rule(flow_rule: 'FlowRule') -> List[str]:
def dump_flow_rule(flow_rule: 'FlowRule') -> List[str]:
    lst = []
    for input_port, output_ports in flow_rule._conn.items():
        lst.append(f"pr({input_port}, [{','.join(output_ports)}])")
    #TODO: edit and delete
    return lst

def fin(output_ports: List[str]) -> List[str]:
    return [f"end({output})" for output in output_ports]

def query_of_flow_rule(flow_rule: 'FlowRule', situation_in='s0', situation_out='S1') -> str:
    output_ports = set()
    for ports in flow_rule._conn.values():
        output_ports.update(ports)
    act_seq = dump_flow_rule(flow_rule)
    act_seq.extend(fin(output_ports))
    s = f"do({':'.join(act_seq)}, {situation_in}, {situation_out})"
    return s

def dispatch(data_rules: 'Dict[str, DataRuleContainer]', flow_rule: 'FlowRule') -> 'PortedRules':
    with tempfile.TemporaryDirectory() as tmp_dir:
        reason_file = f"{tmp_dir}/reason_facts.pl"
        prolog = Prolog()
        prolog.consult(f"{PR_DIR}/prolog/flow_rule.pl")
        with open(reason_file, 'w') as f:
            for port, data_rule in data_rules.items():
                s = dump_data_rule(data_rule, port)
                f.write(s)
        prolog.consult(reason_file)
        res = {}
        sit_out = 'S1'
        q_sit = query_of_flow_rule(flow_rule, situation_out=sit_out)
        q_attr = f"{q_sit}, attr(N, T, V, H, {sit_out})"
        q_ob = f"{q_sit}, obligation(Ob, Attr, Ac, P, {sit_out})"
        attr_hist = {}
        ported_attrs = defaultdict(lambda : defaultdict(list))
        ported_obs = defaultdict(list)
        for r_attr in prolog.query(q_attr):
            # print(r_attr)
            hist = r_attr['H']
            port = hist[-1].value
            name = r_attr['N'].decode()
            attr = Attribute.instantiate(name, raw_attribute=r_attr['V'].decode())
            index = len(ported_attrs[port][name])
            ported_attrs[port][name].append(attr)
            attr_hist[tuple(hist)] = (name, index)
        for r_ob in prolog.query(q_ob):
            # print(r_ob)
            port = r_ob['P']
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
        # print(ported_obs)
        ported_drs = {}
        for port in set(ported_attrs) & set(ported_obs):
            obs = [ob for ob in ported_obs[port] if isinstance(ob, ObligationDeclaration)]
            attrs = [AttributeCapsule(name, attribute=attrs) for name, attrs in ported_attrs[port].items()]
            data_rule = DataRuleContainer(obs, attrs)
            ported_drs[port] = data_rule
        print(ported_drs)
        return ported_drs

