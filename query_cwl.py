#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/03/31 17:04:03
#   License :   Apache 2.0 (See LICENSE)
#

'''
This module contains the queries used by the CWL SPARQL helper, handling the CWLProv schema.
'''

from functools import partial
from typing import Iterable

from .names import T_REF


def P(s, *args, **kwargs):
    if callable(s):
        return partial(s, *args, **kwargs)
    else:
        assert isinstance(s, str)
        return partial(s.format, *args, **kwargs)


def D(post, pri_key, pri, *args, **kwargs):
    def wrapped(*iargs, **ikwargs):
        pri_result = pri(*iargs, **ikwargs)
        kwargs[pri_key] = pri_result
        return post(*args, **kwargs)
    return wrapped


def DP(post, pri_key, pri, *args, **kwargs):
    '''
    Deferred P
    '''
    def wrapped(*iargs, **ikwargs):
        pri_result = pri(*iargs, **ikwargs)
        if callable(pri_result):
            return DP(post, pri_key, pri_result, *args, **kwargs)
        kwargs[pri_key] = pri_result
        return P(post, *args, **kwargs)
    return wrapped


def Q(s, *args, **kwargs):
    if callable(s):
        s = s(*args, **kwargs)
        while callable(s):
            s = s()
        return PREFIX + s
    else:
        assert not args and not kwargs
        return PREFIX + s

PREFIX = '''
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX wf4prov: <http://purl.org/wf4ever/wfprov#>
PREFIX wf4desc: <http://purl.org/wf4ever/wfdesc#>
PREFIX cwl: <https://w3id.org/cwl/cwl#>
PREFIX wf: <http://www.w3.org/2005/01/wf/flow#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>


PREFIX s-prov: <http://s-prov/ns/#>
'''


T_QUERY = P("""
SELECT {target} {{
  GRAPH <{graph}> {{

    {body}

  }}
}}
""")

def F_QUERY(target: str, graph: T_REF, body: str) -> str:
    #return T_QUERY(target=target, graph="<{}>".format(graph), body=body)
    return T_QUERY(target=target, graph=graph, body=body)

P_INVOCATION_DATA_IN = '''
    { # invocation <- data
      SELECT ?invocation ?data_in ?port_in WHERE {
        ?invocation prov:qualifiedUsage ?usage .
        ?usage prov:entity ?data_in .
        OPTIONAL {
          ?usage provone:hadInPort ?port_in .
        }
      }
    }
'''
P_INVOCATION_DATA_OUT = '''
    { # invocation -> data
      SELECT ?invocation ?data_out ?port_out WHERE {
        ?data_out prov:qualifiedGeneration ?generation .
        ?generation prov:activity ?invocation .
        OPTIONAL {
          ?generation provone:hadOutPort ?port_out .
        }
      }
    }
'''
P_INVOCATION_DATA = f'''
    {P_INVOCATION_DATA_IN}
    UNION
    {P_INVOCATION_DATA_OUT}
'''


P_INVOCATION_OF_COMPONENT_INDIRECT = '''
    {
      SELECT ?invocation ?component ?component_instance WHERE {
        ?invocation a prov:Activity ;
                    prov:wasAssociatedWith ?component_instance .
        ?component_instance a s-prov:ComponentInstance ;
                            prov:actedOnBehalfOf ?component .
      }
    }
'''


def F_P_FILTER_COMPONENT_IN(component_list: Iterable) -> str:
    T_FILTER = """
FILTER (str(?component) in ({}))
"""
    assert component_list
    c_list = ['"{}"'.format(c) for c in component_list]
    s = ",".join(c_list)
    return T_FILTER.format(s)


P_COMPONENT_WITHOUT_INPUT_DATA = """
    {
      SELECT ?component {
        ?component a s-prov:Component .
        ?component_instance a s-prov:ComponentInstance ;
                            prov:actedOnBehalfOf ?component .
        ?invocation a prov:Activity ;
                    prov:wasAssociatedWith ?component_instance .

        OPTIONAL { # invocation <- data
          SELECT ?invocation ?data_in {
            ?invocation prov:qualifiedUsage ?usage .
            ?usage prov:entity ?data_in .
            MINUS {?data_in a s-prov:ComponentParameters.}
          }
        }

        FILTER(!BOUND(?data_in))
      }
    }
"""


def F_COMPONENT_WITHOUT_INPUT_DATA(graph: T_REF) -> str:
    return F_QUERY('?component', graph, P_COMPONENT_WITHOUT_INPUT_DATA)

INITIAL_COMPONENT_AND_DATA = P(T_QUERY, target='?component ?data_out ?port_out',
        body=P_COMPONENT_WITHOUT_INPUT_DATA+P_INVOCATION_OF_COMPONENT_INDIRECT+P_INVOCATION_DATA_OUT)

INITIAL_COMPONENT_AND_DATA_AND_PAR = P(T_QUERY, target='?component (?data_in AS ?par) ?data_out ?port_out',
        body=P_COMPONENT_WITHOUT_INPUT_DATA+P_INVOCATION_OF_COMPONENT_INDIRECT+P_INVOCATION_DATA)


P_COMPONENT_PARS = '''
    ?component a s-prov:Component .
    ?component_instance a s-prov:ComponentInstance;
                        prov:actedOnBehalfOf ?component .
    ?invocation prov:wasAssociatedWith ?component_instance .

    ?invocation prov:qualifiedUsage ?usage .

    ?usage a prov:Usage ;
           prov:entity ?par .
    ?par a s-prov:ComponentParameters ;
         ?pred ?obj .

    FILTER (?pred != rdf:type)
'''


