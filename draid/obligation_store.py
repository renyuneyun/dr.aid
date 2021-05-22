# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/03/21 21:58:56
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

import json

from rdflib import URIRef
from typing import Dict, List, Tuple

from draid.rule import ActivatedObligation, Attribute


def _dump_activated_obligation(ob: ActivatedObligation):
    obligated_action = ob.name
    arguments = [ (attr.name, attr.type, attr.value) for attr in ob.attributes ]
    return (obligated_action, arguments)

def _load_activated_obligation(obd) -> ActivatedObligation:
    obligated_action, arguments = obd
    attrs = [ Attribute(name, a_type, a_value) for name, a_type, a_value in arguments ]
    return ActivatedObligation(obligated_action, attrs)


class ObligationStore:
    '''
    The main class to interact with the obligation store.
    The same module contains helper functions for simple tasks, which are wrapped around this class.
    '''

    def __init__(self, filename: str):
        self._filename = filename
        self._obligation_list = []  # type: List[Tuple[URIRef, ActivatedObligation]]
        self.reload()

    def reload(self):
        self._obligation_list = []
        try:
            with open(self._filename) as fd:
                obligation_db_raw = json.load(fd)
            for component_uri_str, ob_item in obligation_db_raw:
                component_uri = URIRef(component_uri_str)
                ob = _load_activated_obligation(ob_item)
                self._obligation_list.append((component_uri, ob))
        except FileNotFoundError:
            pass

    def write(self):
        ob_list_raw = []
        for component_uri, ob in self._obligation_list:
            ob_raw = _dump_activated_obligation(ob)
            ob_list_raw.append((str(component_uri), ob_raw))
        with open(self._filename, 'w') as fd:
            json.dump(ob_list_raw, fd)

    def insert(self, activated_obligations: Dict[URIRef, List[ActivatedObligation]]) -> None:
        for component_uri, ob_list in activated_obligations.items():
            for ob in ob_list:
                ob_item = (component_uri, ob)
                if ob_item not in self._obligation_list:
                    self._obligation_list.append((component_uri, ob))

    def list(self):
        return self._obligation_list

    def delete(self, index):
        self._obligation_list = [ob for i, ob in enumerate(self._obligation_list) if ob != index]

    def find(self, component):
        return []


def insert_to_store(activated_obligations: Dict[URIRef, List[ActivatedObligation]], filename: str) -> None:
    ob_store = ObligationStore(filename)
    ob_store.insert(activated_obligations)
    ob_store.write()


def read_from_store(filename: str) -> List[Tuple[URIRef, List[ActivatedObligation]]]:
    ob_store = ObligationStore(filename)
    return ob_store.list()
