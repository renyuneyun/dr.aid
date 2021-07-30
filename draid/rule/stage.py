#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/05/23 17:54:49
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''


class Stage:
    pass


class Imported(Stage):
    pass


class Finished(Stage):
    pass


class Processing(Stage):
    pass


stage_mapping = {
        Imported: 'import',
        Finished: 'finish',
        Processing: 'processing',
        }

