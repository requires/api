Requires.io API
===============

.. image:: https://requires.io/github/requires/api/requirements.svg?branch=master
   :target: https://requires.io/github/requires/api/requirements/?branch=master
   :alt: Requirements Status

Installation
------------

To install, simply:

.. code-block:: bash

    $ pip install requires.io

Usage
-----

Create or update a repository:

.. code-block:: bash

    $ requires.io update-repo -t MY_TOKEN -r MY_REPO (--public | --private)

Create or update a branch:

.. code-block:: bash

    $ requires.io update-branch -t MY_TOKEN -r MY_REPO -n MY_BRANCH /path/to/my/sources

Create or update a tag:

.. code-block:: bash

    $ requires.io update-tag -t MY_TOKEN -r MY_REPO -n MY_TAG /path/to/my/sources

Monitor a site:

* freeze the current environment with pip
* hostname is the default site name

.. code-block:: bash

    $ requires.io update-site -t MY_TOKEN -r MY_REPO

Delete repositories, branches, tags and sites:

.. code-block:: bash

    $ requires.io delete-repo -t MY_TOKEN -r MY_REPO
    $ requires.io delete-branch -t MY_TOKEN -r MY_REPO -n MY_BRANCH
    $ requires.io delete-tag -t MY_TOKEN -r MY_REPO -n MY_TAG
    $ requires.io delete-site -t MY_TOKEN -r MY_REPO -n MY_SITE
