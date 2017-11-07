# -*- coding: utf-8 -*-
import codecs
import contextlib
import os
import shutil
import tempfile
import unittest

from requests.exceptions import HTTPError
from requests.status_codes import codes

from requires_io.commands import glob_type_re, GlobType, main, _to_urls


class Repository(object):
    def __init__(self, name):
        self.name = name
        self.root = None

    @contextlib.contextmanager
    def context(self):
        tmp = tempfile.mkdtemp()
        try:
            self.root = os.path.join(tmp, self.name)
            yield self
        finally:
            shutil.rmtree(tmp)
            self.root = None

    def write(self, filename, content, **kwargs):
        path = os.path.normpath(os.path.join(self.root, filename))
        fld = os.path.dirname(path)
        if not os.path.exists(fld):
            os.makedirs(fld)
        with codecs.open(path, kwargs.pop('mode', 'w'), **kwargs) as fd:
            fd.write(content)
            if kwargs.get('clrf', True):
                if not content.endswith('\n'):
                    fd.write('\n')


class TestCase(unittest.TestCase):
    def assertIsNotNone(self, val):  # missing in 2.6
        self.assertTrue(val is not None)

    def assertRaiseForStatus(self, status_code, callable_obj, *args):
        try:
            callable_obj(*args)
        except HTTPError as e:
            self.assertEquals(status_code, e.response.status_code)
        else:
            self.fail('failed to raise status code %d' % status_code)

    def test_re(self):
        self.assertIsNotNone(glob_type_re.search('/foo/bar/setup.py'))
        self.assertIsNotNone(glob_type_re.search('/foo/bar/tox.ini'))
        self.assertIsNotNone(glob_type_re.search('/foo/bar/buildout.cfg'))
        self.assertIsNotNone(glob_type_re.search('/foo/bar/versions.cfg'))
        self.assertIsNotNone(glob_type_re.search('/foo/bar/requirements.txt'))
        self.assertIsNotNone(glob_type_re.search('/foo/bar/requirements.pip'))
        self.assertIsNotNone(glob_type_re.search('/foo/bar/pip.txt'))
        self.assertIsNotNone(glob_type_re.search('/foo/bar/dependences.txt'))
        self.assertIsNotNone(glob_type_re.search('/foo/bar/requirements/prod.txt'))
        self.assertIsNotNone(glob_type_re.search('/foo/bar/requirements/test.pip'))

    def test_to_url(self):
        n = os.path.normpath
        self.assertEquals({}, _to_urls({}))
        self.assertEquals({
            n('/root/foo/bar/setup.py'): 'setup.py',
        }, _to_urls({
            n('/root/foo/bar/setup.py'): 'setup.py',
        }))
        self.assertEquals({
            n('/root/foo/bar/setup.py'): 'setup.py',
            n('/root/foo/bar/requirements/prod.txt'): 'requirements/prod.txt',
        }, _to_urls({
            n('/root/foo/bar/setup.py'): 'setup.py',
            n('/root/foo/bar/requirements/prod.txt'): n('requirements/prod.txt'),
        }))
        self.assertEquals({
            n('/root/foo/bar/requirements/dev.txt'): 'requirements/dev.txt',
            n('/root/foo/bar/requirements/prod.txt'): 'requirements/prod.txt',
        }, _to_urls({
            n('/root/foo/bar/requirements/dev.txt'): n('requirements/dev.txt'),
            n('/root/foo/bar/requirements/prod.txt'): n('requirements/prod.txt'),
        }))
        self.assertEquals({
            n('/root/foo/baz/setup.py'): 'baz/setup.py',
            n('/root/foo/bar/requirements/prod.txt'): 'bar/requirements/prod.txt',
        }, _to_urls({
            n('/root/foo/baz/setup.py'): n('setup.py'),
            n('/root/foo/bar/requirements/prod.txt'): n('requirements/prod.txt'),
        }))
        self.assertEquals({
            n('/root/foo/baz/setup.py'): 'baz/setup.py',
            n('/root/foo/bar/requirements/prod.txt'): 'bar/requirements/prod.txt',
        }, _to_urls({
            n('/root/foo/baz/setup.py'): n('setup.py'),
            n('/root/foo/bar/requirements/prod.txt'): n('requirements/prod.txt'),
        }))

    def assertPaths(self, paths, path):
        self.assertEquals(paths, GlobType()(path))

    def test_paths(self):
        j = os.path.join
        repository = Repository('foo')
        with repository.context():
            repository.write('setup.py', 'hello')
            repository.write(j('requirements', 'prod.txt'), 'hello')
            self.assertPaths({
                j(repository.root, 'setup.py'): 'setup.py',
                j(repository.root, 'requirements', 'prod.txt'): j('requirements', 'prod.txt'),
            }, repository.root)
            self.assertPaths({
                j(repository.root, 'requirements', 'prod.txt'): j('requirements', 'prod.txt'),
            }, j(repository.root, '*', '*.txt'))

    def test_update_site(self):
        self.assertRaiseForStatus(codes.UNAUTHORIZED, main, ['requires.io', 'update-site', '-t', '1234', '-r', 'foo'])


if __name__ == '__main__':
    unittest.main()
