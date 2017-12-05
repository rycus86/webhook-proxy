import os

from integrationtest_helper import IntegrationTestBase


class ImportIntegrationTest(IntegrationTestBase):

    def test_import(self):
        current_dir = os.path.dirname(__file__)

        with open(os.path.join(current_dir, 'imports/test1/action.py')) as action1:
            self.prepare_file('extra_action_1.py', action1.read())
        with open(os.path.join(current_dir, 'imports/test2/action.py')) as action2:
            self.prepare_file('extra_action_2.py', action2.read())

        config = """
        server:
          host: 0.0.0.0
          port: 9001
          imports:
            - /var/tmp/extra_action_1.py
            - /var/tmp/extra_action_2.py

        endpoints:
          - /imports:
              method: 'POST'

              actions:
                - test1:
                    action: test-1
                - test2:
                    action: test-2
        """

        self.prepare_file('test-61.yml', config)

        container = self.start_app_container('test-61.yml')

        response = self.request('/imports', test='test')

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertIn('action=test-1', output.strip())
        self.assertIn('action=test-2', output.strip())

