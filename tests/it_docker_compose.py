from unittest import skip

from integrationtest_helper import IntegrationTestBase


class DockerComposeIntegrationTest(IntegrationTestBase):
    def setUp(self):
        super(DockerComposeIntegrationTest, self).setUp()

        self.prepare_images('alpine')

    def test_service_names(self):
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
                    directory: /var/tmp/project
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

        self.assertIn('name=app', output)
        self.assertIn('name=web', output)

    def test_scale_service(self):
        project_yaml = """
        version: '2'
        services:
          app:
            image: alpine
            command: sh -c 'echo "app is running" && sleep 3600'
          web:
            image: alpine
            command: sh -c 'echo "web is running" && sleep 3600'
        """

        self.prepare_file('scaling_project/docker-compose.yml', project_yaml)

        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /compose/scaling:
              actions:
                - docker-compose:
                    project_name: scaling
                    directory: /var/tmp/scaling_project
                    $up:
                      detached: true
                - docker-compose:
                    project_name: scaling
                    directory: /var/tmp/scaling_project
                    $get_service:
                      name: '{{ request.json.service }}'
                    output: >
                      {{ context.set("service", result) }}
                - eval:
                    block: >
                      {% set target_num = request.json.num %}
                      {{ context.service.scale(desired_num=target_num) }}
                - docker-compose:
                    project_name: scaling
                    directory: /var/tmp/scaling_project
                    $containers:
                    output: |
                      {% for container in result %}
                      name={{ container.name }}
                      logs={{ container.logs(stdout=true) }}
                      {% endfor %}
        """

        self.prepare_file('test-32.yml', config)

        container = self.start_app_container('test-32.yml')

        response = self.request('/compose/scaling', service='web', num=2)

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertIn('name=scaling_app_1\nlogs=app is running', output)
        self.assertIn('name=scaling_web_1\nlogs=web is running', output)
        self.assertIn('name=scaling_web_2\nlogs=web is running', output)

    @skip('Currently recreating containers rather than restarting them so output checks are off')
    def test_restart_service(self):
        project_yaml = """
        version: '2'
        services:
          app:
            image: alpine
            command: sh -c 'echo "app is running" && sleep 3600'
          web:
            image: alpine
            command: sh -c 'echo "web is running" && sleep 3600'
        """

        self.prepare_file('restarts/docker-compose.yml', project_yaml)

        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /compose/restart:
              actions:
                - docker-compose:
                    project_name: restarts
                    directory: /var/tmp/restarts
                    $up:
                      detached: true
                      scale_override:
                        web: 2
                    output: 'Started the project'
                - docker-compose:
                    project_name: restarts
                    directory: /var/tmp/restarts
                    $up:
                      detached: true
                      scale_override:
                        web: 2
                      service_names:
                        - web
                      strategy: 2
                    output: 'Restarted web'
                - docker-compose:
                    project_name: restarts
                    directory: /var/tmp/restarts
                    $containers:
                      service_names:
                        - app
                    output: >
                      {{ context.set('containers', result) }}
                - eval:
                    block: >
                      {% for container in context.containers %}
                        {{ container.restart(timeout=request.json.timeout) }}
                      {% endfor %}
                      Restarted app
                - docker-compose:
                    project_name: restarts
                    directory: /var/tmp/restarts
                    $containers:
                      stopped: true
                    output: |
                      {% for container in result %}
                        Logging for {{ container.name }}
                        {{ container.logs(stdout=true) }}
                      {% endfor %}
        """

        self.prepare_file('test-33.yml', config)

        container = self.start_app_container('test-33.yml')

        response = self.request('/compose/restart', timeout=1)

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertEqual(output.count('app is running'), 2)
        self.assertEqual(output.count('web is running'), 4)
