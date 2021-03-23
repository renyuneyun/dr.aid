#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
#   Author  :   renyuneyun
#   E-mail  :   renyuneyun@gmail.com
#   Date    :   19/04/12 18:53:31
#   License :   Apache 2.0 (See LICENSE)
#

'''

'''

import logging, coloredlogs
import logging.config

logging.basicConfig()
coloredlogs.install(level='DEBUG')
logger = logging.getLogger()

import argparse
import yaml

from draid.main import main
from draid import setting


def console_entry():

    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='The URL to the service (SPARQL endpoint), e.g. http://127.0.0.1:3030/prov')
    parser.add_argument('scheme', choices=['SPROV', 'CWLPROV'],
            default=setting.SCHEME, nargs='?',
            help='Set what scheme the target is using. Currently "SPROV" and "CWLPROV" are supported.')
    parser.add_argument('--aio', action='store_true',
            help='Perform ALl-In-One reasoning, rather than reason about one component at a time.')
    parser.set_defaults(aio=False)
    parser.add_argument('--rule-db',
            default=setting.RULE_DB,
            help='The database where the data rules and flow rules are stored. Use comma to separate multiple values. Every database should be a JSON file. If the file does not exist, it will be ignored.')
    parser.add_argument('-w', '--write',
            action='store', nargs='?', default=None, const=True,
            help='Write the reasoning results into database. Optionally specifies the location it writes to. The default location is the last rule database.')  # See https://stackoverflow.com/questions/21997933/how-to-make-an-optional-value-for-argument-using-argparse
    parser.add_argument('--obligation-db',
            default=setting.OBLIGATION_DB,
            help='The obligation database path. If present, the identified obligations will be stored to the database.')
    parser.add_argument("-v", "--verbosity", action="count", default=0,
            help='Increase the verbosity of messages. Overrides "logging.yml"')
    args = parser.parse_args()

    with open('logging.yml','rt') as f:
        config=yaml.safe_load(f.read())
    logging.config.dictConfig(config)
    if args.verbosity:
        logging_level = logging.DEBUG
        if args.verbosity == 1:
            logging_level = logging.CRITICAL
        elif args.verbosity == 2:
            logging_level = logging.ERROR
        elif args.verbosity == 3:
            logging_level = logging.WARN
        elif args.verbosity == 4:
            logging_level = logging.INFO
        elif args.verbosity == 5:
            logging_level = logging.DEBUG
        for handler in logging.getLogger().handlers:
            handler.setLevel(logging_level)
        logger.setLevel(logging_level)
        for logger_name in config['loggers']:
            logging.getLogger(logger_name).setLevel(logging_level)

    main(args.url, args.scheme, args.aio, args.rule_db.split(','), args.write, args.obligation_db)


if __name__ == '__main__':
    console_entry()
