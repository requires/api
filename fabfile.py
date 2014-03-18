# -*- coding: utf-8 -*-
from fabric.api import task, local

@task
def clean():
    local('rm -rf build dist *.egg requires_io/__pycache__ requires_io/*.pyc')

@task
def bumpversion(part='patch'):
    clean()
    local('pip install --upgrade bumpversion')
    local('bumpversion ' + part)
    local('git push --tags')

@task
def tox():
    local('pip install --upgrade tox')
    local('tox')

@task
def flake8():
    local('pip install --upgrade flake8')
    local('flake8 --max-line-length=120 requires_io')

@task
def pypi():
    clean()
    local('pip install --upgrade wheel')
    local('python setup.py clean')
    local('python setup.py register')
    local('python setup.py sdist bdist_wheel upload')

@task
def release(part='patch'):
    bumpversion(part)
    pypi()
