import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('context', Path(__file__).resolve().parents[1] / 'transcript-maker/scripts/build_context.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ContextTests(unittest.TestCase):
    def test_group_selection_and_deduplication(self):
        self.assertEqual(m.build_context({'a': ['Claude', 'GitHub'], 'b': ['github', '雅思']}, ['a', 'b']), 'Claude GitHub 雅思')

    def test_rejects_bad_groups_and_excess_terms(self):
        for groups, selected, limit in [({'a': ['x']}, ['missing'], 30), ({'a': ['x\ny']}, ['a'], 30), ({'a': ['x', 'y']}, ['a'], 1)]:
            with self.assertRaises(ValueError):
                m.build_context(groups, selected, limit)


if __name__ == '__main__':
    unittest.main()
