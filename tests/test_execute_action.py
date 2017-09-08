from unittest_helper import ActionTestBase


class ExecuteActionTest(ActionTestBase):
    def test_echo(self):
        output = self._invoke({'execute': {'command': 'echo "Hello there!"'}})

        self.assertEqual(output, 'Hello there!')

    def test_format_output(self):
        output = self._invoke({'execute': {'command': 'echo "one"; echo "two"',
                                           'output': '{% for line in result.splitlines() %}'
                                                     'line={{ line }}'
                                                     '{% endfor %}'}})

        self.assertIn('line=one', output)
        self.assertIn('line=two', output)

    def test_alternative_shell(self):
        output = self._invoke({'execute': {'command': 'echo "Hello from Bash"',
                                           'shell': 'bash'}})

        self.assertEqual(output, 'Hello from Bash')

    def test_no_shell(self):
        output = self._invoke({'execute': {'command': ['ls', '-l', '/'], 'shell': False}})

        self.assertIn(' bin', output)
        self.assertIn(' usr', output)
        self.assertIn(' var', output)

    def test_custom_shell_command(self):
        output = self._invoke({'execute': {'command': ['ls', '-l', '/'], 'shell': ['bash', '-c']}})

        self.assertIn(' bin', output)
        self.assertIn(' usr', output)
        self.assertIn(' var', output)
