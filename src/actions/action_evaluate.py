from __future__ import print_function

from actions import action, Action


@action('eval')
class EvaluateAction(Action):
    def __init__(self, block):
        self.block = block

    def _run(self):
        print(self._render_with_template(self.block))
