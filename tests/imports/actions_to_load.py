from __future__ import print_function

import json

from actions import action, Action


@action('sample')
class SampleAction(Action):
    def __init__(self, **kwargs):
        self.params = kwargs

    def _run(self):
        print('\n'.join('%s=%s' % (key, value) for key, value in self.params.items()))


@action('json')
class JsonAction(Action):
    def __init__(self, **kwargs):
        self.params = kwargs

    def _run(self):
        print(json.dumps(self.params, indent=2))

