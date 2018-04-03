import os
import json as jsonlib
import time

import actions.replay_helper as helper

from actions import action, Action

from unittest_helper import ActionTestBase, capture_stream


class ReplayHelperTest(ActionTestBase):
    path = '.unittest-test.db'

    def setUp(self):
        os.environ['REPLAY_DATABASE'] = self.path

        if os.path.exists(self.path):
            os.remove(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

        del os.environ['REPLAY_DATABASE']

    def test_with_read_only_db(self):
        with helper.read_only_db(self.path) as db:
            result = db.execute('SELECT 1').fetchone()
            self.assertEqual(1, result[0])

    def test_with_read_write_db(self):
        with helper.read_write_db(self.path) as db:
            db.execute('CREATE TABLE test (value integer)')
            db.execute('INSERT INTO test VALUES (?)', (1,))
            db.commit()

            result = db.execute('SELECT * FROM test').fetchone()
            self.assertEqual(1, result[0])

        with helper.read_only_db(self.path) as db:
            result = db.execute('SELECT * FROM test').fetchone()
            self.assertEqual(1, result[0])

    def test_replay(self):
        import requests

        helper.initialize()

        # give it some time to start up
        time.sleep(1)

        # use the Flask test client instead of requests
        original_requests_request = requests.request

        def test_request(method, url, headers, json):
            self.assertTrue(url.endswith('/testing'), msg='Unexpected URL: %s' % url)
            self.assertIn('testing', json)
            self.assertEqual(json['testing'], True)

            return self._client.open(url, method=method, headers=headers, data=jsonlib.dumps(json))

        requests.request = test_request

        try:
            invocations = []

            @action('remember')
            class RememberAction(Action):
                def _run(self):
                    invocations.append(1)

            self._invoke([
                {
                    'log': {
                        'message': 'Invoked the testing endpoint'
                    },
                    'remember': {},
                    'eval': {
                        'block': '{{ replay(0.33) }}'
                    }
                }
            ])

            self.assertEqual(1, sum(invocations))

            with capture_stream(echo=False):
                time.sleep(2)

                self.assertGreater(sum(invocations), 1)

        finally:
            requests.request = original_requests_request
            helper.shutdown()
