'''
The settings, shared among all modules.
'''

SCHEME = 'CWLPROV'

AIO = False

RULE_DB = 'rule-db.json'


# Internal configurations. Normally they do not need to change, unless the you know what they are

IMPORT_PORT_NAME = 'imported_rule'


# Rule injection

from rdflib import URIRef
from . import synthetic_raw_rules as rr

# The extra flow rules to be injected into the reasoner. It takes precedence of the added rules from the database.
# It is a nested dictionary, where the key of the first level is the graph ID (if there is a subgraph in the provenance) specifying a specific graph where the flow rule applies. For anything with graph ID `None`, it is applied universally unless already specified above.
# A valid graph ID must be a URIRef.
INJECTED_FLOW_RULE = {
        ###### k1 : {k2 : v}  <==> graph_id : {component_name/function: rule_str}
        None : {
            # k2 : v  <==>  component_name/function: rule_str
            'NumberProducer': '',
            'Increase': '',
            'Redispatch': '''{'output0': ['input0', 'input1'], 'output1': ['input0', 'input2'], 'output3': ['input1', 'input2']}''',
            # 'arcp://uuid,19bb7653-72fd-4a80-8e4b-44d409346434/workflow/packed.cwl#main/processfiles_2': rr.Remove_Source_UoE,
            # 'arcp://uuid,19bb7653-72fd-4a80-8e4b-44d409346434/workflow/packed.cwl#main/processfiles_3': rr.Change_Source_UoE_UK,
            },
        URIRef('http://schema.org#2a3c188f8cd6-19-b9fee0c2-7179-11e9-bd29-0242ac120003') : {
            # k1 : {k2 : v}  <==>  graph_id : {component_id: rule_str}
            URIRef('123'): '{}',
            }
        }

# The extra data rules to be injected into the reasoner, through the "import" port.
# The value can be a string, a function with signature (ComponentInfo) -> str, or None (or anything else seen as False).
# If the value is a string, it is used as the raw rules.
# If the value is equivalent to False, then a random rule is applied.
# If the value is a function, the return value is used as the raw rules, even if it's empty.
INJECTED_IMPORTED_RULE = {
        # k:v <==> component_name/function: rule_str
        'Source' : None,
        'downloadPE' : None,
        'Collector' : None,
        'COLLECTOR1' : None,
        'COLLECTOR2' : None,
        'NumberProducer' : None,
        # 'arcp://uuid,19bb7653-72fd-4a80-8e4b-44d409346434/workflow/packed.cwl#main/create_environment' : rr.Acknowledgement_UoE,
        # 'arcp://uuid,19bb7653-72fd-4a80-8e4b-44d409346434/workflow/packed.cwl#main/create_environment_2' : rr.Acknowledgement_UoE,
        # 'arcp://uuid,19bb7653-72fd-4a80-8e4b-44d409346434/workflow/packed.cwl#main/create_environment_3' : rr.Acknowledgement_UoE,
        }

# The extra data rules to be injected into the reasoner. It takes precedence of the added rules from the database.
# Warning: Only specify the rules of the initial input data or the final output data. If the data object is inside the workflow, the behaviour is not defined.
# INJECTED_DATA_RULE = {
#         }

