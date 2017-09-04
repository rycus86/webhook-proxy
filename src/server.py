from flask import Flask

from endpoints import Endpoint
from util import ConfigurationException


class Server(object):
    def __init__(self, endpoint_configurations, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port

        if not endpoint_configurations:
            raise ConfigurationException('No endpoints defined')

        endpoints = [Endpoint(route, settings)
                     for config in endpoint_configurations
                     for route, settings in config.items()]

        self.app = Flask(__name__)

        for endpoint in endpoints:
            endpoint.setup(self.app)

    def run(self):
        self.app.run(host=self.host, port=self.port, threaded=True)
