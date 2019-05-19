#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/05/09 15:38:09
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Tuple, Union

from .rule import DataRule, DataRuleContainer, Property, PropertyCapsule


@dataclass
class VMapping:
    this: str
    next: str


class MalformedRuleException(Exception):

    def __init__(self, msg=None):
        super().__init__(msg)


class NotFoundException(MalformedRuleException):

    def __init__(self, msg=None):
        super().__init__(msg)


class UnexpectedTerm(MalformedRuleException):

    def __init__(self, found, reason):
        super().__init__(f"<{found}> found but {reason}")


class NotTerminated(MalformedRuleException):

    def __init__(self, msg):
        super().__init__(msg)


class UnexpectedToken(MalformedRuleException):

    def __init__(self, found=None, expected=None, msg=None):
        if not msg:
            if found and expected:
                msg = f"<{found}> found but <{expected}> expected"
            elif found:
                msg = f"<{found}>"
        super().__init__(msg)


class TermFinishingNotEncountered(UnexpectedToken):

    def __init__(self, found, remaining):
        super().__init__(msg="<{}> expected but <{}> found (line: <{}>)".format('.', found, remaining))


TOKEN_RE = re.compile(r'([^\s\(\)\[\]\.,]+|\(|\)|\[|\]|\.|,)')
KEYWORD_RE = re.compile(r'[^\s\(\)\[\]\.,]+')


def _next_token(s: str, must: bool = True) -> Tuple[str, str]:
    ma = TOKEN_RE.search(s)
    if ma:
        token = ma.group(0)
        s = s[ma.end():].lstrip()
    else:
        if must:
            raise NotFoundException(
                "Token expected but nothing found. String: <{}>".format(s))
        else:
            token = ''
    return token, s


def _read_until(s: str, end: str, must: bool = True) -> Tuple[str, str]:
    assert len(end) == 1
    if must:
        i = 0
        while s[i] != end:
            i += 1
            if i >= len(s):
                raise NotFoundException()
        return s[:i+1], s[i+1:].lstrip()
    else:
        raise NotImplementedError()


def _next_paren(s: str, must: bool = True) -> Tuple[str, str]:
    if must:
        if s[0] != '(':
            raise MalformedRuleException(
                "parenthes expected but not found. string is: <{}>".format(s))
        return _read_until(s[1:], ')', must)
    else:
        raise NotImplementedError()


# def _next_square_bracket(s: str, must: bool = True) -> Tuple[str, str]:
#    if must:
#        if s[0] != '[':
#            raise MalformedRuleException("square bracket expected but not found. string is: <{}>".format(s))
#        return _read_until(s[1:], ']', must)
#    else:
#        raise NotImplementedError()


def _next_keyword(s: str, must: bool = True) -> Tuple[str, str]:
    token, s = _next_token(s, must)
    if KEYWORD_RE.match(token):
        return token, s
    else:
        if must:
            raise UnexpectedToken(token, 'keyword')
        else:
            return '', s


def _parse_title_line(line: str) -> Tuple[str, VMapping, Optional[str]]:
    line = line[5:].strip()
    title, line = _next_keyword(line)
    vthis = None
    vnext = None
    i = 0
    while line and i < 3:
        token, line = _next_token(line)
        if token == 'begin':
            break
        line = token + line
        element, line = _next_paren(line)
        elements = element[1:-1].strip().split(' ')
        if len(elements) != 2:
            raise UnexpectedToken(element)
        key, value = elements
        if key == 'this':
            assert not vthis
            vthis = value.strip()
        elif key == 'next':
            assert not vnext
            vnext = value.strip()
        else:
            raise UnexpectedToken(key)
        i += 1
    vmapping = VMapping(vthis if vthis else 'this', vnext if vnext else 'next')
    return title, vmapping, line


def read_obligation(line0: str) -> Tuple[str, Optional[Tuple[str, int]]]:
    _, line = _next_keyword(line0)
    name, line = _next_keyword(line)
    token, line = _next_token(line)
    property_name = None
    property_order = 0
    if token != '.':
        property_name = token
        token, line = _next_token(line)
        if token != '.':
            if token == '[':
                token, line = _next_token(line)
                property_order = int(token)
                token, line = _next_token(line)
                if token != ']':
                    raise UnexpectedToken(token, ']')
            else:
                raise UnexpectedToken(token, '[')
            token, line = _next_token(line)
    if token == '.':
        if property_name:
            return name, (property_name, property_order)
        else:
            return name, None
    raise TermFinishingNotEncountered(token, line0)


def read_property(line0: str) -> Tuple[str, Union[str, List[str]]]:
    _, line = _next_keyword(line0)
    name, line = _next_keyword(line)
    token, line = _next_token(line)
    if token == '[':
        content, line = _read_until(line, ']')
        data = content[:-1]
        property = [r.strip() for r in data.split(',')]
    else:
        property = token  # type: ignore
    token, line = _next_token(line)
    if token == '.':
        return name, property
    raise TermFinishingNotEncountered(token, line0)


def _construct_obligation(name: str, property: Optional[Tuple[str, int]]) -> DataRule:
    if property:
        return DataRule(name, property)
    else:
        return DataRule(name)


def parse_data_rule(data_rule: str) -> DataRuleContainer:
    lines = list(map(str.strip, data_rule.splitlines(False)))

    i = 0
    while not lines[i] and i < len(lines):
        i += 1
    if i >= len(lines):
        raise MalformedRuleException('no start of rule found')
    starting = lines[i]
    title, vmapping, remaining = _parse_title_line(starting)
    assert not remaining

    obligations: List[Tuple[str, Optional[Tuple[str, int]]]] = []
    pmap: Dict[str, PropertyCapsule] = {}

    for line in lines[i+1:]:
        if not line:
            continue
        line = line.strip()
        if line == 'end':
            rules = []
            for pack in obligations:
                ob = _construct_obligation(*pack)
                rules.append(ob)
            return DataRuleContainer(rules, pmap)
        if line:
            token, line = _next_keyword(line)
            if token == 'obligation':
                name, property_ref = read_obligation('obligation ' + line)
                obligations.append((name, property_ref))
            elif token == 'property':
                name, property_data = read_property('property ' + line)
                if name in pmap:
                    raise UnexpectedTerm(name, "property already defined")
                pmap[name] = PropertyCapsule(name, property_data)

    raise NotTerminated(
        "data rule should end with 'end'. Rule: {}".format(lines))