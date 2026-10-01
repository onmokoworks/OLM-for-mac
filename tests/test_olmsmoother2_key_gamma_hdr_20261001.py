"""Public AEX key/gamma/HDR and isolated signed-64-bit PF16 conversion witnesses."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/emulation'))
replay = importlib.import_module('replay_olmsmoother2_key_gamma_hdr_20261001')
pack = importlib.import_module('probe_olmsmoother2_pf16_pack_20261001')


class KeyGammaHdrTests(unittest.TestCase):
    def test_public_current_source(self):
        result = replay.replay(replay.probe.SOURCE.read_text())
        self.assertEqual(result['case_count'], 1692)
        self.assertEqual(result['render_count'], 3384)
        self.assertEqual(result['summary']['raw_exact_count'], 3384)

    def test_pf16_pack_current_source(self):
        path = ROOT / 'reports/olmsmoother2_pf16_pack_production_20261001.json'
        capture = json.loads(path.read_text())
        self.assertEqual(capture['aex_sha256'], pack.campaign.retained.native_identity.AEX_SHA256)
        self.assertEqual(capture['case_count'], 569)
        self.assertEqual(capture['mxcsr_initial'], 0x1f80)
        self.assertTrue(capture['native_hashes_preserved'])
        for dependency, expected in capture['dependencies_sha256'].items():
            self.assertEqual(pack.campaign.sha((ROOT / dependency).read_bytes()), expected, dependency)
        cases = list(pack.specifications())
        for case, actual in zip(cases, capture['cases']):
            self.assertEqual(case['argb_input_bits'], actual['argb_input_bits'])
            self.assertTrue(actual['raw_exact'])
        with tempfile.TemporaryDirectory(prefix='sm2_pack_regression_') as directory:
            for sanitize in (False, True):
                binary = pack.compile_pack(Path(directory) / ('san' if sanitize else 'o2'),
                                           pack.campaign.SOURCE.read_text(), sanitize)
                values = pack.mac_pack(binary, cases, dict(os.environ,
                                       ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1'))
                for raw, actual in zip(values, capture['cases']):
                    self.assertEqual(pack.campaign.sha(raw), actual['native_raw_sha256'])
                print('SM2_PACK_CURRENT_REPLAY', 'san' if sanitize else 'o2', len(values), flush=True)


if __name__ == '__main__':
    unittest.main()
