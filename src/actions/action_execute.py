from __future__ import print_function

from subprocess import check_output as invoke_command

from actions import action, Action
from util import ConfigurationException


@action('execute')
class ExecuteAction(Action):
    def __init__(self, command, shell=True, output='{{ result }}'):
        self.command = command if isinstance(command, list) else [command]
        self.output_format = output
        
        if isinstance(shell, bool):
            self.shell = 'sh' if shell else None

        elif shell:
            self.shell = shell

    def _run(self):
        if self.shell:
            if isinstance(self.shell, list):
                output = invoke_command(self.shell + [' '.join(self.command)])

            else:
                output = invoke_command([self.shell, '-c', ' '.join(self.command)])

        else:
            output = invoke_command(self.command)

        print(self._render_with_template(self.output_format, result=output))

