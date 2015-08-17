#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#
# Library: pydas
#
# Copyright 2010 Kitware, Inc., 28 Corporate Dr., Clifton Park, NY 12065, USA.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################

"""
Will version pydas. Takes argument of [major|minor|patch] with no argument
resulting a default of patch.
"""

from __future__ import print_function

import getopt
import re
import sys

version_types = ['major', 'minor', 'patch']
release_types = ['major', 'minor', 'patch']


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def version(versioner):
    conf_lines = []
    conf = open('docs/conf.py')

    for line in conf:
        if versioner != 'patch':
            match = re.match('^version = \'([0-9]*).([0-9]*)\'$', line)

            if match is not None:
                ver = {'major': match.group(1), 'minor': match.group(2)}
                ver[versioner] = str(int(ver[versioner]) + 1)

                if versioner == 'major':
                    ver['minor'] = '0'
                line = 'version = \'{0}.{1}\'\n'.format(ver['major'],
                                                        ver['minor'])

        match = re.match('^release = \'([0-9]*).([0-9]*).([0-9]*)\'$', line)

        if match is not None:
            rel = {'major': match.group(1),
                   'minor': match.group(2),
                   'patch': match.group(3)}
            rel[versioner] = str(int(rel[versioner]) + 1)

            if versioner == 'major':
                rel['minor'] = '0'
                rel['patch'] = '0'

            if versioner == 'minor':
                rel['patch'] = '0'

            line = 'release = \'{0}.{1}.{2}\'\n'.format(rel['major'],
                                                        rel['minor'],
                                                        rel['patch'])

        conf_lines.append(line)

    conf.close()
    conf = open('docs/conf.py', 'w')
    conf.write(''.join(conf_lines))
    conf.close()

    new_version = None
    old_version = None
    init_lines = []
    init = open('pydas/__init__.py')

    for line in init:
        match = re.match('^__version__ = \'([0-9]*).([0-9]*).([0-9]*)\'$', line)

        if match is not None:
            ver = {'major': match.group(1),
                   'minor': match.group(2),
                   'patch': match.group(3)}
            old_version = '{0}.{1}.{2}'.format(ver['major'], ver['minor'],
                                               ver['patch'])
            ver[versioner] = str(int(ver[versioner]) + 1)

            if versioner == 'major':
                ver['minor'] = '0'
                ver['patch'] = '0'

            if versioner == 'minor':
                ver['patch'] = '0'
            new_version = '{0}.{1}.{2}'.format(ver['major'], ver['minor'],
                                               ver['patch'])

            line = "__version__ = \'%s\'\n" % new_version

        init_lines.append(line)

    init.close()
    init = open('pydas/__init__.py', 'w')
    init.write(''.join(init_lines))
    init.close()

    setup_lines = []
    setup = open('setup.py')

    for line in setup:
        match = re.match('^      version=\'([0-9]*).([0-9]*).([0-9]*)\',$', line)

        if match is not None:
            ver = {'major': match.group(1),
                   'minor': match.group(2),
                   'patch': match.group(3)}
            old_version = '{0}.{1}.{2}'.format(ver['major'], ver['minor'],
                                               ver['patch'])
            ver[versioner] = str(int(ver[versioner]) + 1)
            if versioner == 'major':
                ver['minor'] = '0'
                ver['patch'] = '0'

            if versioner == 'minor':
                ver['patch'] = '0'

            new_version = '{0}.{1}.{2}'.format(ver['major'], ver['minor'],
                                               ver['patch'])

            line = '      version=\'{0}\',\n'.format(new_version)

        setup_lines.append(line)

    setup.close()
    setup = open('setup.py', 'w')
    setup.write(''.join(setup_lines))
    setup.close()

    print('updated version from {0} to {1}'.format(old_version, new_version))


def main(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        try:
            opts, args = getopt.getopt(argv[1:], 'h', ['help'])
        except getopt.error as msg:
            raise Usage(msg)

        if len(args) == 0:
            versioner = 'patch'
        else:
            if args[0] not in version_types:
                raise Usage('argument must be [major|minor|patch]')

            versioner = args[0]

        version(versioner)

    except Usage as err:
        print(err.msg, sys.stderr)
        print('for help use --help', sys.stderr)
        print('usage: python version.py [major|minor|patch], no argument '
              'defaults to patch')
        return 2


if __name__ == '__main__':
    sys.exit(main())
