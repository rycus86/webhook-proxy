import json
import unittest

from server import Server


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.server = Server([
            {
                '/testing': {
                    'headers': {
                        'X-Sample': '^ab[0-9]+$'
                    },
                    'body': {
                        'key': 'value',
                        'item': {
                            'prop': '^[0-9]*'
                        }
                    }
                }
            }
        ])

        self.server.app.testing = True
        self.client = self.server.app.test_client()

    def test_valid_request(self):
        headers = {
            'X-Sample': 'ab001'
        }

        body = {
            'key': 'value',
            'item': {
                'prop': '123'
            }
        }

        self._check(200, headers, body)

    def test_invalid_headers(self):
        headers = {
            'X-Sample': 'invalid'
        }

        body = {
            'key': 'value',
            'item': {
                'prop': '123'
            }
        }

        self._check(409, headers, body)

    def test_invalid_body(self):
        headers = {
            'X-Sample': 'ab001'
        }

        body = {
            'key': 'value',
            'item': 'prop'
        }

        self._check(409, headers, body)

    def _check(self, expected_status_code, headers, body):
        response = self.client.post('/testing',
                                    headers=headers, data=json.dumps(body),
                                    content_type='application/json')

        self.assertEqual(expected_status_code, response.status_code)
