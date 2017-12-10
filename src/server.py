import os

from flask import Flask
from prometheus_client import Summary
from prometheus_flask_exporter import PrometheusMetrics

from endpoints import Endpoint
from util import ConfigurationException, import_action_module


class Server(object):
    app = None

    def __init__(self, endpoint_configurations, host='127.0.0.1', port=5000, imports=None):
        self.host = host
        self.port = int(port)

        if not endpoint_configurations:
            raise ConfigurationException('No endpoints defined')

        if imports:
            for path in imports:
                import_action_module(path)

        Server.app = Flask(__name__)

        action_metrics = self._setup_metrics()

        endpoints = [Endpoint(route, settings, action_metrics)
                     for config in endpoint_configurations
                     for route, settings in config.items()]

        for endpoint in endpoints:
            endpoint.setup(self.app)

    def _setup_metrics(self):
        metrics = PrometheusMetrics(self.app)

        metrics.info('flask_app_info', 'Application info',
                     version=os.environ.get('GIT_COMMIT') or 'unknown')

        metrics.info(
            'flask_app_built_at', 'Application build timestamp'
        ).set(
            float(os.environ.get('BUILD_TIMESTAMP') or '0')
        )

        action_summary = Summary(
            'webhook_proxy_actions',
            'Action invocation metrics',
            labelnames=('http_route', 'http_method', 'action_type', 'action_index')
        )

        return action_summary

    def run(self):
        self.app.run(host=self.host, port=self.port, threaded=True)
