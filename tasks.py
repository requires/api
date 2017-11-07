# -*- coding: utf-8 -*-
from invoke import task


@task
def clean(ctx):
    ctx.run('rm -rf build dist *.egg requires_io/__pycache__ requires_io/*.pyc')


@task
def bumpversion(ctx, part='patch'):
    clean(ctx)
    ctx.run('pip install --upgrade bumpversion')
    ctx.run('bumpversion ' + part)
    ctx.run('git push --tags')


@task
def tox(ctx):
    ctx.run('pip install --upgrade tox')
    ctx.run('tox')


@task
def flake8(ctx):
    ctx.run('pip install --upgrade flake8')
    ctx.run('flake8 --max-line-length=120 requires_io')


@task
def pypi(ctx):
    clean(ctx)
    ctx.run('pip install --upgrade wheel')
    ctx.run('python setup.py clean')
    ctx.run('python setup.py register')
    ctx.run('python setup.py sdist bdist_wheel upload')


@task
def release(ctx, part='patch'):
    bumpversion(ctx, part)
    pypi(ctx)
