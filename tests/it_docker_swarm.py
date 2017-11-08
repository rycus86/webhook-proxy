import time


from integrationtest_helper import IntegrationTestBase


class DockerSwarmIntegrationTest(IntegrationTestBase):
    DIND_VERSION = '17.09'

    @classmethod
    def setUpClass(cls):
        super(DockerSwarmIntegrationTest, cls).setUpClass()

        cls.prepare_images('alpine')
        cls.dind_container.exec_run('docker swarm init')

    def tearDown(self):
        super(DockerSwarmIntegrationTest, self).tearDown()

        for service in self.remote_client.services.list():
            service.remove()

    def test_list_services_using_docker_action(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /docker/services/list:
              actions:
                - docker:
                    $services:
                      $list:
                    output: |
                      {% for service in result %}
                        s={{ service.name }}#{{ service.id }}
                      {% endfor %}
        """

        self.prepare_file('test-41.yml', config)

        service = self.remote_client.services.create('alpine',
                                                     name='sample-app',
                                                     command='sh -c "date +%s ; sleep 3600"',
                                                     stop_grace_period=1)

        self.wait_for_service_start(service, num_tasks=1)

        self.assertGreater(len(self.get_service_logs(service)), 0)

        container = self.start_app_container('test-41.yml')

        response = self.request('/docker/services/list', data='none')

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertIn('s=%s#%s' % (service.name, service.id), output)

    def test_restart_service(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /docker/swarm/restart:
              actions:
                - docker-swarm:
                    $restart:
                      service_id: '{{ request.json.service }}'
        """

        self.prepare_file('test-42.yml', config)

        service = self.remote_client.services.create('alpine',
                                                     name='sample-app',
                                                     command='sh -c "echo \"Starting\" ; sleep 3600"',
                                                     stop_grace_period=1)

        self.wait_for_service_start(service, num_tasks=1)

        logs = self.get_service_logs(service)

        self.assertEqual(logs.count('Starting'), 1)

        self.start_app_container('test-42.yml')

        response = self.request('/docker/swarm/restart', service='sample-app')

        self.assertEqual(response.status_code, 200)

        self.wait_for_service_start(service, num_tasks=2)

        logs = self.get_service_logs(service)

        self.assertEqual(logs.count('Starting'), 2)

    @staticmethod
    def wait_for_service_start(service, num_tasks, max_wait=30):
        for _ in range(max_wait * 2):
            if len(service.tasks()) >= num_tasks:
                tasks_to_run = service.tasks(filters={'desired-state': 'running'})

                if len(tasks_to_run) > 0 and all(task['Status']['State'] == 'running' for task in tasks_to_run):
                    break

            time.sleep(0.5)

    def get_service_logs(self, service, stdout=True, stderr=False):
        logs = list()

        for container in self.remote_client.containers.list(all=True, filters={'name': service.name}):
            logs.extend(''.join(char for char in container.logs(stdout=stdout, stderr=stderr)).splitlines())

        return filter(len, map(lambda x: x.strip(), logs))
