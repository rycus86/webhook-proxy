import os
import re


class Validator(object):

    def __init__(self, settings):
        if not settings:
            settings = dict()

        self.method = settings.get('method', 'POST')

        self._headers = settings.get('headers', dict())
        self._body = settings.get('body', dict())

    def accept(self, request):
        return self._accept_headers(request.headers, self._headers) and self._accept_body(request.json, self._body)

    def _accept_headers(self, headers, rules):
        for key, rule in rules.items():
            value = headers.get(key, '')

            if not re.match(rule, value):
                print 'Failed to validate the "%s" header: "%s" does not match "%s"' % \
                    (key, value, rule)
                return False

        return True

    def _accept_body(self, data, rules, prefix=''):
        for key, rule in rules.items():
            value = data.get(key, '')
            
            if isinstance(value, list):
                for idx, item in enumerate(value):
                    if not self._check_body(key, item, rule, '%s.%s[%d]' % (prefix, key, idx)):
                        return False

            else:
                if not self._check_body(key, value, rule, '%s.%s' % (prefix, key)):
                    return False

        return True

    def _check_body(self, key, value, rule, property_path):
        if isinstance(rule, dict) and isinstance(value, dict):
            if not self._accept_body(value, rule, property_path):
                return False

        elif not isinstance(rule, (str, unicode)) or not re.match(rule, str(value)):
            print 'Failed to validate %s: "%s" does not match "%s"' % \
                (property_path[1:], value, rule) 
            return False

        return True

