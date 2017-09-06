from __future__ import print_function

import sys
import json
import unittest

from actions import action, Action
from server import Server, ConfigurationException


class ActionTest(unittest.TestCase):
    _original_stdout = sys.stdout
    _headers = {'Content-Type': 'application/json'}
    _body = {'testing': True}

    def tearDown(self):
        sys.stdout = self._original_stdout

    def _setup(self, actions):
        server = Server([{'/testing': {'actions': actions}}])

        server.app.testing = True
        self.client = server.app.test_client()

        class MockStdOut(object):
            def __init__(self):
                self.lines = list()

            def write(self, line):
                self.lines.append(line)

            def dump(self):
                return ' '.join(line for line in self.lines if line.strip())

        self.stdout = MockStdOut()
        sys.stdout = self.stdout

    def _invoke(self, actions, expected_status_code=200):
        try:
            self._setup(actions)

            response = self.client.post('/testing',
                                        headers=self._headers, data=json.dumps(self._body),
                                        content_type='application/json')

            self.assertEqual(expected_status_code, response.status_code)

            return self.stdout.dump()

        finally:
            sys.stdout = self._original_stdout

    def test_simple_log(self):
        actions = [{'log': {'message': 'Hello there!'}}]
        output = self._invoke(actions)

        self.assertEqual(output, 'Hello there!')

    def test_log_with_variable(self):
        actions = [{'log': {'message': 'HTTP {{ request.method }} {{ request.path }}'}}]

        output = self._invoke(actions)

        self.assertEqual(output, 'HTTP POST /testing')

    def test_custom_action(self):
        @action('for-test')
        class TestAction(Action):
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def _run(self):
                print(*('%s=%s' % (key, value) for key, value in self.kwargs.items()))

        actions = [{'for-test': {'string': 'Hello', 'number': 12, 'bool': True}}]

        output = self._invoke(actions)

        self.assertIn('string=Hello', output.split())
        self.assertIn('number=12', output.split())
        self.assertIn('bool=True', output.split())

    def test_invalid_action(self):
        actions = [{'invalid': {'Should': 'not work'}}]

        self.assertRaises(ConfigurationException, self._invoke, actions)

    def test_wrong_configuration(self):
        actions = [{'log': {'unknown_argument': 1}}]

        self.assertRaises(ConfigurationException, self._invoke, actions)

