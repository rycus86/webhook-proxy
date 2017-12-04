from unittest_helper import ActionTestBase


class MetricsActionTest(ActionTestBase):
    def test_metrics(self):
        output = self._invoke({'metrics': {'counter': {'name': 'test'}}})

        self.fail('Not implemented yet')

