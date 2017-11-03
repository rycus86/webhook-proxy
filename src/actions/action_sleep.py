import time

from actions import action, Action


@action('sleep')
class SleepAction(Action):
    def __init__(self, seconds):
        self.seconds = seconds

    def _run(self):
        time.sleep(float(self.seconds))
