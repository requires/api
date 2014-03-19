# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import glob
import base64
import logging
from optparse import OptionParser

import requests

from . import __version__

log = logging.getLogger(__name__)


def main(args=sys.argv, extra=None, setup_log=True):

    if setup_log:
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    usage = 'usage: %prog [options] path ...'
    version = '%prog ' + __version__
    parser = OptionParser(usage=usage, version=version)
    parser.add_option('-a', '--auth-token', dest='token',
                      help='API token.', metavar='TOKEN')
    parser.add_option('-r', '--repository', dest='repository_name',
                      help='repository name.', metavar='NAME')
    parser.add_option('-p', '--private',
                      action='store_true', dest='private', default=False,
                      help='is the repository private? (default: false)')
    parser.add_option('-b', '--branch', dest='branch_name', default='master',
                      help='branch or tag name. (default: master)', metavar='NAME')
    parser.add_option('-t', '--tag',
                      action='store_true', dest='tag', default=False,
                      help='does the branch name stand for a tag? (default: false)')

    options, args = parser.parse_args(args)

    if not options.token:
        parser.error('authentication token required (use -a or --auth-token option)')
    if not options.repository_name:
        parser.error('repository name required (use -r or --repository option)')
    if not options.branch_name:
        parser.error('branch name required (use -b or --branch)')
    if len(args) == 0:
        parser.error('at least one path required')

    data = options.__dict__
    if extra:
        data.update(extra)

    config = Config(data, args)
    if len(config.paths) == 0:
        parser.error('not file to push')

    client = Client(config)
    client.push()

    log.info('done')

require_io_re = re.compile(r'''
   [/\\](
   setup\.py
   |tox\.ini
   |(buildout|versions)\.cfg
   |req[^/\\]*\.(txt|pip)
   |requirements[/\\][^/\\]*\.(pip|txt)
   )$
''', re.X | re.IGNORECASE)


def _common_index(paths):
    index = 0
    for parts in zip(*[path.split(os.sep) for path in paths]):
        if len(set(parts)) != 1:
            return index
        index += 1


def _to_urls(paths):
    if not paths:
        return []
    if len(paths) == 1:
        return [os.path.basename(next(iter(paths))), ]
    index = _common_index(paths)
    return ['/'.join(path.split(os.sep)[index:]) for path in paths]


class Config(object):

    def __init__(self, options, paths):
        self.options = dict(
            verify=True,
            endpoint='https://requires.io/api/v1/hook/',
        )
        self.options.update(options)
        self.raw_paths = paths
        self._paths = None

    def __getattr__(self, item):
        return self.options[item]

    def _walk(self):
        '''
        Get the paths to process.
        '''
        # Go threw the provided paths
        for raw_path in self.raw_paths:
            # Resolve "*"
            for path in glob.glob(os.path.normpath(os.path.abspath(raw_path))):
                # If this is a folder, look for known files in it
                if os.path.isdir(path):
                    for root, dirs, files in os.walk(path):
                        # Go threw the files to check if they match a known pattern
                        for name in files:
                            current = os.path.join(root, name)
                            if require_io_re.search(current):
                                yield current
                        # Ignore CVS folders
                        if 'CVS' in dirs:
                            dirs.remove('CVS')
                        # Ignore hidden folders
                        ignores = [d for d in dirs if d.startswith('.')]
                        for ignore in ignores:
                            dirs.remove(ignore)
                # If this is a file, add it anyway
                elif os.path.isfile(path):
                    yield path

    @property
    def paths(self):
        if self._paths is None:
            self._paths = set(self._walk())
        return self._paths


class Client(object):

    def __init__(self, config):
        self.config = config

    def build_payload(self):
        payload = {
            'repository': {
                'name': self.config.repository_name,
                'private': self.config.private,
            },
            'branch': {
                'name': self.config.branch_name,
                'tag': self.config.tag,
            },
            'files': [],
        }
        paths = self.config.paths
        for path, url in zip(paths, _to_urls(paths)):
            log.info('add %s to payload', url)
            with open(path, 'rb') as f:
                payload['files'].append({
                    'path': url,
                    'content': base64.b64encode(f.read()),
                })
        return payload

    def push(self):
        payload = self.build_payload()
        headers = {
            'Authorization': 'Token %s' % self.config.token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        log.debug('headers: %s', headers)
        log.debug('payload: %s', payload)
        requests.post(
            self.config.endpoint,
            headers=headers,
            data=json.dumps(payload),
            verify=self.config.verify,
        ).raise_for_status()
