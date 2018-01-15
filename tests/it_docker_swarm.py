import time

from integrationtest_helper import IntegrationTestBase


def skip_below_version(version):
    def decorator(f):
        def wrapper(self, *args, **kwargs):
            if map(int, self.DIND_VERSION.split('.')) < map(int, version.split('.')):
                self.skipTest(reason='Skipping %s on version %s (< %s)' % (f.__name__, self.DIND_VERSION, version))
            else:
                f(self, *args, **kwargs)

        return wrapper

    return decorator


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

    @skip_below_version('1.13')
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

    def test_scale_service(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /docker/swarm/scale:
              actions:
                - docker-swarm:
                    $scale:
                      service_id: '{{ request.json.service }}'
                      replicas: '{{ request.json.replicas }}'
        """

        self.prepare_file('test-43.yml', config)

        service = self.remote_client.services.create('alpine',
                                                     name='sample-app',
                                                     command='sh -c "echo \"Starting\" ; sleep 3600"',
                                                     stop_grace_period=1)

        self.wait_for_service_start(service, num_tasks=1)

        self.assertEqual(len(service.tasks()), 1)

        self.start_app_container('test-43.yml')

        response = self.request('/docker/swarm/scale', service='sample-app', replicas=2)

        self.assertEqual(response.status_code, 200)

        self.wait_for_service_start(service, num_tasks=2)

        self.assertGreaterEqual(len(service.tasks(filters={'desired-state': 'running'})), 2)

    def test_update_service(self):
        config = """
        server:
          host: 0.0.0.0
          port: 9001

        endpoints:
          - /docker/swarm/update:
              actions:
                - docker-swarm:
                    $update:
                      service_id: '{{ request.json.service }}'
                      command: '{{ request.json.command }}'
                      labels:
                        label_1: 'sample'
                        label_2: '{{ request.json.label }}'
        """

        self.prepare_file('test-44.yml', config)

        service = self.remote_client.services.create('alpine',
                                                     name='sample-app',
                                                     command='sh -c "echo \"Starting\" ; sleep 3600"',
                                                     stop_grace_period=1)

        self.wait_for_service_start(service, num_tasks=1)

        self.start_app_container('test-44.yml')

        response = self.request('/docker/swarm/update',
                                service='sample-app',
                                command='sh -c "echo \"Updated\" ; sleep 300"',
                                label='testing')

        self.assertEqual(response.status_code, 200)

        self.wait_for_service_start(service, num_tasks=2)

        service.reload()

        self.assertEqual(service.attrs.get('Spec').get('Labels', dict()).get('label_1'), 'sample')
        self.assertEqual(service.attrs.get('Spec').get('Labels', dict()).get('label_2'), 'testing')

        logs = self.get_service_logs(service)

        self.assertIn('Starting', logs)
        self.assertIn('Updated', logs)

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