def F_COMPONENT_PARS_IN(graph, component_list: Iterable) -> str:
    ifilter = F_P_FILTER_COMPONENT_IN(component_list)
    q_body = "{body} {filter}".format(body=P_COMPONENT_PARS, filter=ifilter)
    return F_QUERY('DISTINCT ?component ?par ?pred ?obj', graph, q_body)


Q_COMPONENT_FUNCTION = '''
SELECT ?component ?function_name WHERE {
  ?component prov:qualifiedAssociation [prov:hadPlan ?function_name].
} 
'''


C_COMPONENT_GRAPH = P('''
PREFIX : <http://ryey/ns/#>


CONSTRUCT {{
  ?component0 :hasNextStage ?component1 .
}}
WHERE {{
  ?component0 a wf4prov:ProcessRun.
  ?mid prov:qualifiedGeneration [prov:activity ?component0].
  ?component1 a prov:Activity.
  {{
    ?component1 prov:qualifiedUsage [prov:entity ?mid].
  }}
  UNION
  {{
    ?component1 prov:qualifiedUsage [prov:entity [prov:hadMember ?mid]].
  }}

}}
''')



# TODO: remove P() and double brackets -- this does not contain templates / string formatter
# C_DATA_DEPENDENCY_WITH_PORT = P('''
# PREFIX : <http://ryey/ns/#>


# CONSTRUCT {{
#   ?component0 a s-prov:Component ;
#     :hasOutPort ?port_out .

#   ?port_out a :OutputPort ;
#     :name ?out_port ;
#     :hasConnection ?connection .

#   ?connection a :Connection ;
#     :target ?port_in ;
#     :data ?data_out0 .

#   ?data_out0 a s-prov:Data .

#   ?port_in a :InputPort ;
#     :name ?in_port ;
#     :inputTo ?component1 .
# }}
# WHERE {{
#   ?component0 a wf4prov:ProcessRun.
#   ?data_out0 prov:qualifiedGeneration [prov:activity ?component0; prov:hadRole ?out_port].

#   OPTIONAL {{
#     ?component1 a wf4prov:ProcessRun.
#     {{
#       ?component1 prov:qualifiedUsage [prov:entity ?data_out0; prov:hadRole ?in_port].
#     }}
#     UNION
#     {{
#       ?component1 prov:qualifiedUsage [prov:entity [prov:hadMember ?data_out0]; prov:hadRole ?in_port].
#     }}
#   }}

#   BIND (STRAFTER(STR(?component0), "#") AS ?component0_name)
#   BIND (STRAFTER(STR(?component1), "#") AS ?component1_name)

#   BIND (IRI(CONCAT("http://ryey/ns/#", CONCAT(STR(?component0_name), CONCAT("=)", STR(?out_port))))) AS ?port_out)
#   BIND (IRI(CONCAT("http://ryey/ns/#", CONCAT(STR(?component1_name), CONCAT("(=", STR(?in_port))))) AS ?port_in)
#     BIND (IRI(
#         CONCAT("http://ryey/ns/#",
#           CONCAT(
#             CONCAT(
#               CONCAT(?component0_name, CONCAT("::", STR(?out_port))),
#               "::"),
#             CONCAT(CONCAT(CONCAT("::", STR(?in_port)), "::"), ?component1_name)
#           )
#         )
#       ) AS ?connection)
# }}
# ''')
C_DATA_DEPENDENCY_WITH_PORT = P('''
PREFIX : <http://ryey/ns/#>


CONSTRUCT {{
  ?component0 a s-prov:Component ;
    :hasOutPort ?port_out .

  ?port_out a :OutputPort ;
    :name ?out_port ;
    :hasConnection ?connection .

  ?connection a :Connection ;
    :data ?data_out0 .

  ?connection :target ?port_in .

  ?data_out0 a s-prov:Data .

  ?port_in a :InputPort ;
    :name ?in_port ;
    :inputTo ?component1 .
}}
WHERE {{
  ?component0 a wf4prov:ProcessRun.
  ?data_out0 prov:qualifiedGeneration [prov:activity ?component0; prov:hadRole ?out_port].

  OPTIONAL {{
    ?component1 a wf4prov:ProcessRun.
    {{
      ?component1 prov:qualifiedUsage [prov:entity ?data_out0; prov:hadRole ?in_port].
    }}
    UNION
    {{
      ?component1 prov:qualifiedUsage [prov:entity [prov:hadMember ?data_out0]; prov:hadRole ?in_port].
    }}
  }}

  BIND (IF(REGEX(STR(?component0), "http://[^#]+#"), STRAFTER(STR(?component0), "#"), STR(?component0)) AS ?component0_name)
  BIND (IF(REGEX(STR(?component1), "http://[^#]+#"), STRAFTER(STR(?component1), "#"), STR(?component1)) AS ?component1_name)

  BIND (IRI(CONCAT("http://ryey/ns/#", CONCAT(STR(?component0_name), CONCAT("=)", STR(?out_port))))) AS ?port_out)
  BIND (IRI(CONCAT("http://ryey/ns/#", CONCAT(STR(?component1_name), CONCAT("(=", STR(?in_port))))) AS ?port_in)
    BIND (IRI(
        CONCAT("http://ryey/ns/#",
          CONCAT(
            CONCAT(
              CONCAT(?component0_name, CONCAT("::", STR(?out_port))),
              "::"),
            CONCAT(CONCAT(CONCAT("::", STR(?in_port)), "::"), ?component1_name)
          )
        )
      ) AS ?connection)
}}
''')

