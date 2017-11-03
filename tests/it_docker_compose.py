from integrationtest_helper import IntegrationTestBase


class DockerComposeIntegrationTest(IntegrationTestBase):

    def x_WIP_test_service_names(self):
        project_yaml = """
        version: '2'
        services:

          app:
            image: alpine
            command: sleep 10
          
          web:
            image: alpine
            command: echo "hello"
        """

        self.prepare_file('project/docker-compose.yml', project_yaml)

        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /compose/info:
              actions:
                - docker-compose:
                    project_name: sample
                    directory: /tmp/project
                    $get_services:
                    output: |
                      {% for service in result %}
                      name={{ service.name }}
                      {% endfor %}
        """

        self.prepare_file('test-31.yml', config)

        container = self.start_app_container('test-31.yml')

        response = self.request('/compose/info', data='none')

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertIn('version=%s' % self.DIND_VERSION, output)

