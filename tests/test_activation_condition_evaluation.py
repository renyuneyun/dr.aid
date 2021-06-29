#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/05/14 11:20:04
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

import pytest

from draid.rule.activation import (
        ActivationCondition,
        EqualAC,
        NEqualAC,
        Never,
        Connective,
        And,
        Or,
        Not,
        )
from draid.rule.stage import (
        Imported,
        Finished,
        Processing,
        )


on_any = EqualAC('action', '*')
on_publish = EqualAC('action', 'publish')
when_import = EqualAC('stage', 'import')
on_not_any = NEqualAC('action', '*')
on_not_publish = NEqualAC('action', 'publish')
when_not_import = NEqualAC('stage', 'import')
never = Never()


@pytest.mark.parametrize('ac, expect, function, stage', [
    (on_publish, True, 'publish', Processing()),
    (on_publish, False, 'average', Processing()),
    (on_any, True, 'publish', Processing()),
    (on_any, True, 'average', Processing()),
    (when_import, True, 'test', Imported()),
    (when_import, False, 'test', Finished()),
    ])
def test_equal_ac(ac, expect, function, stage, info={}):
    assert ac.is_met(stage, function, info) == expect


@pytest.mark.parametrize('ac, expect, function, stage', [
    (on_not_publish, False, 'publish', Processing()),
    (on_not_publish, True, 'average', Processing()),
    (on_not_any, False, 'publish', Processing()),
    (on_not_any, False, 'average', Processing()),
    (when_not_import, False, 'aaa', Imported()),
    (when_not_import, True, 'aaa', Finished()),
    ])
def test_nequal_ac(ac, expect, function, stage, info={}):
    assert ac.is_met(stage, function, info) == expect


@pytest.mark.parametrize('function, stage', [
    ('publish', Processing()),
    ('average', Processing()),
    ('not publish', Processing()),
    ('aaa', Imported()),
    ('aaa', Finished()),
    ])
def test_never(function, stage, info={}):
    ac = never
    assert not ac.is_met(stage, function, info)


@pytest.mark.parametrize('acs, expect, function, stage', [
    ([on_publish], True, 'publish', Processing()),
    ([on_not_publish], False, 'publish', Processing()),
    ([on_publish, on_not_publish], False, 'publish', Processing()),
    ([on_publish, when_import], False, 'average', Processing()),
    ([on_publish, when_import], False, 'publish', Processing()),
    ([on_publish, when_import], True, 'publish', Imported()),
    ([on_publish, when_import], False, 'average', Imported()),
    ])
def test_connective_and(acs, expect, function, stage, info={}):
    ac = And(acs)
    assert ac.is_met(stage, function, info) == expect


@pytest.mark.parametrize('acs, expect, function, stage', [
    ([on_publish], True, 'publish', Processing()),
    ([on_not_publish], False, 'publish', Processing()),
    ([on_publish, on_not_publish], True, 'publish', Processing()),
    ([on_publish, when_import], False, 'average', Processing()),
    ([on_publish, when_import], True, 'publish', Imported()),
    ([on_publish, when_import], True, 'average', Imported()),
    ])
def test_connective_or(acs, expect, function, stage, info={}):
    ac = Or(acs)
    assert ac.is_met(stage, function, info) == expect


@pytest.mark.parametrize('ac0, expect, function, stage', [
    (on_publish, False, 'publish', Processing()),
    (on_publish, True, 'average', Processing()),
    (on_any, False, 'publish', Processing()),
    (on_any, False, 'average', Processing()),
    (when_import, False, 'test', Imported()),
    (when_import, True, 'test', Finished()),
    ])
def test_connective_not(ac0, expect, function, stage, info={}):
    ac = Not(ac0)
    assert ac.is_met(stage, function, info) == expect
