import json
import sys
import unittest

from server import Server


def capture_stream(stream='stdout', echo=False):
    _original_stream = getattr(sys, stream)

    class CapturedStream(object):
        def __init__(self):
            self.lines = list()

        def write(self, line):
            self.lines.append(line.strip())

            if echo:
                _original_stream.write(line)

        def dumps(self):
            return '\n'.join(str(line.strip()) for line in self.lines if line)

    class CapturedContext(object):
        def __enter__(self):
            capture = CapturedStream()

            setattr(sys, stream, capture)

            return capture

        def __exit__(self, *args, **kwargs):
            setattr(sys, stream, _original_stream)

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

        with capture_stream() as sout:
            response = self.client.post('/testing',
                                        headers=self._headers, data=json.dumps(body),
                                        content_type='application/json')

            self.assertEqual(expected_status_code, response.status_code)

            return sout.dumps()
