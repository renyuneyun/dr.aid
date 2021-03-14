#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/03/31 17:04:03
#   License :   Apache 2.0 (See LICENSE)
#

'''
This module contains the queries used by the SProv SPARQL helper, handling the S-Prov schema.
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
PREFIX provone: <http://purl.dataone.org/provone/2015/01/15/ontology#>
PREFIX s-prov: <http://s-prov/ns/#>
'''

#ALL_WFE_GRAPHS = '''
#SELECT ?g WHERE {
#  ?g a s-prov:WFExecutionBundle
#} 
#'''
ALL_WFE_GRAPHS = '''
SELECT ?g WHERE {
  GRAPH ?g {
  }
} 
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

#P_INVOCATION_OF_COMPONENT_DIRECT = '''
#    {
#      SELECT ?invocation ?component WHERE {
#        ?invocation a prov:Activity;
#                    prov:wasAssociatedWith ?component.
#        FILTER NOT EXISTS {?invocation a s-prov:WFExecution}
#      }
#    }
#'''

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

# P_COMPONENT_TIL_DATA = P_INVOCATION_OF_COMPONENT_INDIRECT + P_INVOCATION_DATA

# def F_DATA_OF_COMPONENT(graph: T_REF, component: str) -> str:
#     body = """
#     ?component a s-prov:Component.
#     FILTER (str(?component) = "{}")

#     {body}
#         """
#     return F_QUERY('*', graph, body.format(component, body=P_COMPONENT_TIL_DATA))


#T_QUERY_INFLUENCED_DATA = P("""
#SELECT * WHERE {{
#  graph ?g {{
#
#    ?component a s-prov:Component .
#
#    ?data_out a s-prov:Data.
#    FILTER (str(?data_out) = "{}")
#
#    {body}
#
#  }}
#}}
#""", body=P_COMPONENT_TIL_DATA)


# INFLUENCED_DATA = DP(T_QUERY,
#         'body',
#         P("""
#     ?component a s-prov:Component .

#     ?data_out a s-prov:Data.
#     FILTER (str(?data_out) = "{}")

#     {body}
#         """, body=P_COMPONENT_TIL_DATA),
#         target='*'
#         )

# def F_INFLUENCED_DATA(graph: T_REF, data_out: T_REF) -> str:
#     body = """
#     ?component a s-prov:Component .

#     ?data_out a s-prov:Data.
#     FILTER (str(?data_out) = "{}")

#     {body}
#         """
#     return F_QUERY('*', graph, body.format(data_out, body=P_COMPONENT_TIL_DATA))

#T_COMPONENT_WITH_DATA = P("""
#SELECT * WHERE {{
#  graph ?g {{
#
#    ?component a s-prov:Component .
#
#    {body}
#
#  }}
#}}
#""", body=P_COMPONENT_TIL_DATA)

# COMPONENT_AND_DATA = P(T_QUERY, target='*', body="""
#     ?component a s-prov:Component .

#     {body}
# """.format(body=P_COMPONENT_TIL_DATA))

# def F_COMPONENT_AND_DATA(graph: T_REF) -> str:
#     body = """
#     ?component a s-prov:Component .

#     {body}
#     """
#     return F_QUERY('*', graph, body.format(body=P_COMPONENT_TIL_DATA))


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

# COMPONENT_WITHOUT_INPUT_DATA = P(T_QUERY, target='?component', body=P_COMPONENT_WITHOUT_INPUT_DATA)

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

# COMPONENT_PARS = P(T_QUERY, target='DISTINCT ?component ?par ?pred ?obj',
#                    body=P_COMPONENT_PARS)

# COMPONENT_PARS_IN = DP(T_QUERY,
#         'body',
#         DP("{body} {filter}",
#             'filter',
#             F_P_FILTER_COMPONENT_IN,
#             body=P_COMPONENT_PARS,
#             ),
#         target='DISTINCT ?component ?par ?pred ?obj')

