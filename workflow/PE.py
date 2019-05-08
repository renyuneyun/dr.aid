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

from dispel4py.base import create_iterative_chain, GenericPE, ConsumerPE, IterativePE, SimpleFunctionPE, ProducerPE


class NumberProducer(ProducerPE):
    def __init__(self, num=10):
        super().__init__()
        self.num = num

    def _process(self, inputs):
        for i in range(self.num):
            self.write('output', i)


class MultiAverage(GenericPE):

    INPUT = 'input{}'
    OUTPUT = 'output'

    def __init__(self, num, pool_size=5):
        super().__init__()
        self.num = num
        self.pool = []
        self.pool_size = pool_size
        self._add_output(MultiAverage.OUTPUT)
        for i in range(num):
            self._add_input(MultiAverage.INPUT.format(i))

    def _flush(self):
        self.write(MultiAverage.OUTPUT, sum(self.pool) / len(self.pool))
        self.pool.clear()

    def _add_to_pool(self, num):
        self.pool.append(num)
        if len(self.pool) == self.pool_size:
            self._flush()

    def _process(self, inputs):
        if inputs:
            for num in inputs.values():
                self._add_to_pool(num)

    def postprocess(self):
        self._flush()


class Average(MultiAverage):

    INPUT = 'input'
    OUTPUT = MultiAverage.OUTPUT

    def __init__(self, pool_size=None):
        super().__init__()
        self.pool = []
        self.pool_size = pool_size
        self._add_input(Average.INPUT)
        self._add_output(Average.OUTPUT)

    def _process(self, inputs):
        if Average.INPUT in inputs:
            self._process(inputs[Average.INPUT])


class Increase(IterativePE):

    def __init__(self, shift=1):
        super().__init__()
        self.shift = shift

    def _process(self, data):
        return data + self.shift


class Copy(GenericPE):

    INPUT = 'input'
    OUTPUT = 'output{}'

    def __init__(self, num_of_outputs):
        super().__init__()
        self._num = num_of_outputs
        self._add_input(Copy.INPUT)
        for i in range(self._num):
            self._add_output(Copy.OUTPUT.format(i))

    def _process(self, inputs):
        if Copy.INPUT in inputs:
            data = inputs[Copy.INPUT]
            for i in range(self._num):
                self.write(Copy.OUTPUT.format(i), data)


class Redispatch(GenericPE):

    INPUT = 'input{}'
    OUTPUT = 'output{}'

    def __init__(self, num_of_inputs, num_of_outputs):
        super().__init__()
        self._inum = num_of_inputs
        self._onum = num_of_outputs
        for i in range(num_of_inputs):
            self._add_input(Redispatch.INPUT.format(i))
        for i in range(num_of_outputs):
            self._add_output(Redispatch.OUTPUT.format(i))
        self._mapping = {}

    def _process(self, inputs):
        if inputs:
            for iport, data in inputs.items():
                if self._mapping:
                    oports = self._mapping[iport]
                else:
                    oports = [Redispatch.OUTPUT.format(n) for n in range(self._onum)]
                for oport in oports:
                    self.write(oport, data)


