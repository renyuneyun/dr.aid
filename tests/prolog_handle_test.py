import pytest
import os

from exp.rule import ObligationDeclaration, DataRuleContainer, AttributeCapsule, FlowRule
from exp.proto import WhenImported

from exp import prolog_handle

pc1 = AttributeCapsule('name', 'UoE')
pc1_2 = AttributeCapsule('name', ['UoE', 'University of Earth'])

pc2 = AttributeCapsule('sens', '1')

ob1 = (
        ObligationDeclaration('credit', ('name', 0)),
        ObligationDeclaration('credit', ('name', 1)),
        ObligationDeclaration('credit', ('name', 0), WhenImported()),
        ObligationDeclaration('credit', ('name', 1), WhenImported()),
        )
ob2 = ObligationDeclaration('hide', ('sens', 0))

rule1 = DataRuleContainer([ob1[0], ob2], [pc1, pc2])
# rule2 = DataRuleContainer([ob1[0], ob1[1], ob2, ob3], [pc1, pc2])

flow_rule1 = FlowRule({
    'input1': ['output1', 'output2'],
    'input2': ['output1'],
    })


@pytest.mark.parametrize('drc, port', [
    (rule1, 'input1'),
    ])
def test_dump_data_rule(drc, port):
    d = prolog_handle.dump_data_rule(drc, port)
    assert d
    assert d == ''

@pytest.mark.parametrize('flow_rule', [
    flow_rule1,
    ])
def test_dump_flow_rule(flow_rule):
    d = prolog_handle.dump_flow_rule(flow_rule)
    assert d
    assert d == ''

@pytest.mark.parametrize('flow_rule', [
    flow_rule1,
    ])
def test_query_of_flow_rule(flow_rule):
    d = prolog_handle.query_of_flow_rule(flow_rule)
    assert d
    assert d == ''

@pytest.mark.parametrize('data_rules, flow_rule', [
    ({'input1': rule1}, flow_rule1),
    ])
def test_dispatch(data_rules, flow_rule):
    prolog_handle.PR_DIR = '/home/ryey/self/Edinburgh/PhD/exp/exp'
    prolog_handle.dispatch(data_rules, flow_rule)
    assert True

