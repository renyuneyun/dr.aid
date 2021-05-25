#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   21/05/25 18:03:15
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''
import json

from typing import Any, Optional


def escaped(value: Any) -> Optional[str]:
    if isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    elif value is None:  # `None` may represent different meanings for different elements, so it should be treated separately where it is used
        return None
    raise NotImplementedError(f"Unknown value to be escaped: {value}")


def deescaped(repr: Optional[str]) -> Any:
    if repr is None:
        return None
    try:
        return int(repr)
    except ValueError:
        pass
    try:
        return float(repr)
    except ValueError:
        pass
    try:
        return json.loads(f'"{repr}"')
    except ValueError:
        pass
    raise NotImplementedError(f"Unknown repr to be de-escaped: {repr}")
