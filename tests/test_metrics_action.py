from unittest_helper import ActionTestBase, unregister_metrics

from server import Server
from util import ConfigurationException


class MetricsActionTest(ActionTestBase):
    def test_histogram(self):
        output = self._invoke({'metrics': {'histogram': dict(
            name='test_histogram', help='Test Histogram'
        )}})

        self.assertEqual(output, 'Tracking metrics: test_histogram')
        self.assertIn('test_histogram_count 1.0', self.metrics())
        self.assertIn('test_histogram_sum 0.', self.metrics())
        self.assertIn('test_histogram_bucket{le=', self.metrics())

        unregister_metrics()

        output = self._invoke({'metrics': {'histogram': dict(
            name='test_histogram_with_labels', help='Test Histogram',
            labels={'path': '{{ request.path }}'}
        )}})

        self.assertEqual(output, 'Tracking metrics: test_histogram_with_labels')
        self.assertIn('test_histogram_with_labels_count{path="/testing"} 1.0', self.metrics())
        self.assertIn('test_histogram_with_labels_sum{path="/testing"} 0.', self.metrics())
        self.assertIn('test_histogram_with_labels_bucket{le=', self.metrics())

    def test_summary(self):
        output = self._invoke({'metrics': {'summary': dict(
            name='test_summary', help='Test Summary'
        )}})

        self.assertEqual(output, 'Tracking metrics: test_summary')
        self.assertIn('test_summary_count 1.0', self.metrics())
        self.assertIn('test_summary_sum 0.', self.metrics())

        unregister_metrics()

        output = self._invoke({'metrics': {'summary': dict(
            name='test_summary_with_labels', help='Test Summary',
            labels={'path': '{{ request.path }}'}
        )}})

        self.assertEqual(output, 'Tracking metrics: test_summary_with_labels')
        self.assertIn('test_summary_with_labels_count{path="/testing"} 1.0', self.metrics())
        self.assertIn('test_summary_with_labels_sum{path="/testing"} 0.', self.metrics())

    def test_gauge(self):
        output = self._invoke({'metrics': {'gauge': dict(
            name='test_gauge', help='Test Gauge'
        )}})

        self.assertEqual(output, 'Tracking metrics: test_gauge')
        self.assertIn('test_gauge 0.0', self.metrics())

        unregister_metrics()

        output = self._invoke({'metrics': {'gauge': dict(
            name='test_gauge_with_labels', help='Test Gauge',
            labels={'target': '{{ request.json.target }}'}
        )}}, body=dict(target='sample'))

        self.assertEqual(output, 'Tracking metrics: test_gauge_with_labels')
        self.assertIn('test_gauge_with_labels{target="sample"} 0.0', self.metrics())

    def test_counter(self):
        output = self._invoke({'metrics': {'counter': dict(
            name='test_counter', help='Test Counter'
        )}})

        self.assertEqual(output, 'Tracking metrics: test_counter')
        self.assertIn('test_counter_total 1.0', self.metrics())

        unregister_metrics()

        output = self._invoke({'metrics': {'counter': dict(
            name='test_counter_with_labels', help='Test Counter',
            labels={'code': '{{ response.status_code }}'}
        )}})

        self.assertEqual(output, 'Tracking metrics: test_counter_with_labels')
        self.assertIn('test_counter_with_labels_total{code="200"} 1.0', self.metrics())

    def test_multiple_endpoints(self):
        unregister_metrics()

        server = Server([
            {
                '/one': {
                    'actions': [{
                        'metrics': {
                            'counter': {'name': 'metric_one'}
                        }
                    }]
                },
                '/two': {
                    'actions': [
                        {
                            'metrics': {
                                'counter': {'name': 'metric_two'}
                            }
                        },
                        {
                            'metrics': {
                                'counter': {'name': 'metric_xyz'}
                            }
                        }]
                }
            }
        ])

        server.app.testing = True
        client = server.app.test_client()

        self._server = server

        client.post('/one', headers={'Content-Type': 'application/json'},
                    data='{"test":"1"}', content_type='application/json')

        self.assertIn('metric_one_total 1.0', self.metrics())
        self.assertIn('metric_two_total 0.0', self.metrics())
        self.assertIn('metric_xyz_total 0.0', self.metrics())

        client.post('/one', headers={'Content-Type': 'application/json'},
                    data='{"test":"2"}', content_type='application/json')

        self.assertIn('metric_one_total 2.0', self.metrics())
        self.assertIn('metric_two_total 0.0', self.metrics())
        self.assertIn('metric_xyz_total 0.0', self.metrics())

        client.post('/two', headers={'Content-Type': 'application/json'},
                    data='{"test":"3"}', content_type='application/json')

        self.assertIn('metric_one_total 2.0', self.metrics())
        self.assertIn('metric_two_total 1.0', self.metrics())
        self.assertIn('metric_xyz_total 1.0', self.metrics())

    def test_invalid_metric(self):
        self.assertRaises(ConfigurationException, self._invoke, {'metrics': {'unknown': {}}})

    def metrics(self):
        client = self._server.app.test_client()

        response = client.get('/metrics')

        self.assertEqual(response.status_code, 200)

        return str(response.data)
