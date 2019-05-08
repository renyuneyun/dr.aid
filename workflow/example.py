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
import networkx as nx
import random
from itertools import combinations
import matplotlib.pyplot as plt
import numpy
import pandas as pd
import seaborn as sns

from provenance_info import *
from service_config import *


class Start(GenericPE):

    def __init__(self):
        GenericPE.__init__(self)
        self._add_input('iterations')
        self._add_output('output')
        # self.prov_cluster="myne"

    def _process(self, inputs):

        if 'iterations' in inputs:
            inp = inputs['iterations']

            self.write('output', inp, metadata={'iterations': inp})

        # Uncomment this line to associate this PE to the mycluster provenance-cluster
        #self.prov_cluster ='mycluster'


class Source(GenericPE):

    def __init__(self, sr, index, batchsize):
        GenericPE.__init__(self)
        self._add_input('iterations')
        self._add_output('output')
        self.sr = sr
        self.var_index = index
        self.batchsize = batchsize
        # self.prov_cluster="myne"

        self.parameters = {'sampling_rate': sr, 'batchsize': batchsize}

        # Uncomment this line to associate this PE to the mycluster provenance-cluster
        #self.prov_cluster ='mycluster'

    def _process(self, inputs):

        if 'iterations' in inputs:
            iteration = inputs['iterations'][0]

        batch = []
        it = 1
        # Streams out values at 1/self.sr sampling rate, until iteration>0
        while (it <= iteration):
            while (len(batch) < self.batchsize):
                val = random.uniform(0, 100)
                time.sleep(1/self.sr)
                batch.append(val)

            self.write('output', (it, self.var_index, batch), metadata={
                       'var': self.var_index, 'iteration': it, 'batch': batch})
            batch = []
            it += 1


class MaxClique(GenericPE):

    def __init__(self, threshold):
        GenericPE.__init__(self)
        self._add_input('input')
        self._add_output('graph')
        self._add_output('clique')
        self.threshold = threshold
        # self.prov_cluster="myne"

        self.parameters = {'threshold': threshold}

        # Uncomment this line to associate this PE to the mycluster provenance-cluster
        #self.prov_cluster ='mycluster'

    def _process(self, inputs):

        if 'input' in inputs:
            matrix = inputs['input'][0]
            iteration = inputs['input'][1]

        low_values_indices = matrix < self.threshold  # Where values are low
        matrix[low_values_indices] = 0
        # plt.figure('graph_'+str(iteration))

        H = nx.from_numpy_matrix(matrix)
        fig = plt.figure('graph_'+str(iteration))
        text = "Iteration "+str(iteration)+" "+"graph"

        labels = {i: i for i in H.nodes()}
        pos = nx.circular_layout(H)
        nx.draw_circular(H)
        nx.draw_networkx_labels(H, pos, labels, font_size=15)
        fig.text(.1, .1, text)
        self.write('graph', matrix, metadata={
                   'graph': str(matrix), 'batch': iteration})

       # labels = {i : i for i in H.nodes()}
       # pos = nx.circular_layout(H)
       # nx.draw_circular(H)
       # nx.draw_networkx_labels(H, pos, labels, font_size=15)

        cliques = list(nx.find_cliques(H))

        fign = 0
        maxcnumber = 0
        maxclist = []

        for nodes in cliques:
            if (len(nodes) > maxcnumber):
                maxcnumber = len(nodes)

        for nodes in cliques:
            if (len(nodes) == maxcnumber):
                maxclist.append(nodes)

        for nodes in maxclist:
            edges = combinations(nodes, 2)
            C = nx.Graph()
            C.add_nodes_from(nodes)
            C.add_edges_from(edges)
            fig = plt.figure('clique_'+str(iteration)+str(fign))
            text = "Iteration "+str(iteration)+" "+"clique "+str(fign)
            fign += 1
            labels = {i: i for i in C.nodes()}
            pos = nx.circular_layout(C)
            nx.draw_circular(C)
            nx.draw_networkx_labels(C, pos, labels, font_size=15)
            fig.text(.1, .1, text)
            self.write('clique', cliques, metadata={'clique': str(
                nodes), 'iteration': iteration, 'order': maxcnumber, 'prov:type': "hft:products"}, location="file://cliques/")


