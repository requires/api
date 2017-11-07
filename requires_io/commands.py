# -*- coding: utf-8 -*-
import argparse
import glob
import logging
import os
import re
import socket
import sys

from requires_io import __version__, consts
from requires_io.api import RequiresAPI
from requires_io.draw import draw

log = logging.getLogger(__name__)


class NameType(object):
    def __init__(self):
        self.max_length = 128
        self.pattern = '^[a-zA-Z0-9-_\.]{1,%s}$' % self.max_length

    def __call__(self, value):
        if not value:
            raise argparse.ArgumentTypeError('required')
        if len(value) > self.max_length:
            raise argparse.ArgumentTypeError('at most %d character (it has %d)' % (self.max_length, len(value)))
        if not re.search(self.pattern, value):
            raise argparse.ArgumentTypeError('only alphanumeric and "-_." character allowed')
        return value


class TokenType(object):
    def __call__(self, value):
        if not value:
            raise argparse.ArgumentTypeError('required')
        return value


glob_type_re = re.compile(r'''
   [/\\](
   setup\.py
   |tox\.ini
   |(buildout|versions)\.cfg
   |(req|pip|dep)[\w-]*\.(txt|pip)
   |requirements[/\\][\w-]*\.(pip|txt)
   )$
''', re.X | re.IGNORECASE)


class GlobType(object):
    def __call__(self, value):
        paths = {}
        for path in glob.glob(os.path.normpath(os.path.abspath(value))):
            # If this is a folder, look for known files in it
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    # Go threw the files to check if they match a known pattern
                    for name in files:
                        self._store(paths, os.path.join(root, name))
                    # Ignore CVS folders
                    if 'CVS' in dirs:
                        dirs.remove('CVS')
                    # Ignore hidden folders
                    ignores = [d for d in dirs if d.startswith('.')]
                    for ignore in ignores:
                        dirs.remove(ignore)
            # If this is a file, add it if matches the pattern
            elif os.path.isfile(path):
                self._store(paths, path)
        if not paths:
            raise argparse.ArgumentTypeError('failed to find requirement files matching the pattern for %s' % value)
        return paths

    def _store(self, paths, path):
        match = glob_type_re.search(path)
        if match:
            paths[path] = match.group(1)


class PathType(object):
    def __call__(self, value):
        if not os.path.isfile(value):
            raise argparse.ArgumentTypeError('file does not exist: %s' % value)
        return value


def _common_index(paths):
    index = 0
    for parts in zip(*[os.path.normcase(path).split(os.sep) for path in paths]):
        if len(set(parts)) != 1:
            return index
        index += 1
    return index


def _to_urls(*all_paths):
    paths = {}
    for currents_paths in all_paths:
        paths.update(currents_paths)
    if not paths:
        return {}
    candidates = set()
    for path, basename in paths.items():
        candidates.add(path[:-len(basename) - 1])
    candidates = list(candidates)
    index = _common_index(candidates)
    urls = {}
    for path in paths.keys():
        url = '/'.join(os.path.splitdrive(path)[1].split(os.sep)[index:])
        urls[path] = url
    return urls


