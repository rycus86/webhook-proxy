import random

import docker
from docker.errors import NotFound

from server import ConfigurationException
from unittest_helper import ActionTestBase


class DockerActionTest(ActionTestBase):
    client = docker.DockerClient()

    @classmethod
    def setUpClass(cls):
        cls.client.containers.run(image='alpine', command='echo "Init"', remove=True)

    @classmethod
    def tearDownClass(cls):
        cls.client.api.close()

    def test_list(self):
        container = self.client.containers.run(image='alpine',
                                               command='sleep 10',
                                               detach=True)

        try:
            output = self._invoke({'docker': {'$containers': {'$list': None},
                                              'output': '{% for container in result %}'
                                                        ' container={{ container.name }}'
                                                        '{% endfor %}'}})

            self.assertIn('container=%s' % container.name, output)

        finally:
            container.remove(force=True)

    def test_execute(self):
        name = 'testing_%s' % int(random.randint(1000, 9999))

        self.assertRaises(NotFound, self.client.containers.get, name)

        output = self._invoke({'docker': {'$containers': {'$run': {
            'image': '{{ request.json.incoming.image }}',
            'command': 'sh -c \'{{ request.json.incoming.command }}\'',
            'remove': True}}}},
            body={'incoming': {'image': 'alpine', 'command': 'echo "Hello from Docker"'}})

        self.assertEqual(output, 'Hello from Docker')

    def test_embedded_arguments(self):
        name = 'testing_%s' % int(random.randint(1000, 9999))

        container = self.client.containers.run(image='alpine', command='sleep 10',
                                               name=name, detach=True)

        try:
            output = self._invoke({'docker': {'$containers': {'$list': {'filters': {
                'name': '{{ request.json.incoming.pattern }}',
                'status': '{{ request.json.incoming.status.value }}'}}},
                'output': '{% for container in result %}-{{ container.name }}-{% endfor %}'}},
                body={'incoming': {'pattern': 'testing_', 'status': {'value': 'running'}}})

            self.assertIn('-%s-' % container.name, output)

        finally:
            container.remove(force=True)

    def test_arguments_with_variables(self):
        output = self._invoke([
            {'eval': {'block': '{% set _ = context.set("user", "nobody") %}'}},
            {'docker': {'$containers': {'$run': {
                'image': 'alpine', 'command': 'sh -c "env && echo \"user=$(whoami)\""',
                'user': '{{ context.user }}',
                'remove': True, 'environment': [
                    'UPPER={{ "upper"|upper }}',
                    'LOWER={{ "LOWER"|lower }}'
                ]}},
                'output': '{{ result }}'}}
        ],
            body={'incoming': {'pattern': 'testing_', 'status': {'value': 'running'}}})

        self.assertIn('UPPER=UPPER', output)
        self.assertIn('LOWER=lower', output)
        self.assertIn('user=nobody', output)

    def test_images(self):
        output = self._invoke({'docker': {'$images': {'$list': {
            'filters': {'reference': 'alp*'}}}}})

        self.assertRegexpMatches('alpine\s+latest', output)

    def test_no_invocation(self):
        self.assertRaises(ConfigurationException, self._invoke, {'docker': {'output': 'Uh-oh'}})

    def test_invalid_invocation(self):
        self.assertRaises(ConfigurationException, self._invoke,
                          {'docker': {'$containers': {'$takeOverTheWorld': {'when': 'now'}}}})

    def test_invalid_arguments(self):
        self._invoke(
            {'docker': {'$containers': {'$list': {'filters': {'name': 'test', 'unknown': 1}}}}},
            expected_status_code=500)
