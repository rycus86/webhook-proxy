from __future__ import print_function

import docker

from actions import action, Action
from util import ConfigurationException


@action('docker')
class DockerAction(Action):
    client = docker.DockerClient()

    def __init__(self, output='{{ result }}', execute=None, **invocations):
        if len(invocations) != 1:
            raise ConfigurationException('The "docker" action has to have one invocation')

        self.execution = execute
        self.output_format = output
        self.command, self.arguments = self._split_invocation(invocations, self.client)

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

