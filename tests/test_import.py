import os
import unittest

from util import ConfigurationException

from unittest_helper import ActionTestBase


class ImportTest(ActionTestBase):
    base_dir = os.path.join(os.path.dirname(__file__), 'imports')

    def test_import_external_action(self):
        actions_module_path = os.path.join(self.base_dir, 'actions_to_load.py')

        output = self._invoke([
            {
                'sample': {'x': 1}
            },
            {
                'json': {'bool': True, 'num': 2, 'str': 'abc'}
            }
        ], imports=[actions_module_path])

        self.assertIn('x=1', output)
        self.assertIn('"bool": true', output)
        self.assertIn('"num": 2', output)
        self.assertIn('"str": "abc"', output)

    def test_imports_with_same_filename(self):
        imports = [
            os.path.join(self.base_dir, 'test1/action.py'),
            os.path.join(self.base_dir, 'test2/action.py')
        ]

        output = self._invoke([
            {'test1': {'action': 'test-1'}},
            {'test2': {'action': 'test-2'}}
        ], imports=imports)

        self.assertIn('action=test-1', output)
        self.assertIn('action=test-2', output)

    def test_raises_configuration_exception_on_failure(self):
        self.assertRaises(ConfigurationException, self._invoke, list(), imports=['not-found'])
        self.assertRaises(ConfigurationException, self._invoke, list(),
                          imports=[os.path.join(self.base_dir, 'invalid.py')])

