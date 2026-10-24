#!/usr/bin/env python3
"""Offline checks; these do not establish any AE pixel result."""
import unittest
from unittest.mock import patch
import numpy as np
import run_ae_smoke as runner


class PipelineTests(unittest.TestCase):
    def test_main_executable_check_excludes_helpers_and_includes_versions(self):
        listing = ('1 /Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects\n'
                   '2 /Applications/Adobe After Effects 2025/Adobe After Effects 2025.app/Contents/MacOS/After Effects\n'
                   '3 /Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/crashpad_handler\n')
        with patch.object(runner, 'capture', return_value=listing) as call:
            self.assertEqual(runner.running(), ['1', '2'])
            self.assertEqual(call.call_args.args[0], ['ps', '-axo', 'pid=,comm='])

    def test_ae16_file_encoding_inverse_for_every_sdr_value(self):
        source = np.arange(32769, dtype=np.uint64)
        encoded = source * 65535 // 32768
        decoded = (encoded * 32768 + 32767) // 65535
        self.assertTrue(np.array_equal(source, decoded))

    def test_only_2026_full_path_is_used(self):
        self.assertEqual(str(runner.APP), '/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app')


if __name__ == '__main__':
    unittest.main()
