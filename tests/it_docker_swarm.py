import time


from integrationtest_helper import IntegrationTestBase


class DockerSwarmIntegrationTest(IntegrationTestBase):

    @classmethod
    def setUpClass(cls):
        super(DockerSwarmIntegrationTest, cls).setUpClass()

        cls.prepare_images('alpine')
        cls.dind_container.exec_run('docker swarm init')

    def tearDown(self):
        super(DockerSwarmIntegrationTest, self).tearDown()

        for service in self.remote_client.services.list():
            service.remove()

    def test_list_services(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /swarm/list:
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
                                                     command='sh -c "date +%s ; sleep 3600"')

        self.wait_for_service_start(service, num_tasks=1)

        self.assertGreater(len(self.get_service_logs(service)), 0)

        container = self.start_app_container('test-41.yml')

        response = self.request('/swarm/list', data='none')

        self.assertEqual(response.status_code, 200)

        output = container.logs(stdout=True, stderr=False)

        self.assertIn('s=%s#%s' % (service.name, service.id), output)

    @staticmethod
    def wait_for_service_start(service, num_tasks, max_wait=30):
        for _ in range(max_wait * 2):
            if len(service.tasks()) >= num_tasks:
                if all(task['Status']['State'] == 'running'
                       for task in service.tasks(filters={'desired-state': 'running'})):
                    break

            time.sleep(0.5)

    def get_service_logs(self, service, stdout=True, stderr=False):
        logs = list()

        if self.is_below_version('17.05'):
            for container in self.remote_client.containers.list(filters={'name': service.name}):
                logs.extend(''.join(char for char in container.logs(stdout=stdout, stderr=stderr)).splitlines())

        else:
            logs.extend(''.join(item for item in service.logs(stdout=stdout, stderr=stderr)).splitlines())

        return filter(len, map(lambda x: x.strip(), logs))

    def is_below_version(self, version):
        return map(int, self.DIND_VERSION.split('.')) < map(int, version.split('.'))

