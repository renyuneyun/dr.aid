#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/06/29 11:53:44
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from rdflib import Graph, URIRef
from rdflib.namespace import NamespaceManager
from typing import Dict, Optional

from draid.defs.exception import IllegalCaseError

from .proto import WELL_KNOWN, Thing, Obligation, get_obligation


def get_url_for_ns(nm, ns):
    return dict(nm.namespaces())[ns]

def get_ns_for_url(nm, url):
    return {v:k for k,v in nm.namespaces()}[url]


class OntologiableString:

    graph = Graph()
    nm = graph.namespace_manager

    def __init__(self, s: str, namespaces: Optional[Dict[str, str]]=None):
        for k, v in WELL_KNOWN.items():
            self.nm.bind(k, v)
        if namespaces:
            for k, v in namespaces.items():
                self.nm.bind(k, v, replace=True)
        self._s = s
        parts = s.split(':')
        if len(parts) == 1:
            self.prefix = None
            self.name = parts[0]
            self._onto = self._get_from_ontology(self.prefix, self.name)
        elif len(parts) == 2:
            self.prefix = parts[0]
            self.name = parts[1]
            self._onto = self._get_from_ontology(self.prefix, self.name)
        else:
            raise IllegalCaseError("String is neither a normal string nor an ontology reference")

    def _get_from_ontology(self, prefix: Optional[str], name: str) -> Thing:
        return NotImplemented

    def get(self) -> Thing:
        return self._onto

    def fully_quantified(self) -> str:
        return self._onto.iri

    def dump(self) -> str:
        # return self._s
        if self.prefix is not None:
            return self.prefix + ':' + self.name
        else:
            return self.name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self._onto != other._onto:
                return False
            return True
        else:
            return NotImplemented

    def __repr__(self):
        if self.prefix is not None:
            return f'{self.prefix}:{self.name}'
        else:
            return f'{self._s}'


class ObligationOntoString(OntologiableString):

    graph = Graph()
    nm = graph.namespace_manager

    def _get_from_ontology(self, prefix: Optional[str], name: str) -> Obligation:
        if prefix is not None:
            onto_url = get_url_for_ns(self.nm, prefix)
        else:
            onto_url = None
        return get_obligation(onto_url, name)
