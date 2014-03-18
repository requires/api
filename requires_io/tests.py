# -*- coding: utf-8 -*-
import os
import codecs
import shutil
import unittest
import tempfile
import contextlib

from requires_io.main import Config, require_io_re, _to_urls


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

    def assertIsNotNone(self, val):   # missing in 2.6
        self.assertTrue(val is not None)

    def test_re(self):
        self.assertIsNotNone(require_io_re.search('/foo/bar/setup.py'))
        self.assertIsNotNone(require_io_re.search('/foo/bar/tox.ini'))
        self.assertIsNotNone(require_io_re.search('/foo/bar/buildout.cfg'))
        self.assertIsNotNone(require_io_re.search('/foo/bar/versions.cfg'))
        self.assertIsNotNone(require_io_re.search('/foo/bar/requirements.txt'))
        self.assertIsNotNone(require_io_re.search('/foo/bar/requirements.pip'))
        self.assertIsNotNone(require_io_re.search('/foo/bar/requirements/prod.txt'))
        self.assertIsNotNone(require_io_re.search('/foo/bar/requirements/test.pip'))

    def test_to_url(self):
        self.assertEquals([], _to_urls([]))
        self.assertEquals(['setup.py'], _to_urls(['/foo/bar/setup.py']))
        self.assertEquals(
            ['setup.py', 'requirements/prod.txt'],
            _to_urls(['/foo/bar/setup.py', '/foo/bar/requirements/prod.txt']),
        )

    def assertPaths(self, repository, paths, raw_paths):
        config = Config({}, raw_paths)
        self.assertEquals(paths, config.paths)

    def test_paths(self):
        repository = Repository('foo')
        with repository.context():
            repository.write('setup.py', 'hello')
            repository.write('foobar.txt', 'hello')
            self.assertPaths(repository, set([os.path.join(repository.root, 'setup.py')]), [repository.root, ])
            self.assertPaths(
                repository,
                set([os.path.join(repository.root, 'foobar.txt')]),
                [os.path.join(repository.root, '*.txt'), ],
            )

if __name__ == '__main__':
    unittest.main()
