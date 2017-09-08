from __future__ import print_function

import docker

from actions import action, Action
from util import ConfigurationException


@action('docker')
class DockerAction(Action):
    client = docker.DockerClient()

    def __init__(self, output='{{ result }}', **invocations):
        if len(invocations) != 1:
            raise ConfigurationException('The "docker" action has to have one invocation')

        self.output_format = output
        self.command, self.arguments = self._split_invocation(invocations, self.client)

    def _split_invocation(self, invocation, target):
        if invocation is None or not(any(key.startswith('$') for key in invocation)):
            return target, invocation if invocation else dict()

        prop, value = next(iter(invocation.items()))
        
        return self._split_invocation(value, getattr(target, prop[1:]))

    def _run(self):
        arguments = self._process_arguments(self.arguments.copy())

        result = self.command(**arguments)
        
        print(self._render_with_template(self.output_format, result=result))

    def _process_arguments(self, current):
        for key, value in current.items():
            if isinstance(value, dict):
                current[key] = self._process_arguments(value.copy())

            elif isinstance(value, (str, unicode)):
                current[key] = self._render_with_template(value)

        return current

