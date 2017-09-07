from unittest_helper import capture_stdout, ActionTestBase

import random
import docker

from server import Server, ConfigurationException


class DockerActionTest(ActionTestBase):
    client = docker.DockerClient()
    
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
        
        self.assertRaises(docker.errors.NotFound, self.client.containers.get, name)

        output = self._invoke({'docker': {'$containers': {'$run': {
            'image': '{{ request.json.incoming.image }}',
            'command': 'sh -c \'{{ request.json.incoming.command }}\'',
            'remove': True}}}}, 
            body={'incoming': {'image': 'alpine', 'command': 'echo "Hello from Docker"'}})

        self.assertEqual(output, 'Hello from Docker')