class CorrMatrix(GenericPE):

    def __init__(self, variables_number):
        GenericPE.__init__(self)
        self._add_input('input', grouping=[0])
        self._add_output('output')
        self.size = variables_number
        self.parameters = {'variables_number': variables_number}
        self.data = {}

        # Uncomment this line to associate this PE to the mycluster provenance-cluster
        # self.prov_cluster ='mycluster'self.prov_cluster='mycluster'

    def _process(self, inputs):
        for x in inputs:

            if inputs[x][0] not in self.data:
                # prepares the data to visualise the xcor matrix of a specific batch number.
                self.data[inputs[x][0]] = {}
                self.data[inputs[x][0]]['matrix'] = numpy.identity(self.size)
                self.data[inputs[x][0]]['ro_count'] = 0

            if (inputs[x][1][0] > inputs[x][1][1]):
                self.data[inputs[x][0]]['matrix'][inputs[x][1]
                                                  [0]-1, inputs[x][1][1]-1] = inputs[x][2]
            if (inputs[x][1][0] < inputs[x][1][1]):
                self.data[inputs[x][0]]['matrix'][inputs[x][1]
                                                  [1]-1, inputs[x][1][0]-1] = inputs[x][2]

            self.data[inputs[x][0]]['matrix'][inputs[x][1]
                                              [0]-1, inputs[x][1][1]-1] = inputs[x][2]
            self.data[inputs[x][0]]['ro_count'] += 1

            if self.data[inputs[x][0]]['ro_count'] == (self.size*(self.size-1))/2:
                matrix = self.data[inputs[x][0]]['matrix']

                d = pd.DataFrame(data=matrix,
                                 columns=range(0, self.size), index=range(0, self.size))

                mask = numpy.zeros_like(d, dtype=numpy.bool)
                mask[numpy.triu_indices_from(mask)] = True

                # Set up the matplotlib figure
                f, ax = plt.subplots(figsize=(11, 9))

                # Generate a custom diverging colormap
                cmap = sns.diverging_palette(220, 10, as_cmap=True)

                # Draw the heatmap with the mask and correct aspect ratio
                sns.heatmap(d, mask=mask, cmap=cmap, vmax=1,
                            square=True,
                            linewidths=.5, cbar_kws={"shrink": .5}, ax=ax)

                plt.show()
                self.log('\r\n'+str(matrix))
                self.write('output', (matrix, inputs[x][0]), metadata={
                           'matrix': str(d), 'iteration': str(inputs[x][0])})
                # dep=['iter_'+str(inputs[x][0])])


class CorrCoef(GenericPE):

    def __init__(self):
        GenericPE.__init__(self)
        # self._add_input('input1',grouping=[0])
        # self._add_input('input2',grouping=[0])
        self._add_output('output')
        self.data = {}

    def _process(self, inputs):
        index = None
        val = None

        for x in inputs:
            if inputs[x][0] not in self.data:
                self.data[inputs[x][0]] = []

            for y in self.data[inputs[x][0]]:

                ro = numpy.corrcoef(y[2], inputs[x][2])

                self.write('output', (inputs[x][0], (y[1], inputs[x][1]), ro[0][1]), metadata={'iteration': inputs[x][0], 'vars': str(
                    y[1])+"_"+str(inputs[x][1]), 'rho': ro[0][1]}, dep=['var_'+str(y[1])+"_"+str(y[0])])

            # appends var_index and value
            self.data[inputs[x][0]].append(inputs[x])
            # self.log(self.data[inputs[x][0]])
            self.update_prov_state('var_'+str(inputs[x][1])+"_"+str(inputs[x][0]), None, metadata={
                                   'var_'+str(inputs[x][1]): inputs[x][2]}, ignore_inputs=True)


variables_number = 3
sampling_rate = 100
batch_size = 3
iterations = 2

input_data = {"Start": [{"iterations": [iterations]}]}

# Instantiates the Workflow Components
# and generates the graph based on parameters


def createWf():
    graph = WorkflowGraph()
    mat = CorrMatrix(variables_number)
    mat.prov_cluster = 'record2'
    mc = MaxClique(-0.5)
    mc.prov_cluster = 'record0'
    start = Start()
    start.prov_cluster = 'record0'
    sources = {}

    cc = CorrCoef()
    cc.prov_cluster = 'record1'
    stock = ['hft:NASDAQ', 'hft:MIBTEL', 'hft:DOWJ']

    for i in range(1, variables_number+1):
        sources[i] = Source(sampling_rate, i, batch_size)
        sources[i].prov_cluster = stock[i % len(stock)-1]

        sources[i].numprocesses = 1

    for h in range(1, variables_number+1):
        cc._add_input('input'+'_'+str(h+1), grouping=[0])
        graph.connect(start, 'output', sources[h], 'iterations')
        graph.connect(sources[h], 'output', cc, 'input'+'_'+str(h+1))

    graph.connect(cc, 'output', mat, 'input')
    graph.connect(mat, 'output', mc, 'input')

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
    "provone:User": "aspinuso",
    "s-prov:description": " correlation of four continuous variables",
    "s-prov:workflowName": "CAW",
    "s-prov:workflowType": "hft:CorrelationAnalysis",
    "s-prov:workflowId": "190341",
    "s-prov:description": "CAW Test Case",
    "s-prov:save-mode": "service",
    "s-prov:componentsType":
        {"MaxClique": {"s-prov:type": (IntermediateStatefulOut,),
                        "s-prov:stateful-port": "graph",
                        "s-prov:prov-cluster": "hft:StockAnalyser"},

         "CorrMatrix": {"s-prov:type": (ASTGrouped, StockType,),
                        "s-prov:prov-cluster": "hft:StockAnalyser"},

         "CorrCoef": {"s-prov:type": (SingleInvocationFlow,),
                      "s-prov:prov-cluster": "hft:Correlator"}
         },
        "s-prov:sel-rules": selrule2
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
rid = 'MINE_'+getUniqueId()

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
                   componentsType=prov_config["s-prov:componentsType"],
                   save_mode=prov_config["s-prov:save-mode"],
                   sel_rules=prov_config["s-prov:sel-rules"],

                   )

start_time = time.time()
process_and_return(graph, input_data)
elapsed_time = time.time() - start_time
print("ELAPSED TIME: "+str(elapsed_time))
