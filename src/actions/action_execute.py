from __future__ import print_function

from subprocess import check_output as invoke_command

from actions import action, Action


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
            command = self._render_with_template(' '.join(self.command))

            if isinstance(self.shell, list):
                output = invoke_command(self.shell + [command])

            else:
                output = invoke_command([self.shell, '-c', command])

        else:
            command = map(self._render_with_template, self.command)

            output = invoke_command(command)

        if not isinstance(output, str) and hasattr(output, 'decode'):
            output = output.decode()

        print(self._render_with_template(self.output_format, result=output))
