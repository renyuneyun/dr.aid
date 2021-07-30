#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/05/21 16:45:48
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from dataclasses import dataclass
from rdflib import URIRef
from typing import Dict, List, Optional


@dataclass
class InitialInfo:
    par: List[str]
    data: Dict[str, List[str]]


@dataclass
class ComponentInfo:
    id: URIRef
    function: Optional[str]
    par: Dict[str, str]
