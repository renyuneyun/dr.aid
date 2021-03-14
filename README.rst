dr.Aid 
####################

dr.Aid = DR.Aid = Data Rule Aid

DR.Aid is a framework helping data-users comply with data-use rules (data-governance rules, data policies, etc).


Install and run
=================

This framework is mainly written in Python, and uses SWI-Prolog as the reasoner. To use it, you must have both Python and SWI-Prolog installed.
You need to have Python >= 3.6.

A :code:`setup.py` is present, so you can install DR.Aid via any tool you like.
After installation, you'll find a command-line tool called :code:`draid`.

For example, when using pip, you can do:

.. code:: shell

    pip install .
    draid --help
    
    
Basic usage
================

The repo contains the necessary files to run DR.Aid. Apart from that, you need a running SPARQL endpoint with a supported provenance scheme.
Currently, DR.Aid supports `CWLProv <https://github.com/common-workflow-language/cwlprov>`_ and `SProv <https://github.com/aspinuso/s-provenance>`_.

The basic structure to run DR.Aid from command line is:

.. code:: shell
    
    draid SPARQL_ENDPOINT PROVENANCE_SCHEMA
    
You may often wish to specify the addition rule database to customize the data-use rules associated:

.. code:: shell

    draid --rule-db rule-db.json SPARQL_ENDPOINT PROVENANCE_SCHEMA

Run this command to see additional help:

.. code:: shell

    draid --help
    
Additional information
===========================

The :doc:`design.rst` file contains additional information of the design, such as the database scheme.
