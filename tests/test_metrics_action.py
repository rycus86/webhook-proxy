from unittest_helper import ActionTestBase

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
        self.assertIn('test_counter 1.0', self.metrics())

        output = self._invoke({'metrics': {'counter': dict(
            name='test_counter_with_labels', help='Test Counter',
            labels={'path': '{{ request.path }}'}
        )}})

        self.assertEqual(output, 'Tracking metrics: test_counter_with_labels')
        self.assertIn('test_counter_with_labels{path="/testing"} 1.0', self.metrics())

    def test_invalid_metric(self):
        self.assertRaises(ConfigurationException, self._invoke, {'metrics': {'unknown': {}}})

    def metrics(self):
        client = self._server.app.test_client()

        response = client.get('/metrics')

        self.assertEqual(response.status_code, 200)

        return str(response.data)
