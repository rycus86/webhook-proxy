import os
import random

from unittest_helper import ActionTestBase


class DockerComposeActionTest(ActionTestBase):
    def test_executions(self):
        directory = '/tmp/compose_test_%s' % random.randint(1000, 9999)
        os.makedirs(directory)

        with open('%s/docker-compose.yml' % directory, 'w') as composefile:
            composefile.write("version: '2'     \n"
                              "services:        \n"
                              "  cmps_one:      \n"
                              "    image: alpine        \n"
                              "    command: sleep 10    \n"
                              "    stop_signal: KILL    \n"
                              "  cmps_two:      \n"
                              "    image: alpine        \n"
                              "    command: sleep 10    \n"
                              "    stop_signal: KILL    \n")

        try:
            output = self._invoke([
                {'docker-compose': {
                    'project_name': 'testing',
                    'directory': directory,
                    '$up': {
                        'detached': True
                    },
                    'output': 'Compose containers:\n'
                              '{% for container in result %}'
                              '-C- {{ container.name }}\n'
                              '{% endfor %}'
                }},
                {'docker-compose': {
                    'project_name': 'testing',
                    'directory': directory,
                    '$down': {
                        'remove_image_type': False,
                        'include_volumes': True
                    }
                }}
            ])

            self.assertIn('-C- testing_cmps_one_1', output)
            self.assertIn('-C- testing_cmps_two_1', output)

        finally:
            os.remove('%s/docker-compose.yml' % directory)
            os.rmdir(directory)