def F_COMPONENT_PARS_IN(graph, component_list: Iterable) -> str:
    ifilter = F_P_FILTER_COMPONENT_IN(component_list)
    q_body = "{body} {filter}".format(body=P_COMPONENT_PARS, filter=ifilter)
    return F_QUERY('DISTINCT ?component ?par ?pred ?obj', graph, q_body)

P_COMPONENT_FUNCTION = '''
    ?component a s-prov:Component .
    ?component s-prov:functionName ?function_name.
'''

# COMPONENT_FUNCTION = P(T_QUERY, target='?component ?function_name',
#                        body=P_COMPONENT_FUNCTION)

def F_COMPONENT_FUNCTION(graph: T_REF) -> str:
    return F_QUERY('?component ?function_name', graph, P_COMPONENT_FUNCTION)


T_COMPONENT_GRAPH = P('''
PREFIX : <http://ryey/ns/#>


CONSTRUCT {{
  ?component0 :hasNextStage ?component1 .
}}
WHERE {{
  graph {} {{

    ?component0 a s-prov:Component .
    ?invocation0 a prov:Activity ;
                prov:wasAssociatedWith ?component_instance0 .
    ?component_instance0 a s-prov:ComponentInstance ;
                        prov:actedOnBehalfOf ?component0 .

    ?data_out0 prov:qualifiedGeneration ?generation .
    ?generation prov:activity ?invocation0 .


    OPTIONAL {{
      ?component1 a s-prov:Component .
      ?invocation1 a prov:Activity ;
                   prov:wasAssociatedWith ?component_instance1 .
      ?component_instance1 a s-prov:ComponentInstance ;
                           prov:actedOnBehalfOf ?component1 .

      ?invocation1 prov:qualifiedUsage ?usage .
      ?usage prov:entity ?data_out0 .

      FILTER (?component0 != ?component1)
    }}

  }}
}}
''')

# C_COMPONENT_GRAPH = T_COMPONENT_GRAPH('?g')


def F_C_COMPONENT_GRAPH(graph: T_REF) -> str:
    return T_COMPONENT_GRAPH("<{}>".format(graph))


# C_DATA_DEPENDENCY = '''
# PREFIX : <http://ryey/ns/#>

# CONSTRUCT {
#   ?component0 a s-prov:Component .
#   ?component0 :hasNextStage ?component1 .
#   ?component0 :hasOutput ?data_out0 .
# #  ?component1 :hasPrevStage ?component0 .
# }
# WHERE {
#   graph ?g {

#     ?component0 a s-prov:Component .
#     ?invocation0 a prov:Activity ;
#                 prov:wasAssociatedWith ?component_instance0 .
#     ?component_instance0 a s-prov:ComponentInstance ;
#                         prov:actedOnBehalfOf ?component0 .

#     ?data_out0 prov:qualifiedGeneration ?generation .
#     ?generation prov:activity ?invocation0 .


#     OPTIONAL {
#       ?component1 a s-prov:Component .
#       ?invocation1 a prov:Activity ;
#                    prov:wasAssociatedWith ?component_instance1 .
#       ?component_instance1 a s-prov:ComponentInstance ;
#                            prov:actedOnBehalfOf ?component1 .

#       ?invocation1 prov:qualifiedUsage ?usage .
#       ?usage prov:entity ?data_out0 .

#       FILTER (?component0 != ?component1)
#     }

#   }
# }
# '''

