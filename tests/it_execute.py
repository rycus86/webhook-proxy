import base64

from integrationtest_helper import IntegrationTestBase


class ExecuteIntegrationTest(IntegrationTestBase):

    def test_execute_hostname(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /command:
              method: 'POST'

              actions:
                - execute:
                    command: >
                      {{ request.json.command }}
                    output: 'host={{ result }}'
                    shell: false
        """

        self.prepare_file('test-01.yml', config)

        container = self.start_app_container('test-01.yml')

        response = self.request('/command', command='hostname')

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertEqual(output.strip(), 'host=%s' % container.attrs['Config']['Hostname'])

    def test_execute_base64(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /b64:
              method: 'POST'

              actions:
                - execute:
                    command: echo -n "{{ request.json.content }}" | base64 -
                    output: encoded={{ result }}
                    shell: true
        """

        self.prepare_file('test-02.yml', config)

        container = self.start_app_container('test-02.yml')

        response = self.request('/b64', content='testing')

        self.assertEqual(response.status_code, 200)

        response = self.request('/b64', content='sample')

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertIn('encoded=%s' % base64.b64encode('testing'), output)
        self.assertIn('encoded=%s' % base64.b64encode('sample'), output)

