import sys
import json
import unittest

from server import Server


_original_stdout = sys.stdout


def capture_stdout(echo=False):
    class CapturedStream(object):
        def __init__(self):
            self.lines = list()

        def write(self, line):
            self.lines.append(line.strip())

            if echo:
                _original_stdout.write(line)

        def dumps(self):
            return '\n'.join(line for line in self.lines if line)

    class CapturedContext(object):
        def __enter__(self):
            capture = CapturedStream()

            sys.stdout = capture

            return capture

        def __exit__(self, *args, **kwargs):
            sys.stdout = _original_stdout

    return CapturedContext()


class ActionTestBase(unittest.TestCase):
    _headers = {'Content-Type': 'application/json'}
    _body = {'testing': True}
    
    def _invoke(self, actions, expected_status_code=200, body=None):
        if not isinstance(actions, list):
            actions = [actions]

        if not body:
            body = self._body

        server = Server([{'/testing': {'actions': actions}}])

        server.app.testing = True
        self.client = server.app.test_client()

        with capture_stdout() as sout:
            response = self.client.post('/testing',
                                        headers=self._headers, data=json.dumps(body),
                                        content_type='application/json')

            self.assertEqual(expected_status_code, response.status_code)

            return sout.dumps()

