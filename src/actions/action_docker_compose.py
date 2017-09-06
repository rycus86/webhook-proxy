from __future__ import print_function

import docker

from compose.config.config import ConfigFile, ConfigDetails
from compose.config.config import load as load_config
from compose.project import Project

from actions import action, Action
from util import ConfigurationException


@action('docker-compose')
class DockerComposeAction(Action):
    client = docker.DockerClient()

    def __init__(self, project_name, directory, composefile='docker-compose.yml', output='{{ result }}', execute=None, **kwargs):
        # FIXME code duplication with the DockerAction
        config = ConfigFile.from_filename('%s/%s' % (directory, composefile))
        details = ConfigDetails(directory, [config])
        self.project = Project.from_config(project_name, load_config(details), self.client.api)

        self.execution = execute
        self.output_format = output
        
        invocations = kwargs.get('$project', dict())
        self.command, self.arguments = self._split_invocation(invocations, self.project)

    def _split_invocation(self, invocation, target):
        if invocation is None or not(any(key.startswith('$') for key in invocation)):
            return target, invocation if invocation else dict()

        prop, value = next(iter(invocation.items()))
        
        return self._split_invocation(value, getattr(target, prop[1:]))

    def _run(self):
        result = self.command(**self.arguments)

        if self.execution:
            self._render_with_template(self.execution, result=result)

        else:
            print(self._render_with_template(self.output_format, result=result))

