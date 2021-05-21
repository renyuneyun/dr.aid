from rdflib import Graph, URIRef
from typing import Dict, List

from draid.rule import DataRuleContainer, FlowRule, PortedRules
from draid.graph_wrapper import GraphWrapper

from . import prolog_handle

class FlowRuleHandler:

    def __init__(self, flow_rule: FlowRule):
        self._rule = flow_rule

    def dispatch(self, rules: Dict[str, DataRuleContainer]) -> PortedRules:
        return prolog_handle.dispatch(rules, self._rule)

        # outs: 'PortedRules' = {}
        # for op in self._rule._conn:  # pylint: disable=protected-access
        #     rules_to_merge = [rules[ip]
        #                       for ip in self._rule._conn[op] if ip in rules]  # pylint: disable=protected-access
        #     if rules_to_merge:
        #         outs[op] = DataRuleContainer.merge(*rules_to_merge)
        #     else:
        #         outs[op] = None
        # return outs


def dispatch_all(graph: GraphWrapper, data_rules: Dict[URIRef, Dict[str, DataRuleContainer]], flow_rules: Dict[URIRef, FlowRule]):
    return prolog_handle.dispatch_all(graph, data_rules, flow_rules)
