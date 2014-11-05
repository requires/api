requires.io API
---------------

.. image:: https://requires.io/github/requires/api/requirements.svg?branch=master
   :target: https://requires.io/github/requires/api/requirements/?branch=master
   :alt: Requirements Status

Install package:

.. code-block:: text

    pip install requires.io

Create or update a repository:

.. code-block:: text

    requires.io update-repo -t MY_TOKEN -r MY_REPO (--public | --private)

Create or update a branch:

.. code-block:: text

    requires.io update-branch -t MY_TOKEN -r MY_REPO -n MY_BRANCH /path/to/my/sources

Create or update a tag:

.. code-block:: text

    requires.io update-tag -t MY_TOKEN -r MY_REPO -n MY_TAG /path/to/my/sources

Monitor a site:

* freeze the current environment with pip
* hostname is the default site name

.. code-block:: text

    requires.io update-site -t MY_TOKEN -r MY_REPO

Delete repositories, branches, tags and sites:

.. code-block:: text

    requires.io delete-repo -t MY_TOKEN -r MY_REPO
    requires.io delete-branch -t MY_TOKEN -r MY_REPO -n MY_BRANCH
    requires.io delete-tag -t MY_TOKEN -r MY_REPO -n MY_TAG
    requires.io delete-site -t MY_TOKEN -r MY_REPO -n MY_SITE
