from __future__ import print_function

from actions import action, Action
from server import ConfigurationException
from unittest_helper import ActionTestBase


class ActionTest(ActionTestBase):
    def test_simple_log(self):
        actions = [{'log': {'message': 'Hello there!'}}]
        output = self._invoke(actions)

        self.assertEqual(output, 'Hello there!')

    def test_log_with_variable(self):
        actions = [{'log': {'message': 'HTTP {{ request.method }} {{ request.path }}'}}]

        output = self._invoke(actions)

        self.assertEqual(output, 'HTTP POST /testing')

    def test_custom_action(self):
        @action('for-test')
        class TestAction(Action):
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def _run(self):
                print(*('%s=%s' % (key, value) for key, value in self.kwargs.items()))

        actions = [{'for-test': {'string': 'Hello', 'number': 12, 'bool': True}}]

        output = self._invoke(actions)

        self.assertIn('string=Hello', output.split())
        self.assertIn('number=12', output.split())
        self.assertIn('bool=True', output.split())

    def test_invalid_action(self):
        actions = [{'invalid': {'Should': 'not work'}}]

        self.assertRaises(ConfigurationException, self._invoke, actions)

    def test_wrong_configuration(self):
        actions = [{'log': {'unknown_argument': 1}}]

        self.assertRaises(ConfigurationException, self._invoke, actions)
