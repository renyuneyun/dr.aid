#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/05/21 16:48:20
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

import logging

from draid.graph_wrapper import GraphWrapper
from draid.defs.namespaces import NS

from .sparql_helper import Helper

logger = logging.getLogger(__name__)


class AugmentedGraphHelper(Helper):

    def __init__(self, destination):
        super().__init__(destination)

    def write_transformed_graph(self, graph: 'GraphWrapper'):
        '''
        Create / Prune a new graph dedicated to store the old graph + initial rules
        '''
        # TODO
        logger.warning("<write_transformed_graph> Not implemented yet")
        for s, p, o in graph.rdf_graph:
            if p == NS['mine']['rule']:
                logger.info("{} {} {}".format(s, p, o))
