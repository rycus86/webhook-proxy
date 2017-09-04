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
        requests.request(self.method, self.target, headers=self._headers, data=self._body)

    @property
    def _headers(self):
        headers = dict()

        for name, value in self.headers.items():
            try:
                value = self._render_with_template(value)

            except:
                pass

            headers[name] = value

        return headers

    @property
    def _body(self):
        return self._render_with_template(self.body)

