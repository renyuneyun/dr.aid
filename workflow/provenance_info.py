#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/05/07 13:11:14
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from dispel4py.provenance import *


class StockType(ProvenanceType):
    def __init__(self):
        ProvenanceType.__init__(self)
        self.streammeta = []
        self.count = 1
        self.addNamespacePrefix("hft", "http://hft.eu/ns/#")

        def makeUniqueId(self, **kwargs):

            # produce the id
            id = str(uuid.uuid1())

            # Store here the id into the data (type specific):
            if 'data' in kwargs:
                data = kwargs['data']

            # Return
            return id

    def extractItemMetadata(self, data, port):
        try:
            metadata = None
            self.embed = True
            self.streammeta.append({'val': str(data)})

            if (self.count % 1 == 0):

                metadata = deepcopy(self.streammeta)
                self.provon = True
                self.streammeta = []
            else:
                self.provon = False

            self.count += 1
            return metadata

        except Exception as err:
            self.log("Applying default metadata extraction:" +
                     str(traceback.format_exc()))
            self.error = self.error+"Extract Metadata error: " + \
                str(traceback.format_exc())
            return super(StockType, self).extractItemMetadata(data, port)


class ASTGrouped(ProvenanceType):
    def __init__(self):
        ProvenanceType.__init__(self)

    def apply_derivation_rule(self, event, voidInvocation, iport=None, oport=None, data=None, metadata=None):

        if (event == 'write'):
            vv = str(abs(make_hash(tuple([self.getInputAt(
                port=iport, index=x) for x in self.inputconnections[iport]['grouping']]))))
            self.setStateDerivations([vv])

        if (event == 'end_invocation_event' and voidInvocation == False):
            self.discardInFlow()
            self.discardState()

        if (event == 'end_invocation_event' and voidInvocation == True):

            if data != None:

                vv = str(abs(make_hash(tuple([self.getInputAt(
                    port=iport, index=x) for x in self.inputconnections[iport]['grouping']]))))
                self.ignorePastFlow()
                self.update_prov_state(vv, data, metadata={
                                       "LOOKUP": str(vv)}, dep=[vv])
                self.discardInFlow()
                self.discardState()


class IntermediateStatefulOut(ProvenanceType):

    def __init__(self):
        ProvenanceType.__init__(self)

    def apply_derivation_rule(self, event, voidInvocation, iport=None, oport=None, data=None, metadata=None):

        self.ignore_past_flow = False
        self.ignore_inputs = False
        self.stateful = False

        if (event == 'write' and oport == self.STATEFUL_PORT):
            self.update_prov_state(self.STATEFUL_PORT, data, metadata=metadata)

        if (event == 'write' and oport != self.STATEFUL_PORT):
            self.ignorePastFlow()

        if (event == 'end_invocation_event' and voidInvocation == False):

            self.discardInFlow()
            self.discardState()

