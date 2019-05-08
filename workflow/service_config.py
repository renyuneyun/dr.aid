#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/05/07 13:12:10
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

# Store via service
REPOS_URL = 'http://localhost:8082/workflowexecutions/insert'

# Export data lineage via service (REST GET Call on dataid resource /data/<id>/export)
PROV_EXPORT_URL = 'http://localhost:8082/workflowexecutions/'

# Store to local path
PROV_PATH = './prov-files/'

# Size of the provenance bulk before sent to storage or sensor
BULK_SIZE = 20

