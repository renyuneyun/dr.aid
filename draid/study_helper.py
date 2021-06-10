#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/05/31 22:20:24
#   License :   Apache 2.0 (See LICENSE)
#

'''
A module created to simplify the content for the study. It is intended to be used in conjunction with the notebook (see `Example Simple.ipynb`)
'''

from IPython.display import Image
import pandas as pd

from draid import graph_wrapper as gw
from draid import main
from draid import rule_database_helper as rdbh
from draid import setting  # the `setting` module is used to store configuration informations
from draid import sparql_helper as sh
from draid import visualise as vis
from draid.obligation_store import ObligationStore


class Helper:

    def __init__(self, service_url, scheme, rule_db, obligation_db):
        self.s_helper = None
        self.graph = None
        self.graph_wrapper = None
        self.store = None
        self._acob = None
        self._configure(service_url, scheme, rule_db, obligation_db)

    def _configure(self, service, scheme, rule_db, obligation_db):
        setting.SCHEME = scheme  # The scheme in thie service, either SPROV or CWLPROV.

        setting.OBLIGATION_DB = obligation_db  # The database to store the activated obligations.

        self.store = ObligationStore(obligation_db)

        self.load_local_database(rule_db)
        self.set_up_s_helper(service, scheme)
        self.get_graph_wrapper(scheme)

    def load_local_database(self, rule_db):
        setting.RULE_DB = [rule_db]
        # setting.DB_WRITE_TO = True

        rdbh.init_default()

    def set_up_s_helper(self, service, scheme):
        if scheme == 'SPROV':
            self.s_helper = sh.SProvHelper(service)
            graphs = list(self.s_helper.get_wfe_graphs())

            self.graph = graphs[0]
        elif scheme == 'CWLPROV':
            self.s_helper = sh.CWLHelper(service)

    def get_graph_wrapper(self, scheme):
        if scheme == 'SPROV':
            self.graph_wrapper = gw.GraphWrapper.from_sprov(self.s_helper, subgraph=self.graph)
        elif scheme == 'CWLPROV':
            self.graph_wrapper = gw.GraphWrapper.from_cwl(self.s_helper)

    def add_virtual_process(self, process_type):
        self.graph_wrapper.add_virtual(process_type)

    def call_reasoner(self):
        self.graph_wrapper.add_virtual("publish")
        graph_wrapper, activated_obligations = main.propagate_single(self.graph_wrapper)

        self._acob = activated_obligations

        self.store.insert(activated_obligations)
        self.store.write()
        rdbh.update_db_default(self.graph_wrapper)

        return activated_obligations

    def visualize(self, with_rules=False, filename='graph_tmp.png'):
        gb = vis.GraphBuilder(self.graph_wrapper, self._acob) \
                .data_flow()
        if with_rules:
            gb.rules() \
                    .obligation() \
                    .flow_rules()
        G = gb.build()
        vis.draw_to_file(G, filename)

        return Image(filename=filename)

    def list_all_obligations(self):
        obs = self.store.list()
        return pd.DataFrame(obs, columns=['Triggering process', 'Obligation'])

    def delete_obligation(self, *index):
        if isinstance(index[0], int):
            self.store.delete(*index)
        else:
            self.store.delete(*index[0])
        return self.list_all_obligations()


