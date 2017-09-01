from __future__ import print_function

import time

from flask import request
from jinja2 import Template

from actions import action, Action


@action('log')
class LogAction(Action):
    def __init__(self, message='Processing {{ request.path }} ...'):
        self.template = Template(message)

    def _run(self):
        print(self.template.render(request=request, timestamp=time.time(), datetime=time.ctime()))

