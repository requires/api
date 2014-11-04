# -*- coding: utf-8 -*-
import os
import sys
import json
import base64
import codecs
import logging
import subprocess

import requests


log = logging.getLogger(__name__)

try:
    check_output = subprocess.check_output
except AttributeError:
    def check_output(*args, **kwargs):
        process = subprocess.Popen(stdout=subprocess.PIPE, *args, **kwargs)
        output, unused_err = process.communicate()
        code = process.poll()
        if code:
            cmd = kwargs.get('args')
            if cmd is None:
                cmd = args[0]
            raise subprocess.CalledProcessError(code, cmd, output=output)
        return output


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


class RequiresAPI(object):
    def __init__(self, token, base_url='https://requires.io/api/v2/', verify=True):
        self.token = token
        self.base_url = base_url
        if self.base_url[-1] != '/':
            self.base_url += '/'
        self.verify = verify

    def _get_headers(self, content_type='application/json'):
        return {
            'Authorization': 'Token %s' % self.token,
            'Content-Type': content_type,
            'Accept': 'application/json',
        }

    def _update_reference(self, url, paths):
        payload = []
        for path, relative in zip(paths, _to_urls(paths)):
            log.info('add %s to payload', relative)
            with open(path, 'rb') as f:
                payload.append({
                    'path': relative,
                    'content': base64.b64encode(f.read()),
                })
        requests.put(
            url,
            headers=self._get_headers(),
            data=json.dumps(payload),
            verify=self.verify,
        ).raise_for_status()

    # =========================================================================
    # REPOSITORY
    # -------------------------------------------------------------------------
    def _get_repository_url(self, repository):
        return '%srepos/%s' % (self.base_url, repository)

    def update_repository(self, repository, private):
        payload = dict(
            private=private,
        )
        requests.put(
            self._get_repository_url(repository),
            headers=self._get_headers(),
            data=json.dumps(payload),
            verify=self.verify,
        ).raise_for_status()

    def delete_repository(self, repository):
        log.info('delete repository %s', repository)
        requests.delete(
            self._get_repository_url(repository),
            headers=self._get_headers(),
            verify=self.verify,
        ).raise_for_status()

    # =========================================================================
    # BRANCH
    # -------------------------------------------------------------------------
    def _get_branch_url(self, repository, name):
        return '%s/branches/%s' % (self._get_repository_url(repository), name)

    def update_branch(self, repository, name, paths):
        log.info('update branch %s on repository %s', name, repository)
        return self._update_reference(
            self._get_branch_url(repository, name),
            paths,
        )

    def delete_branch(self, repository, name):
        log.info('delete branch %s on repository %s', name, repository)
        requests.delete(
            self._get_branch_url(repository, name),
            headers=self._get_headers(),
            verify=self.verify,
        ).raise_for_status()

    # =========================================================================
    # TAG
    # -------------------------------------------------------------------------
    def _get_tag_url(self, repository, name):
        return '%s/tags/%s' % (self._get_repository_url(repository), name)

    def update_tag(self, repository, name, paths):
        log.info('update tag %s on repository %s', name, repository)
        return self._update_reference(
            self._get_tag_url(repository, name),
            paths,
        )

    def delete_tag(self, repository, name):
        log.info('delete tag %s on repository %s', name, repository)
        requests.delete(
            self._get_tag_url(repository, name),
            headers=self._get_headers(),
            verify=self.verify,
        ).raise_for_status()

    # =========================================================================
    # SITE
    # -------------------------------------------------------------------------
    def _get_site_url(self, repository, name):
        return '%s/sites/%s' % (self._get_repository_url(repository), name)

    def update_site(self, repository, name):
        log.info('update site %s on repository %s', name, repository)
        command = ['pip', 'freeze', '--local']
        output = check_output(command)
        encoding = getattr(sys.stdout, 'encoding', 'utf-8')
        data = codecs.decode(output, encoding, 'replace')
        requests.put(
            self._get_site_url(repository, name),
            headers=self._get_headers('text/plain'),
            data=data,
            verify=self.verify,
        ).raise_for_status()

    def delete_site(self, repository, name):
        log.info('delete site %s on repository %s', name, repository)
        requests.delete(
            self._get_site_url(repository, name),
            headers=self._get_headers(),
            verify=self.verify,
        ).raise_for_status()