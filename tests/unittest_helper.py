import json
import sys
import unittest

from server import Server
from prometheus_client import REGISTRY


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


def unregister_metrics():
    for collector, names in tuple(REGISTRY._collector_to_names.items()):
        if any(name.startswith('flask_') or
               name.startswith('webhook_proxy_')
               for name in names):

            REGISTRY.unregister(collector)


class ActionTestBase(unittest.TestCase):
    _server = None
    _headers = {'Content-Type': 'application/json'}
    _body = {'testing': True}

    def tearDown(self):
        unregister_metrics()

    def _invoke(self, actions, expected_status_code=200, body=None, **kwargs):
        if not isinstance(actions, list):
            actions = [actions]

        if not body:
            body = self._body

        final_body = kwargs.pop('final_body', json.dumps(body))

        unregister_metrics()

        server = Server([{'/testing': {'actions': actions}}], **kwargs)

        server.app.testing = True
        client = server.app.test_client()

        self._server = server

        with capture_stream() as sout:
            response = client.post('/testing',
                                   headers=self._headers, data=final_body,
                                   content_type='application/json')

            self.assertEqual(expected_status_code, response.status_code)

            return sout.dumps()
