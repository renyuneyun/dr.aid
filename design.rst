System design (choices)
############################


Rule database
===============

The general structure of a valid rule database is a series of matchers, against the graph id, the object id, the process, etc. The structure of a valid rule database looks like this (everything starting from # is a comment; everything fully upper case is for the user to replace):

.. code:: json

    {
    	"data_rules": {
    		"": {  # Match any graph. It may be overritten by the ones with specific graph id
    			"uri": {  # Match the uri of a data item (in the provenance)
    				"SOME-URI-AS-YOU-WISH": "THE-DATA-RULE"
    			# },
    			# # Not yet implemented
    			#  "path": {  # Match the path of the data item
    			#  	"SOME-PATH-NAME": "THE-DATA-RULE"
    			}
    		},
    		"GRAPH-ID": {  # Match the ID of the graph
    			"uri": {  # Match the uri of a data item (in the provenance)
    				"SOME-URI-AS-YOU-WISH": "THE-DATA-RULE"
    			# },
    			# # Not yet implemented
    			#  "path": {  # Match the path of the data item
    			#  	"SOME-PATH-NAME": "THE-DATA-RULE"
    			}
    		}
    	},
    	"imported_rules": {
    		"": {  # Match any graph. It may be overritten by the ones with specific graph id
    			"uri": {  # Match the uri of a process (in the provenance)
    				"SOME-URI-AS-YOU-WISH": "THE-DATA-RULE"
    			},
    			"function": {  # Match the function name of the process
    				"SOME-FUNCTION-NAME": "THE-DATA-RULE"
    			}
    		},
    		"GRAPH-ID": {  # Match the ID of the graph
    			"uri": {  # Match the uri of a process (in the provenance)
    				"SOME-URI-AS-YOU-WISH": "THE-DATA-RULE"
    			},
    			"function": {  # Match the function name of the process
    				"SOME-FUNCTION-NAME": "THE-DATA-RULE"
    			}
    		}
    	},
    	"flow_rules": {
    		"": {  # Match any graph. It may be overritten by the ones with specific graph id
    			"uri": {  # Match the uri of a process (in the provenance)
    				"SOME-URI-AS-YOU-WISH": "THE-FLOW-RULE"
    			},
    			"function": {  # Match the function name of the process
    				"SOME-FUNCTION-NAME": "THE-FLOW-RULE"
    			}
    		},
    		"GRAPH-ID": {  # Match the ID of the graph
    			"uri": {  # Match the uri of a process (in the provenance)
    				"SOME-URI-AS-YOU-WISH": "THE-FLOW-RULE"
    			},
    			"function": {  # Match the function name of the process
    				"SOME-FUNCTION-NAME": "THE-FLOW-RULE"
    			}
    		}
    	}
    }

Not every element need to present in the database. Anything unexpected may be removed.

When adding new data rules into the database as a result of the reasoning, it will be added to :code:`{"data_rule": {"": {"uri": {"DATA-ITEM-ID": "DATA-RULE"}}}}` .


Data rule association
=======================

The Prolog reasoner takes the input ports and outputs as identifier for data rules. No matter how it is represented in GraphWrapper, when sending to the reaonser, it needs to associate the rules with the port.

For CWLProv, the GraphWrapper associates data rules with data. So any further queries about data rules are redirected to the data.

For SProv, the GraphWrapper associates data rules with the port. For initial input data and final output data, no particular handling is done at the moment. TODO: Maybe associating that with data files is useful.
