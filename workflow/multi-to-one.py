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

    N = 3

    sources = [NumberProducer() for i in range(N)]

    incs = [Increase() for i in range(N)]

    avg = MultiAverage(N)

    finc = Increase()

    for i in range(N):
        graph.connect(sources[i], 'output', incs[i], 'input')
        graph.connect(incs[i], 'output', avg, MultiAverage.INPUT.format(i))

    graph.connect(avg, MultiAverage.OUTPUT, finc, 'input')

    return graph


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
rid = 'MULTI_TO_ONE_'+getUniqueId()

# Configuration setup of the provenance execution of the run
prov_config = {
    "provone:User": "rui",
    "s-prov:description": "multi to one streaming",
    "s-prov:workflowName": "multi-to-one",
    "s-prov:workflowType": "mine:example",
    "s-prov:workflowId": "3",
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
}

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
                   workflowId=prov_config["s-prov:workflowId"],
                   #componentsType=prov_config["s-prov:componentsType"],
                   save_mode=prov_config["s-prov:save-mode"],
                   )

#start_time = time.time()
#process_and_return(graph, input_data)
#elapsed_time = time.time() - start_time
#print("ELAPSED TIME: "+str(elapsed_time))

