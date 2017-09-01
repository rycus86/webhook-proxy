import requests

from actions import action, Action


@action('http')
class HttpAction(Action):
    def __init__(self, target, method='POST', headers=None, body=None):
        self.target = target
        self.method = method
        self.headers = headers
        self.body = body

    def _run(self):
        requests.request(self.method, self.target, headers=self.headers, data=self.body)

