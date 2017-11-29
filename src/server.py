from flask import Flask
from prometheus_client import CollectorRegistry
from prometheus_client import Summary
from prometheus_flask_exporter import PrometheusMetrics

from endpoints import Endpoint
from util import ConfigurationException


class Server(object):
    def __init__(self, endpoint_configurations, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port

        if not endpoint_configurations:
            raise ConfigurationException('No endpoints defined')

        self.app = Flask(__name__)
        
        self._setup_metrics()

        endpoints = [Endpoint(self.app, route, settings)
                     for config in endpoint_configurations
                     for route, settings in config.items()]

        for endpoint in endpoints:
            endpoint.setup(self.app)

    def _setup_metrics(self):
        PrometheusMetrics(self.app)

        action_summary = Summary(
            'webhook_proxy_actions',
            'Action invocation metrics',
            labelnames=('http_route', 'http_method', 'action_type', 'action_index')
        )

        setattr(self.app, 'action_metrics', action_summary)

    def run(self):
        self.app.run(host=self.host, port=self.port, threaded=True)
