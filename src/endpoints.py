from __future__ import print_function

import re

from flask import request


class Endpoint(object):
    def __init__(self, route, settings):
        if not route:
            raise Exception('An endpoint must have its route defined')

        if not settings:
            raise Exception('An endpoint must have settings')

        self._route = route
        self._method = settings.get('method', 'POST')
        self._headers = settings.get('headers', dict())
        self._body = settings.get('body', dict())

    def setup(self, app):
        @app.route(self._route, endpoint=self._route[1:], methods=[self._method])
        def receive():
            if not request.json:
                return self._make_response(400, 'No payload')

            if not self.accept():
                return self._make_response(409, 'Invalid payload')

            # TODO run actions

            return self._make_response(200, 'OK\n')

    @staticmethod
    def _make_response(status, message):
        return message, status, {'Content-Type': 'text/plain'}

    def accept(self):
        return self._accept_headers(request.headers, self._headers) and self._accept_body(request.json, self._body)

    @staticmethod
    def _accept_headers(headers, rules):
        for key, rule in rules.items():
            value = headers.get(key, '')

            if not re.match(rule, value):
                print('Failed to validate the "%s" header: "%s" does not match "%s"' %
                      (key, value, rule))
                return False

        return True

    def _accept_body(self, data, rules, prefix=''):
        for key, rule in rules.items():
            value = data.get(key, '')

            if isinstance(value, list):
                for idx, item in enumerate(value):
                    if not self._check_body(item, rule, '%s.%s[%d]' % (prefix, key, idx)):
                        return False

            else:
                if not self._check_body(value, rule, '%s.%s' % (prefix, key)):
                    return False

        return True

    def _check_body(self, value, rule, property_path):
        if isinstance(rule, dict) and isinstance(value, dict):
            if not self._accept_body(value, rule, property_path):
                return False

        elif not isinstance(rule, (str, unicode)) or not re.match(rule, str(value)):
            print('Failed to validate "%s": "%s" does not match "%s"' %
                  (property_path[1:], value, rule))
            return False

        return True
