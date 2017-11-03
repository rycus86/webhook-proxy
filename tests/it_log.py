from integrationtest_helper import IntegrationTestBase


class LogIntegrationTest(IntegrationTestBase):

    def test_multi_line_log(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /multi:
              method: 'POST'

              actions:
                - log:
                    message: |
                      This is a multi line log,
                      for the request: {{ request.path }}
        """

        self.prepare_file('test-11.yml', config)

        container = self.start_app_container('test-11.yml')

        response = self.request('/multi', data='none')

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False, tail=20)

        self.assertIn('This is a multi line log,', output)
        self.assertIn('for the request: /multi', output)

    def test_multiple_actions(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /log/messages:
              method: 'POST'

              actions:
                - log:
                - log:
                    message: Plain text
                - log:
                    message: 'With request data: {{ request.json.content }}'
        """

        self.prepare_file('test-12.yml', config)

        container = self.start_app_container('test-12.yml')

        response = self.request('/log/messages', content='sample')

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False, tail=20)

        self.assertIn('Processing /log/messages ...', output)
        self.assertIn('Plain text', output)
        self.assertIn('With request data: sample', output)

