#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/05/07 12:29:58
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''


from dispel4py.workflow_graph import WorkflowGraph
from dispel4py.new.processor import *
import time
import traceback
from dispel4py.base import create_iterative_chain, GenericPE, ConsumerPE, IterativePE, SimpleFunctionPE
from dispel4py.new.simple_process import process_and_return
from dispel4py.visualisation import display
from scipy.stats.stats import pearsonr

from exp.workflow.PE import *
from exp.workflow.provenance_info import *
from exp.workflow.service_config import *


variables_number = 3
sampling_rate = 100
batch_size = 3
iterations = 2

input_data = {"Start": [{"iterations": [iterations]}]}

# Instantiates the Workflow Components
# and generates the graph based on parameters


def createWf():
    graph = WorkflowGraph()

    source = NumberProducer()

    inc1 = Increase()

    inc2 = Increase(2)

    graph.connect(source, 'output', inc1, 'input')
    graph.connect(inc1, 'output', inc2, 'input')

    return graph


# Definition of metadata driven selectivity rules
#  Excludes the start component from the trace
selrule2 = {"Start": {
    "rules": {
        "iterations": {
            "$lt": 0}
    }
}
}


# Configuration setup of the provenance execution of the run
prov_config = {
    "provone:User": "rui",
    "s-prov:description": "one to one streaming",
    "s-prov:workflowName": "one-to-one",
    "s-prov:workflowType": "mine:example",
    "s-prov:workflowId": "1",
    "s-prov:save-mode": "service",
    #"s-prov:componentsType":
    #{"MaxClique": {"s-prov:type": (IntermediateStatefulOut,),
    #    "s-prov:stateful-port": "graph",
    #    "s-prov:prov-cluster": "hft:StockAnalyser"},

    #    "CorrMatrix": {"s-prov:type": (ASTGrouped, StockType,),
    #        "s-prov:prov-cluster": "hft:StockAnalyser"},

    #    "CorrCoef": {"s-prov:type": (SingleInvocationFlow,),
    #        "s-prov:prov-cluster": "hft:Correlator"}
    #    },
    #"s-prov:sel-rules": selrule2
}


# Store via service
ProvenanceType.REPOS_URL = REPOS_URL

# Export data lineage via service (REST GET Call on dataid resource /data/<id>/export)
ProvenanceType.PROV_EXPORT_URL = PROV_EXPORT_URL

# Store to local path
ProvenanceType.PROV_PATH = PROV_PATH

# Size of the provenance bulk before sent to storage or sensor
ProvenanceType.BULK_SIZE = BULK_SIZE

graph = createWf()

# Ranomdly generated unique identifier for the current run
rid = 'ONE_TO_ONE_'+getUniqueId()

# Finally, provenance enhanced graph is prepared:
# Initialise provenance storage end associate a Provenance type with specific components:
configure_prov_run(graph, None,
                   provImpClass=(SingleInvocationFlow,),
                   username=prov_config["provone:User"],
                   runId=rid,
                   input=[{'name': 'variables_number', 'val': variables_number},
                          {'name': 'sampling_rate', 'val': sampling_rate},
                          {'name': 'batch_size', 'val': batch_size},
                          {'name': 'iterations', 'val': iterations}],
                   description=prov_config["s-prov:description"],
                   workflowName=prov_config["s-prov:workflowName"],
                   workflowType=prov_config["s-prov:workflowType"],
                   workflowId="!23123",
                   #componentsType=prov_config["s-prov:componentsType"],
                   save_mode=prov_config["s-prov:save-mode"],
                   #sel_rules=prov_config["s-prov:sel-rules"],

                   )

#start_time = time.time()
#process_and_return(graph, input_data)
#elapsed_time = time.time() - start_time
#print("ELAPSED TIME: "+str(elapsed_time))
