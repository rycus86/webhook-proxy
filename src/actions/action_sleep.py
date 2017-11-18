import time

from actions import action, Action


@action('sleep')
class SleepAction(Action):
    def __init__(self, seconds, output='Waiting {{ seconds }} seconds before continuing ...'):
        self.seconds = seconds
        self.output_format = output

    def _run(self):
        seconds = float(self._render_with_template(str(self.seconds)))

        print(self._render_with_template(self.output_format, seconds=seconds))

        time.sleep(seconds)

