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
    				"SOME-URI-AS-YOU-WISH": {
    					"": "THE-DATA-RULE",  # Uses the default name
    					"IMPORT-PORT-NAME-AS-YOU-WISH": "THE-DATA-RULE"
    				},
    				"SOME-URI-AS-YOU-WISH":  "THE-DATA-RULE"  # Uses the default name
    			},
    			"function": {  # Match the function name of the process
    				"SOME-FUNCTION-NAME": {
    					"": "THE-DATA-RULE",  # Uses the default name
    					"IMPORT-PORT-NAME-AS-YOU-WISH": "THE-DATA-RULE"
    				},
    				"SOME-FUNCTION-NAME":  "THE-DATA-RULE"  # Uses the default name
    			}
    		},
    		"GRAPH-ID": {  # Match the ID of the graph; uses the same schema as above, and omitted for length
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

Link
-----

The rule database may optionally specify an extra information for linking between data items. This is useful when data are from different execution traces and the relation can't be easily detected by the system -- but humans (the operators) know that. The below is how to specify it from the root level:

.. code:: json

    {
    	"link": {
    		"": {
    			"SOME-URI": {
    				"": "SOME-URI",
    				"GRAPH-ID": "SOME-URI"
    			}
    		},
    		"GRAPH-ID": {
    			"SOME-URI": {
    				"": "SOME-URI",
    				"GRAPH-ID": "SOME-URI"
    			}
    		}
    	}
    }

Note every data can only have one link, so in the 4th level (:code:`""` and :code:`"GRAPH-ID"`), only one of them can be specified. If both are specified, the bahviour is not guaranteed.

Remember to put the first one (the output) first (as the key) -- this should make future extension easier.


Data rule association
=======================

The Prolog reasoner takes the input ports and outputs as identifier for data rules. No matter how it is represented in GraphWrapper, when sending to the reaonser, it needs to associate the rules with the port.

For CWLProv, the GraphWrapper associates data rules with data. So any further queries about data rules are redirected to the data.

For SProv, the GraphWrapper associates data rules with the port. For initial input data and final output data, no particular handling is done at the moment. TODO: Maybe associating that with data files is useful.
