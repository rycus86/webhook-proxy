from integrationtest_helper import IntegrationTestBase


class DockerIntegrationTest(IntegrationTestBase):
    
    def test_docker_info(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /info:
              actions:
                - docker:
                    $info:
                    output: 'version={{ result.ServerVersion }}'
        """

        self.prepare_file('test-21.yml', config)

        container = self.start_app_container('test-21.yml')

        response = self.request('/info', data='none')

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertIn('version=%s' % self.DIND_VERSION, output)

    def test_list_containers(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /docker/list:
              actions:
                - docker:
                    $containers:
                      $list:
                        filters:
                          name: '{{ request.json.name }}'
                    output: |
                      {% for container in result %}
                      - {{ container.id }}
                      {% endfor %}
        """

        self.prepare_file('test-22.yml', config)

        container = self.start_app_container('test-22.yml')
        
        response = self.request('/docker/list', name=container.name)

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertIn('- %s' % container.id, output)
        self.assertEqual(len(output.strip().splitlines()), 1)

    def test_run_container(self):
        self.prepare_images('alpine')

        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /run:
              actions:
                - docker:
                    $containers:
                      $run:
                        image: alpine
                        command: 'echo "Alpine says: {{ request.json.message }}"'
                        remove: true
        """

        self.prepare_file('test-23.yml', config)

        container = self.start_app_container('test-23.yml')

        response = self.request('/run', message='testing')

        self.assertEqual(response.status_code, 200)

        response = self.request('/run', message='sample')

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertIn('Alpine says: testing', output)
        self.assertIn('Alpine says: sample', output)

    def test_log_container_status(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /log/status:
              actions:
                - docker:
                    $containers:
                      $get:
                        container_id: '{{ request.json.target }}'
                    output: '{{ context.set("container", result) }}'
                - log:
                    message: >
                      status={{ context.container.status }}
        """

        self.prepare_file('test-24.yml', config)

        container = self.start_app_container('test-24.yml')

        response = self.request('/log/status', target=container.id)

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertIn('status=running', output)

    def test_restart_container(self):
        self.prepare_images('alpine')

        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /docker/restart:
              actions:
                - docker:
                    $containers:
                      $run:
                        image: alpine
                        command: 'sh -c "echo \"{{ request.json.message }}\" && sleep 3600"'
                        detach: true
                    output: '{% set _ = context.set("target", result) %}'
                - eval:
                    block: |
                      {{ context.target.restart(timeout=1) }}
                      {{ context.target.logs(stdout=true, stderr=false) }}
        """

        self.prepare_file('test-25.yml', config)

        container = self.start_app_container('test-25.yml')

        response = self.request('/docker/restart', message='Starting...')

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertIn('Starting...\nStarting...', output)