class Commands(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='requires.io')
        self.parser.add_argument('--version', action='version', version=__version__)
        self.subparsers = self.parser.add_subparsers()
        self.add_parser_update_repository()
        self.add_parser_delete_repository()
        self.add_parser_update_branch()
        self.add_parser_delete_branch()
        self.add_parser_update_tag()
        self.add_parser_delete_tag()
        self.add_parser_update_site()
        self.add_parser_delete_site()
        self.add_parser_parse()

    def add_argument_paths(self, group):
        group.add_argument('paths', metavar='PATH', type=GlobType(), nargs='+',
                           help='requirement files or folders containing requirement files (glob allowed)')

    def add_parser(self, title, help, executor):
        parser = self.subparsers.add_parser(title, help=help)
        group = parser.add_argument_group('global options')
        group.add_argument('-t', '--token',
                           help='API token (default: REQUIRES_TOKEN environment variable)',
                           type=TokenType(), default=os.getenv('REQUIRES_TOKEN'))
        parser.set_defaults(execute=lambda args: executor(RequiresAPI(args.token), args))
        return parser.add_argument_group('command options')

    def add_repository_parser(self, *args, **kwargs):
        group = self.add_parser(*args, **kwargs)
        group.add_argument('-r', '--repository', metavar='REPO',
                           help='repository name',
                           type=NameType(), required=True)
        return group

    def execute(self, args):
        args = self.parser.parse_args(args)
        if not hasattr(args, 'execute'):
            self.parser.print_usage()
        else:
            args.execute(args)

    # =========================================================================
    # REPOSITORY
    # -------------------------------------------------------------------------
    def add_parser_update_repository(self):
        group = self.add_repository_parser('update-repo', 'update repository',
                                           lambda api, args: api.update_repository(args.repository, args.private))
        subgroup = group.add_mutually_exclusive_group(required=True)
        subgroup.add_argument('--public', dest='private', help='repo public', action='store_false')
        subgroup.add_argument('--private', dest='private', help='repo public', action='store_true')

    def add_parser_delete_repository(self):
        self.add_repository_parser('delete-repo', 'delete repository',
                                   lambda api, args: api.delete_repository(args.repository))

    # =========================================================================
    # BRANCH
    # -------------------------------------------------------------------------
    def add_argument_branch_name(self, group):
        group.add_argument('-n', '--name', help='branch name', type=NameType(), required=True)

    def add_parser_update_branch(self):
        group = self.add_repository_parser('update-branch', 'create or update branch',
                                           lambda api, args: api.update_branch(args.repository, args.name,
                                                                               _to_urls(*args.paths)))
        self.add_argument_branch_name(group)
        self.add_argument_paths(group)

    def add_parser_delete_branch(self):
        group = self.add_repository_parser('delete-branch', 'delete branch',
                                           lambda api, args: api.delete_branch(args.repository, args.name))
        self.add_argument_branch_name(group)

    # =========================================================================
    # TAG
    # -------------------------------------------------------------------------
    def add_argument_tag_name(self, group):
        group.add_argument('-n', '--name', help='tag name', type=NameType(), required=True)

    def add_parser_update_tag(self):
        group = self.add_repository_parser('update-tag', 'create or update tag',
                                           lambda api, args: api.update_tag(args.repository, args.name,
                                                                            _to_urls(*args.paths)))
        self.add_argument_tag_name(group)
        self.add_argument_paths(group)

    def add_parser_delete_tag(self):
        group = self.add_repository_parser('delete-tag', 'delete tag',
                                           lambda api, args: api.delete_tag(args.repository, args.name))
        self.add_argument_tag_name(group)

    # =========================================================================
    # SITE
    # -------------------------------------------------------------------------
    def add_argument_site_name(self, group):
        group.add_argument('-n', '--name', help='site name (default: %s)' % socket.gethostname(),
                           type=NameType(), default=socket.gethostname())

    def add_parser_update_site(self):
        group = self.add_repository_parser('update-site', 'create or update site',
                                           lambda api, args: api.update_site(args.repository, args.name))
        self.add_argument_site_name(group)

    def add_parser_delete_site(self):
        group = self.add_repository_parser('delete-site', 'delete site',
                                           lambda api, args: api.delete_site(args.repository, args.name))
        self.add_argument_site_name(group)

    # =========================================================================
    # REQUIREMENTS
    # -------------------------------------------------------------------------
    def add_parser_parse(self):
        group = self.add_parser('parse', 'parse provided requirements file',
                                lambda api, args: draw(api.get_requirements(args.paths[0], args.file_type)))
        group.add_argument('-k', '--kind', dest='file_type', choices=consts.TYPES,
                           help='type of requirements file (default: let us guess from file name)')
        group.add_argument('paths', metavar='PATH', type=PathType(), nargs=1,
                           help='requirements file to process')


def main(args=sys.argv, setup_log=True):
    if setup_log:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
        logging.getLogger('requests').setLevel(logging.WARNING)
    Commands().execute(args[1:])
