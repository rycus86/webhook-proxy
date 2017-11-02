import os
import time
import unittest

import docker
import requests


class IntegrationTestBase(unittest.TestCase):
    DIND_HOST = os.environ.get('DIND_HOST', 'localhost')
    DIND_VERSION = os.environ.get('DIND_VERSION')

    @classmethod
    def setUpClass(cls):
        assert cls.DIND_VERSION is not None

        cls.local_client = docker.DockerClient(os.environ.get('DOCKER_ADDRESS'))

        assert cls.local_client.version() is not None

        cls.build_project()

        cls.dind_container = cls.start_dind_container()

        cls.remote_client = cls.dind_client(cls.dind_container)

        cls.prepare_images('webhook-testing', 'alpine')

    @classmethod
    def tearDownClass(cls):
        cls.remote_client.api.close()

        cls.dind_container.remove(force=True, v=True)

        cls.local_client.api.close()

    @classmethod
    def start_dind_container(cls):
        container = cls.local_client.containers.run('docker:%s-dind' % cls.DIND_VERSION,
                                                    command='--storage-driver=overlay',
                                                    name='webhook-dind-%s' % int(time.time()),
                                                    ports={'2375': None},
                                                    privileged=True, detach=True)

        try:
            for _ in range(10):
                container.reload()

                if container.status == 'running':
                    if container.id in (c.id for c in cls.local_client.containers.list()):
                        break

                time.sleep(0.2)

            port = cls.dind_port(container)

            for _ in range(25):
                try:
                    response = requests.get('http://%s:%s/version' % (cls.DIND_HOST, port))
                    if response and response.status_code == 200:
                        break

                except requests.exceptions.RequestException:
                    pass

                time.sleep(0.2)

            remote_client = cls.dind_client(container)

            assert remote_client.version() is not None

            return container

        except Exception:
            container.remove(force=True, v=True)

            raise

    @classmethod
    def dind_port(cls, container):
        return container.attrs['NetworkSettings']['Ports']['2375/tcp'][0]['HostPort']

    @classmethod
    def dind_client(cls, container):
        return docker.DockerClient('tcp://%s:%s' % (cls.DIND_HOST, cls.dind_port(container)),
                                   version='auto')

    @classmethod
    def prepare_images(cls, *images):
        for tag in images:
            image = cls.local_client.images.get(tag)

            cls.remote_client.images.load(image.save().stream())

            if ':' in tag:
                name, tag = tag.split(':')

            else:
                name, tag = tag, None

            cls.remote_client.images.get(image.id).tag(name, tag=tag)

    @classmethod
    def build_project(cls, tag='webhook-testing'):
        cls.local_client.images.build(
            path=os.path.join(os.path.dirname(__file__), '..'),
            dockerfile='Dockerfile-docker',
            tag=tag,
            rm=True)

    @classmethod
    def prepare_file(cls, filename, contents):
        cls.dind_container.exec_run(['tee', '/tmp/%s' % filename], stdin=True, socket=True).sendall(contents)

