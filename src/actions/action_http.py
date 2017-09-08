import requests

from actions import action, Action


@action('http')
class HttpAction(Action):
    def __init__(self, target, method='POST', headers=None, body=None,
                 output='HTTP {{ response.status_code }} : {{ response.content }}'):

        self.target = target
        self.method = method
        self.headers = headers
        self.body = body
        self.output_format = output

    def _run(self):
        headers = self._headers.copy()

        if self.body and 'Content-Length' not in headers:
            headers['Content-Length'] = str(len(self.body))

        response = requests.request(self.method, self.target, headers=headers, data=self._body)

        print(self._render_with_template(self.output_format, response=response))

    @property
    def _headers(self):
        headers = dict()

        if self.headers:
            for name, value in self.headers.items():
                headers[name] = self._render_with_template(value)

        return headers

    @property
    def _body(self):
        if self.body:
            return self._render_with_template(self.body)

        else:
            return self.body
