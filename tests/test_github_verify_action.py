from unittest_helper import ActionTestBase

import os


class ExecuteActionTest(ActionTestBase):
    def setUp(self):
        self.original_headers = self._headers

    def tearDown(self):
        self._headers = self.original_headers

    def test_successful_github_webhook(self):
        self._headers['X-Hub-Signature'] = 'sha1=28fdad22dac5d0a631b5ead69dbb05e43b685d6e'

        with open(os.path.join(os.path.dirname(__file__), 'github/webhook.json')) as webhook:
            output = self._invoke({'github-verify': {
                'secret': 'TopSecret'
            }}, final_body=webhook.read())

        self.assertEqual(output, 'GitHub webhook successfully validated')

    def test_invalid_github_hash_algorithm(self):
        self._headers['X-Hub-Signature'] = 'md5=a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0'

        with open(os.path.join(os.path.dirname(__file__), 'github/webhook.json')) as webhook:
            self._invoke({'github-verify': {
                'secret': 'TopSecret'
            }}, final_body=webhook.read(), expected_status_code=500)

    def test_invalid_github_signature(self):
        self._headers['X-Hub-Signature'] = 'sha1=a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0'

        with open(os.path.join(os.path.dirname(__file__), 'github/webhook.json')) as webhook:
            self._invoke({'github-verify': {
                'secret': 'TopSecret'
            }}, final_body=webhook.read(), expected_status_code=500)

    def test_invalid_github_secret(self):
        self._headers['X-Hub-Signature'] = 'sha1=28fdad22dac5d0a631b5ead69dbb05e43b685d6e'

        with open(os.path.join(os.path.dirname(__file__), 'github/webhook.json')) as webhook:
            self._invoke({'github-verify': {
                'secret': 'ThisIsNotRight'
            }}, final_body=webhook.read(), expected_status_code=500)

    def test_missing_github_header(self):
        with open(os.path.join(os.path.dirname(__file__), 'github/webhook.json')) as webhook:
            self._invoke({'github-verify': {
                'secret': 'NoHeader'
            }}, final_body=webhook.read(), expected_status_code=500)
