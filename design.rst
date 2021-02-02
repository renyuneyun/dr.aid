System design (choices)
############################


Data rule association
=======================

The Prolog reasoner takes the input ports and outputs as identifier for data rules. No matter how it is represented in GraphWrapper, when sending to the reaonser, it needs to associate the rules with the port.

For CWLProv, the GraphWrapper associates data rules with data. So any further queries about data rules are redirected to the data.

For SProv, the GraphWrapper associates data rules with the port. For initial input data and final output data, no particular handling is done at the moment. TODO: Maybe associating that with data files is useful.
