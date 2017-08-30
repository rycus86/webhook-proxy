from flask import Flask, request
from validator import Validator


class Server(object):

    def __init__(self, host='127.0.0.1', port=5000, validators=None):
        self.host = host
        self.port = port

        if validators:
            self.validators = {route: Validator(validator) for config in validators for route, validator in config.items()}

        else:
            self.validators = {'/': Validator()}

    def run(self):
        app = Flask(__name__)
        
        def _make_response(status, message):
            return message, status, {'Content-Type': 'text/plain'}

        for route, validator in self.validators.items():
            @app.route(route, endpoint=route[1:], methods=[validator.method])
            def receive(**kwargs):
                validator = self.validators.get(request.path)

                if not validator:
                    return _make_response(404, 'Not found')  # should not happen
                
                if not request.json:
                    return _make_response(400, 'No payload')

                if not validator.accept(request):
                    return _make_response(409, 'Invalid payload')
            
                # TODO run actions

                return _make_response(200, 'OK\n')

        app.run(host=self.host, port=self.port)

