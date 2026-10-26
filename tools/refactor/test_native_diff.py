"""Comparator regressions independent of production kernel behaviour."""
import tempfile
import unittest
from pathlib import Path
from native_diff import ROOT, classify, first_difference


class ComparatorTests(unittest.TestCase):
    def test_refusal_identity(self):
        a = dict(status='refusal', error=17, tags=['guard:unsupported'])
        self.assertEqual(classify(a, dict(a), None), (True, False, 'refusal'))
        self.assertEqual(classify(a, dict(a, tags=['guard:other']), None),
                         (True, True, 'difference'))
        self.assertEqual(classify(a, dict(a, error=18), None),
                         (True, True, 'difference'))

    def test_identical_timeouts_are_not_success(self):
        self.assertEqual(classify({'status':'timeout'}, {'status':'timeout'}, None),
                         (False, False, 'execution_error'))

    def test_streaming_boundary_and_length(self):
        scratch = ROOT/'orchestra/state/Q00-refactor-native-diff-tool'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as td:
            a, b = Path(td)/'a', Path(td)/'b'
            a.write_bytes(b'\0'*(1048576+4))
            b.write_bytes(a.read_bytes())
            self.assertIsNone(first_difference(a, b))
            with b.open('r+b') as stream:
                stream.seek(1048576); stream.write(b'\1')
            self.assertEqual(first_difference(a, b), 1048576)
            b.write_bytes(b'\0'*1048576)
            self.assertEqual(first_difference(a, b), 1048576)
            a.write_bytes(b''); b.write_bytes(b'')
            self.assertIsNone(first_difference(a, b))


if __name__ == '__main__':
    unittest.main()
