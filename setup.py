# -*- coding: utf-8 -*-
import os
import codecs

# allow setup.py to be run from any path
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    import setuptools
except ImportError:
    import ez_setup

    ez_setup.use_setuptools()
from setuptools import setup

install_requires = ['requests >= 2.0.0', ]

try:
    import argparse
except ImportError:
    install_requires.append('argparse >= 1.2.0')

with codecs.open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()
with codecs.open('CHANGES.rst', 'r', 'utf-8') as f:
    history = f.read()

setup(
    name='requires.io',
    version='0.2.6',
    description='Requires.io API',
    long_description=readme + '\n\n' + history,
    url='https://requires.io/',
    author='Requires.io',
    author_email='support@requires.io',
    packages=['requires_io', ],
    include_package_data=False,
    zip_safe=True,
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'requires.io = requires_io.commands:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)

