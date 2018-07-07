import json
import requests

from actions import action, Action


@action('http')
class HttpAction(Action):
    def __init__(self, target, method='POST', headers=None, body=None, json=False, fail_on_error=False,
                 output='HTTP {{ response.status_code }} : {{ response.content }}'):

        self.target = target
        self.method = method
        self.headers = headers
        self.body = body
        self.json = json
        self.fail_on_error = fail_on_error
        self.output_format = output

    def _run(self):
        headers = self._headers.copy()

        if self.body and 'Content-Length' not in headers:
            headers['Content-Length'] = str(len(self.body))

        response = requests.request(self.method, self._target, headers=headers, data=self._body)

        if self.fail_on_error and response.status_code // 100 != 2:
            self.error('HTTP call failed (HTTP %d)' % response.status_code)

        print(self._render_with_template(self.output_format, response=response))

    @property
    def _target(self):
        return self._render_with_template(self.target)

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
            if self.json:
                return self._render_json(self.body)
            else:
                return self._render_with_template(self.body)
        else:
            return self.body

    def _render_json(self, body):
        return json.dumps(self._render_dict(body))

    def _render_dict(self, a_dict):
        rendered = {}
        for key, value in a_dict.items():
            if type(value) == dict:
                rendered[key] = self._render_dict(value)
            else:
                rendered[key] = self._render_with_template(value).strip()
        return rendered
