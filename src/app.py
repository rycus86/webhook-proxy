from flask import Flask, request
import argparse
import sys
import re
import json
import os


class Validator(object):

    def __init__(self, rule):
        if os.path.exists(rule):
            with open(rule, 'r') as rule_file:
                self._rule = json.load(rule_file)

        else:
            self._rule = json.loads(rule)

    def accept(self, data):
        return self._accept(data, self._rule)

    def _accept(self, data, rules, prefix=''):
        for key, rule in rules.items():
            value = data.get(key, '')
            
            if isinstance(value, list):
                for idx, item in enumerate(value):
                    if not self._check(key, item, rule, '%s.%s[%d]' % (prefix, key, idx)):
                        return False

            else:
                if not self._check(key, value, rule, '%s.%s' % (prefix, key)):
                    return False

        return True

    def _check(self, key, value, rule, property_path):
        if isinstance(rule, dict) and isinstance(value, dict):
            if not self._accept(value, rule, property_path):
                return False

        elif not isinstance(rule, (str, unicode)) or not re.match(rule, str(value)):
            print 'Failed to validate %s: "%s" does not match "%s"' % \
                (property_path[1:], value, rule) 
            return False

        return True


class Server(object):

    def __init__(self, args):
        self.app = None
        self._setup_server()

        settings = self._parse_args(args)

        self.validator = Validator(settings.validator)

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(description='Webhook receiver proxy')
        
        parser.add_argument('--validator', required=True,
                            help='JSON with regex')
        
        print 'parsing', args
        return parser.parse_args(args)

    def _setup_server(self):
        app = Flask(__name__)

        @app.route('/', methods=['POST'])
        @app.route('/<path:path>', methods=['POST'])
        def receive(**kwargs):
            if not request.json:
                return 'No payload', 400

            if not self.validator.accept(request.json):
                return 'Invalid payload', 409
            
            # print 'Payload:', request.json

            # TODO run action

            return 'OK', 200

        self.app = app

    def run(self):
        self.app.run(host='0.0.0.0', port=9999)


if __name__ == '__main__':
    server = Server(sys.argv[1:])
    server.run()

