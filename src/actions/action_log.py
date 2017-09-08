from __future__ import print_function

from actions import action, Action


@action('log')
class LogAction(Action):
    def __init__(self, message='Processing {{ request.path }} ...'):
        self.message = message

    def _run(self):
        print(self._render_with_template(self.message))
