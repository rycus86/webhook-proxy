import json
import threading

import six

if six.PY2:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
else:
    from http.server import HTTPServer, BaseHTTPRequestHandler

from unittest_helper import ActionTestBase, capture_stream


class HttpActionTest(ActionTestBase):
    def setUp(self):
        self.http_server = None

    def tearDown(self):
        if self.http_server:
            self.http_server.shutdown()

    def _start_server(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self._do_ANY()

            def do_POST(self):
                self._do_ANY()

            def do_PUT(self):
                self._do_ANY()

            def _do_ANY(self):
                content_length = int(self.headers.get('Content-Length', '0'))
                if content_length and \
                                self.headers.get('Content-Type', 'application/json') == 'application/json':

                    payload = self.rfile.read(content_length)

                    if not isinstance(payload, str) and hasattr(payload, 'decode'):
                        payload = payload.decode()

                    posted = json.loads(payload)

                else:
                    posted = dict()

                if self.headers.get('X-Fail'):
                    self.send_error(int(self.headers.get('X-Fail')))

                else:
                    self.send_response(200)

                self.end_headers()

                self.wfile.write(six.b('Test finished\n'))

                self.wfile.write(six.b('uri=%s\n' % self.path))
                self.wfile.write(six.b('method=%s\n' % self.command))

                for key, value in self.headers.items():
                    self.wfile.write(six.b('H %s=%s\n' % (key.lower(), value)))

                for key, value in posted.items():
                    if isinstance(value, dict):
                        self.wfile.write(six.b('B %s=%s' % (key, json.dumps(value))))

                    else:
                        self.wfile.write(six.b('B %s=%s\n' % (key, value)))

        self.http_server = HTTPServer(('127.0.0.1', 0), Handler)

        def run_server():
            self.http_server.serve_forever()

        threading.Thread(target=run_server).start()

    def _invoke_http(self, **kwargs):
        self._start_server()

        self.assertIsNotNone(self.http_server)

        port = self.http_server.server_port
        self.assertIsNotNone(port)
        self.assertGreater(port, 0)

        expected_status_code = kwargs.pop('expected_status_code', 200)

        args = kwargs.copy()

        if 'target' not in args:
            args['target'] = 'http://127.0.0.1:%s' % port

        elif args['target'].startswith('/'):
            args['target'] = 'http://127.0.0.1:%s%s' % (port, args['target'])

        return self._invoke({'http': args}, expected_status_code)

    def test_simple_http(self):
        output = self._invoke_http(
            headers={'X-Test': 'Hello'},
            body=json.dumps({'key': 'value'}))

        self.assertIn('method=POST', output)
        self.assertIn('H x-test=Hello', output)
        self.assertIn('B key=value', output)

    def test_put_method(self):
        output = self._invoke_http(
            method='PUT',
            target='/put-test',
            headers={'X-Method': 'PUT'},
            body=json.dumps({'method': 'PUT'}))

        self.assertIn('method=PUT', output)
        self.assertIn('uri=/put-test', output)
        self.assertIn('H x-method=PUT', output)
        self.assertIn('B method=PUT', output)

    def test_get_method(self):
        output = self._invoke_http(
            method='GET',
            target='/some/remote/endpoint',
            headers={'Accept': 'text/plain', 'X-Test': 'test_get_method'})

        self.assertIn('method=GET', output)
        self.assertIn('uri=/some/remote/endpoint', output)
        self.assertIn('H accept=text/plain', output)
        self.assertIn('H x-test=test_get_method', output)

    def test_target_replacement(self):
        output = self._invoke_http(
                target='/some/{{ "remote" }}/endpoint')

        self.assertIn('uri=/some/remote/endpoint', output)

    def test_header_replacement(self):
        output = self._invoke_http(
            headers={'X-Original-Path': '{{ request.path }}'})

        self.assertIn('H x-original-path=/testing', output)

    def test_body_replacement(self):
        output = self._invoke_http(
            body=json.dumps({'original': {'request': {'path': '{{ request.path }}'}}}))

        self.assertIn('B original={"request": {"path": "/testing"}}', output)

    def test_json_output_with_replacement(self):
        output = self._invoke_http(
            json=True,
            body={'original': {'request': {'path': '{{ request.path }}'}}})

        self.assertIn('B original={"request": {"path": "/testing"}}', output)

    def test_output_formatting(self):
        output = self._invoke_http(
            output='HTTP::{{ response.status_code }}')

        self.assertEqual(output, 'HTTP::200')

    def test_content_length_header(self):
        message = 'Hello there!'

        output = self._invoke_http(
            headers={'Content-Type': 'text/plain'},
            body=message)

        self.assertIn('H content-length=%s' % len(message), output)

    def test_404_response(self):
        output = self._invoke_http(headers={'X-Fail': '404'})

        self.assertIn('HTTP 404', output)

    def test_503_response(self):
        output = self._invoke_http(headers={'X-Fail': '503'})

        self.assertIn('HTTP 503', output)

    def test_fail_on_error(self):
        with capture_stream('stderr') as stderr:
            output = self._invoke_http(
                headers={'X-Fail': '500'},
                fail_on_error=True,
                expected_status_code=500
            )

            error = stderr.dumps()

            self.assertIn('ActionInvocationException: HTTP call failed (HTTP 500)', error)

    def test_does_not_fail_on_success(self):
        output = self._invoke_http(
            headers={'X-Fail': '204'},
            output='HTTP::{{ response.status_code }}',
            fail_on_error=True
        )

        self.assertIn('HTTP::204', output)
