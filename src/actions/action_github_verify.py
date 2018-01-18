from __future__ import print_function

import six
import hmac
from hashlib import sha1
from flask import request

from actions import action, Action


@action('github-verify')
class GitHubVerifyAction(Action):
    def __init__(self, secret, output='{{ result }}'):
        self.secret = secret
        self.output_format = output

    def _run(self):
        # based on https://github.com/carlos-jenkins/python-github-webhooks/blob/master/webhooks.py
        secret = str(self._render_with_template(self.secret))
        if six.PY3:
            secret = secret.encode('utf-8')

        header_signature = request.headers.get('X-Hub-Signature')
        if header_signature is None:
            self.error('Missing X-Hub-Signature header')

        sha_name, signature = header_signature.split('=')
        if sha_name != 'sha1':
            self.error('Invalid hashing algorithm')

        mac = hmac.new(secret, msg=request.data, digestmod=sha1)

        if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
            self.error('GitHub webhook validation failed')

        print(self._render_with_template(self.output_format, result='GitHub webhook successfully validated'))
