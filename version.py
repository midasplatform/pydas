"""
Will version Pydas.

Takes arg of [major|minor|patch] with no argument resulting a default of patch.
"""
import sys
import getopt
import re

version_types = ['major', 'minor', 'patch']
release_types = ['major', 'minor', 'patch']


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def version(versioner):

    conf_lines = []
    conf = open('docs/source/conf.py', 'r')
    for line in conf:

        if versioner != 'patch':
            match = re.match('version = \'([0-9]*).([0-9]*)\'', line)
            if match is not None:
                vers = {}
                vers['major'] = match.group(1)
                vers['minor'] = match.group(2)
                vers[versioner] = str(int(vers[versioner]) + 1)
                if versioner == 'major':
                    vers['minor'] = '0'
                line = "version = '" + vers['major'] + "." + vers['minor'] + "'\n"

        match = re.match('release = \'([0-9]*).([0-9]*).([0-9]*)\'', line)
        if match is not None:
                rel = {}
                rel['major'] = match.group(1)
                rel['minor'] = match.group(2)
                rel['patch'] = match.group(3)
                rel[versioner] = str(int(rel[versioner]) + 1)
                if versioner == 'major':
                    rel['minor'] = '0'
                    rel['patch'] = '0'
                if versioner == 'minor':
                    rel['patch'] = '0'

                line = "release = '" + rel['major'] + "." + rel['minor'] + "." + rel['patch'] + "'\n"

        conf_lines.append(line)
    conf.close()

    conf = open('docs/source/conf.py', 'w')
    conf.write(''.join(conf_lines))
    conf.close()

    init_lines = []
    init = open('pydas/__init__.py', 'r')
    for line in init:

        match = re.match('__version__ = \'([0-9]*).([0-9]*).([0-9]*)\'', line)
        if match is not None:
                version = {}
                version['major'] = match.group(1)
                version['minor'] = match.group(2)
                version['patch'] = match.group(3)
                old_version = version['major'] + "." + version['minor'] + "." + version['patch']
                version[versioner] = str(int(version[versioner]) + 1)
                if versioner == 'major':
                    version['minor'] = '0'
                    version['patch'] = '0'
                if versioner == 'minor':
                    version['patch'] = '0'
                new_version = version['major'] + "." + version['minor'] + "." + version['patch']

                line = "__version__ = \'%s\'\n" % new_version

        init_lines.append(line)
    init.close()

    init = open('pydas/__init__.py', 'w')
    init.write(''.join(init_lines))
    init.close()

    setup_lines = []
    setup = open('setup.py', 'r')
    for line in setup:

        match = re.match('version = \'([0-9]*).([0-9]*).([0-9]*)\'', line)
        if match is not None:
                version = {}
                version['major'] = match.group(1)
                version['minor'] = match.group(2)
                version['patch'] = match.group(3)
                old_version = version['major'] + "." + version['minor'] + "." + version['patch']
                version[versioner] = str(int(version[versioner]) + 1)
                if versioner == 'major':
                    version['minor'] = '0'
                    version['patch'] = '0'
                if versioner == 'minor':
                    version['patch'] = '0'
                new_version = version['major'] + "." + version['minor'] + "." + version['patch']

                line = "version = \'%s\'\n" % new_version

        setup_lines.append(line)
    setup.close()

    setup = open('setup.py', 'w')
    setup.write(''.join(setup_lines))
    setup.close()

    print "updated version from %s to %s" % (old_version, new_version)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help"])
        except getopt.error, msg:
            raise Usage(msg)
        version_types = ['major', 'minor', 'patch']
        if(len(args) == 0):
            versioner = 'patch'
        else:
            if args[0] not in version_types:
                raise Usage('argument must be [major|minor|patch]')
            versioner = args[0]
        version(versioner)

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        print "Usage: python version.py [major|minor|patch], no argument defaults to patch"
        return 2

if __name__ == "__main__":
    sys.exit(main())
