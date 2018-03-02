from __future__ import print_function

import docker
import six

from actions import action, Action
from util import ConfigurationException


@action('docker')
class DockerAction(Action):
    client = docker.DockerClient(version='auto')

    def __init__(self, output='{{ result }}', **invocations):
        if len(invocations) != 1:
            raise ConfigurationException('The "%s" action has to have one invocation' % self.action_name)

        self.output_format = output
        self.command, self.arguments = self._split_invocation(invocations, self._target())

    def _target(self):
        return self.client

    def _split_invocation(self, invocation, target):
        if invocation is None or not (any(key.startswith('$') for key in invocation)):
            return target, invocation if invocation else dict()

        prop, value = next(iter(invocation.items()))

        return self._split_invocation(value, getattr(target, prop[1:]))

    def _run(self):
        arguments = self._process_arguments(self.arguments.copy())

        result = self.command(**arguments)

        if result is not None and not isinstance(result, str) and hasattr(result, 'decode'):
            result = result.decode()

        print(self._render_with_template(self.output_format, result=result))

    def _process_arguments(self, current):
        for key, value in current.items():
            if isinstance(value, dict):
                current[key] = self._process_arguments(value.copy())

            elif isinstance(value, list):
                current[key] = [self._render_with_template(item) for item in value]

            elif isinstance(value, six.string_types):
                current[key] = self._render_with_template(value)

        return current
