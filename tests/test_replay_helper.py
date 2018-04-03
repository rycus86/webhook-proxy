import unittest
import actions.replay_helper as helper


class ReplayHelperTest(unittest.TestCase):
    def test_with_read_only_db(self):
        with helper.read_only_db(':memory:') as db:
            result = db.execute('SELECT 1').fetchone()
            self.assertEqual(1, result[0])

    def test_with_read_write_db(self):
        with helper.read_write_db(':memory:') as db:
            result = db.execute('SELECT 1').fetchone()
            self.assertEqual(1, result[0])