T_DATA_DEPENDENCY_WITH_PORT = P('''
PREFIX : <http://ryey/ns/#>


CONSTRUCT {{
  ?component0 a s-prov:Component ;
    :hasOutPort ?port_out .

  ?port_out a :OutputPort ;
    :name ?out_port ;
    :hasConnection ?connection .

  ?connection a :Connection ;
    :data ?data_out0 .

  ?data_out0 a s-prov:Data .

  ?connection :target ?port_in .

  ?port_in a :InputPort ;
    :name ?in_port ;
    :inputTo ?component1 .
}}
WHERE {{
  graph {} {{

    ?component0 a s-prov:Component .
    ?invocation0 a prov:Activity ;
                 prov:wasAssociatedWith ?component_instance0 .
    ?component_instance0 a s-prov:ComponentInstance ;
                         prov:actedOnBehalfOf ?component0 .

    ?data_out0 prov:qualifiedGeneration ?generation .

    ?generation prov:activity ?invocation0 ;
                provone:hadOutPort ?out_port .


    OPTIONAL {{
      ?component1 a s-prov:Component .
      ?invocation1 a prov:Activity ;
                   prov:wasAssociatedWith ?component_instance1 .
      ?component_instance1 a s-prov:ComponentInstance ;
                           prov:actedOnBehalfOf ?component1 .

      ?invocation1 prov:qualifiedUsage ?usage .

      ?usage prov:entity ?data_out0 ;
             provone:hadInPort ?in_port .

      FILTER (?component0 != ?component1)
    }}

    BIND (IF(REGEX(STR(?component0), "http://[^#]+#"), STRAFTER(STR(?component0), "#"), STR(?component0)) AS ?component0_name)
    BIND (IF(REGEX(STR(?component1), "http://[^#]+#"), STRAFTER(STR(?component1), "#"), STR(?component1)) AS ?component1_name)

    BIND (COALESCE(?component1_name, "") AS ?component1_name_safe)
    BIND (COALESCE(?in_port, "") AS ?in_port_safe)

    BIND (IRI(CONCAT("http://ryey/ns/#", CONCAT(STR(?component0_name), CONCAT("=)", STR(?out_port))))) AS ?port_out)
    BIND (IRI(CONCAT("http://ryey/ns/#", CONCAT(STR(?component1_name), CONCAT("(=", STR(?in_port))))) AS ?port_in)
      BIND (IRI(
          CONCAT("http://ryey/ns/#",
            CONCAT(
              CONCAT(
                CONCAT(?component0_name, CONCAT("::", STR(?out_port))),
                "::"),
              CONCAT(CONCAT(CONCAT("::", STR(?in_port_safe)), "::"), ?component1_name_safe)
            )
          )
      	) AS ?connection)
  }}
}}
''')


# C_DATA_DEPENDENCY_WITH_PORT = T_DATA_DEPENDENCY_WITH_PORT('?g')

def F_C_DATA_DEPENDENCY_WITH_PORT(graph: T_REF) -> str:
    return T_DATA_DEPENDENCY_WITH_PORT("<{}>".format(graph))

#C_INITIAL_DATA = '''
#PREFIX : <http://ryey/ns/#>
#
#
#CONSTRUCT {
#  ?component0 a s-prov:Component ;
#    :hasOutPort ?port_out .
#
#  ?port_out a :OutputPort ;
#    :name ?out_port ;
#    :data ?data_out0 .
#
#}
#WHERE {
#  graph ?g {
#
#    ?component0 a s-prov:Component .
#    ?invocation0 a prov:Activity ;
#                 prov:wasAssociatedWith ?component_instance0 .
#    ?component_instance0 a s-prov:ComponentInstance ;
#                         prov:actedOnBehalfOf ?component0 .
#
#    ?data_out0 prov:qualifiedGeneration ?generation .
#
#    ?generation prov:activity ?invocation0 ;
#                provone:hadOutPort ?out_port .
#
#
#    FILTER NOT EXISTS {
#      ?component0 a s-prov:Component .
#      ?invocation00 a prov:Activity ;
#                   prov:wasAssociatedWith ?component_instance00 .
#      ?component_instance00 a s-prov:ComponentInstance ;
#                           prov:actedOnBehalfOf ?component0 .
#
#      ?invocation00 prov:qualifiedUsage ?usage00 .
#
#      ?usage00 prov:entity ?data_in0 .
#
#      ?data_in0 a s-prov:Data .
#    }
#
#    BIND (STRAFTER(STR(?component0), "#") AS ?component0_name)
#
#    BIND (IRI(CONCAT("http://ryey/ns/#", CONCAT(STR(?component0_name), CONCAT("=)", STR(?out_port))))) AS ?port_out)
#
#  }
#}
##LIMIT 1000
#'''
