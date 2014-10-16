# -*- coding: utf-8 -*-
import os
import re
import sys
import glob
import logging
import argparse
import socket

from . import __version__
from .api import Repository, RequiresAPI


log = logging.getLogger(__name__)


class ReferenceType(object):
    def __init__(self):
        self.max_length = 124
        self.pattern = r'^[a-zA-Z0-9-_\.]$'

    def __call__(self, value):
        if not isinstance(value, basestring):
            raise argparse.ArgumentTypeError('invalid string value: %r' % value)
        if len(value) > self.max_length:
            raise argparse.ArgumentTypeError('at most %d character (it has %d)' % (self.max_length, len(value)))
        if not re.search(self.pattern, value):
            raise argparse.ArgumentTypeError('only alphanumeric character, dash, point and underscore allowed')
        return value


class RepositoryType(object):
    PROVIDERS = ('github', 'bitbucket', 'enterprise')

    def __init__(self, full):
        self.full = full

    def __call__(self, value):
        values = value.split('/')
        if len(values) == 1:
            return Repository(value)
        elif len(values) == 3:
            provider, owner, name = values
            if provider not in self.PROVIDERS:
                raise argparse.ArgumentTypeError(
                    'invalid provider: %r (choose from %s)' % (provider, ', '.join(self.PROVIDERS), ))

            return Repository(name, owner=owner, provider=provider)
        raise argparse.ArgumentTypeError('invalid')


glob_type_re = re.compile(r'''
   [/\\](
   setup\.py
   |tox\.ini
   |(buildout|versions)\.cfg
   |req[^/\\]*\.(txt|pip)
   |requirements[/\\][^/\\]*\.(pip|txt)
   )$
''', re.X | re.IGNORECASE)


class GlobType(object):
    def __call__(self, value):
        paths = set()
        for path in glob.glob(os.path.normpath(os.path.abspath(value))):
            # If this is a folder, look for known files in it
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    # Go threw the files to check if they match a known pattern
                    for name in files:
                        current = os.path.join(root, name)
                        if glob_type_re.search(current):
                            paths.append(current)
                    # Ignore CVS folders
                    if 'CVS' in dirs:
                        dirs.remove('CVS')
                    # Ignore hidden folders
                    ignores = [d for d in dirs if d.startswith('.')]
                    for ignore in ignores:
                        dirs.remove(ignore)
            # If this is a file, add it anyway
            elif os.path.isfile(path):
                paths.append(path)
        if not paths:
            raise argparse.ArgumentTypeError(
                'no requirement file for %s (looks for setup.py, tox.ini, req*.txt ...)' % path)
        return paths


class Commands(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='requires.io')
        self.parser.add_argument('--version', action='version', version=__version__)
        self.subparsers = self.parser.add_subparsers(help='sub-command help')
        self.add_parser_update_repository()
        self.add_parser_delete_repository()
        self.add_parser_update_branch()
        self.add_parser_delete_branch()
        self.add_parser_update_tag()
        self.add_parser_delete_tag()
        self.add_parser_update_site()
        self.add_parser_delete_site()

    def add_argument_paths(self, group):
        group.add_argument('paths', metavar='PATH', type=GlobType(), nargs='+',
                           help='requirement file or folder containing requirement files (glob allowed)')

    def add_parser(self, title, help, executor):
        parser = self.subparsers.add_parser(title, help=help)
        group = parser.add_argument_group('global options')
        group.add_argument('-t', '--token', required=True,
                           help='API token. (default: REQUIRES_TOKEN environment variable)', metavar='TOKEN',
                           default=os.getenv('REQUIRES_TOKEN'))
        group.add_argument('-r', '--repository', metavar='REPO',
                           help='repository format: {github,bitbucket,enterprise}/:owner/:name',
                           type=RepositoryType(True), required=True)
        parser.set_defaults(execute=lambda args: executor(RequiresAPI(args.token), args))
        return parser.add_argument_group('command options')

    def execute(self, args):
        args = self.parser.parse_args(args)
        return args.execute(args)

    # =========================================================================
    # REPOSITORY
    # -------------------------------------------------------------------------
    def add_parser_update_repository(self):
        group = self.add_parser('update-repo', 'update repository',
                                lambda api, args: api.update_repository(args.repository))
        subgroup = group.add_mutually_exclusive_group()
        subgroup.add_argument('--public', action='store_true')
        subgroup.add_argument('--private', action='store_true')
        subgroup = group.add_mutually_exclusive_group()
        subgroup.add_argument('--enabled', action='store_true')
        subgroup.add_argument('--disabled', action='store_true')

    def add_parser_delete_repository(self):
        self.add_parser('delete-repo', 'delete repository',
                        lambda api, args: api.delete_repository(args.repository))

    # =========================================================================
    # BRANCH
    # -------------------------------------------------------------------------
    def add_argument_branch_name(self, group):
        group.add_argument('-n', '--name', metavar='SITE', default=socket.gethostname(), required=True)

    def add_parser_update_branch(self):
        group = self.add_parser('update-branch', 'create or update branch',
                                lambda api, args: api.update_branch(args.repository, args.name, args.paths))
        self.add_argument_branch_name(group)
        self.add_argument_paths(group)

    def add_parser_delete_branch(self):
        group = self.add_parser('delete-branch', 'delete branch',
                                lambda api, args: api.delete_branch(args.repository, args.name))
        self.add_argument_branch_name(group)

    # =========================================================================
    # TAG
    # -------------------------------------------------------------------------
    def add_argument_tag_name(self, group):
        group.add_argument('-n', '--name', help='tag name', metavar='TAG', required=True)

    def add_parser_update_tag(self):
        group = self.add_parser('tag', 'create or update tag',
                                lambda api, args: api.update_tag(args.repository, args.name, args.paths))
        self.add_argument_tag_name(group)
        self.add_argument_paths(group)

    def add_parser_delete_tag(self):
        group = self.add_parser('delete-tag', 'delete tag',
                                lambda api, args: api.delete_tag(args.repository, args.name))
        self.add_argument_tag_name(group)

    # =========================================================================
    # SITE
    # -------------------------------------------------------------------------
    def add_argument_site_name(self, group):
        group.add_argument('-n', '--name', help='site name (default: %s)' % socket.gethostname(),
                           metavar='SITENAME', default=socket.gethostname(), required=True)

    def add_parser_update_site(self):
        group = self.add_parser('site', 'create or update site',
                                lambda api, args: api.delete_tag(args.repository, args.name))
        self.add_argument_site_name(group)

    def add_parser_delete_site(self):
        group = self.add_parser('delete-site', 'delete site',
                                lambda api, args: api.delete_tag(args.repository, args.name))
        self.add_argument_site_name(group)


def main(args=sys.argv, setup_log=True):
    if setup_log:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
    return Commands().execute(args[1:])
