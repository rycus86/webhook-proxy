from __future__ import print_function

from timeit import default_timer

from flask import request
from prometheus_client import Histogram, Summary, Gauge, Counter

from actions import action, Action
from util import ConfigurationException


@action('metrics')
class MetricsAction(Action):
    def __init__(self, output='Tracking metrics: {{ metric }}', **kwargs):
        from server import Server

        self._app = Server.app
        self._name = None

        if len(kwargs) != 1:
            raise ConfigurationException('The metrics action has to configure exactly one metric')

        for metric_type, configuration in kwargs.items():
            handler = getattr(self, metric_type)

            if not handler:
                raise ConfigurationException('Invalid metric type: %s' % metric_type)

            handler(**configuration)

        self._output_format = output

    def histogram(self, name, help=None, labels=None, **kwargs):
        self._register(
            Histogram,
            lambda m, t: m.observe(t),
            name, help or name,
            labels or dict(),
            **kwargs
        )

    def summary(self, name, help=None, labels=None, **kwargs):
        self._register(
            Summary,
            lambda m, t: m.observe(t),
            name, help or name,
            labels or dict(),
            **kwargs
        )

    def gauge(self, name, help=None, labels=None, **kwargs):
        self._register(
            Gauge,
            [lambda m: m.inc(), lambda m, _: m.dec()],
            name, help or name,
            labels or dict(),
            **kwargs
        )

    def counter(self, name, help=None, labels=None, **kwargs):
        self._register(
            Counter,
            lambda m, _: m.inc(),
            name, help or name,
            labels or dict(),
            **kwargs
        )

    def _register(self, metric_type, metric_calls, name, help, labels, **kwargs):
        label_names = tuple(labels.keys())

        metric = metric_type(name, help, labelnames=label_names, **kwargs)

        try:
            before_request_call, after_request_call = metric_calls
        except TypeError:
            before_request_call, after_request_call = None, metric_calls

        def target_metric(response):
            if label_names:
                return metric.labels(
                    *map(lambda key: self._render_with_template(
                        labels.get(key), response=response
                    ).strip(), label_names)
                )

            else:
                return metric

        def before_request():
            if request.path == '/metrics':
                return

            if before_request_call:
                before_request_call(target_metric(response=None))

            request.whp_start_time = default_timer()

        def after_request(response):
            if request.path == '/metrics':
                return response

            total_time = max(default_timer() - request.whp_start_time, 0)

            after_request_call(target_metric(response=response), total_time)

            return response

        self._app.before_request(before_request)
        self._app.after_request(after_request)

        self._name = name

    def _run(self):
        print(self._render_with_template(self._output_format, metric=self._name))
