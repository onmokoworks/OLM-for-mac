"""Current-source replay of naturally generated missing dispatch-index witnesses."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / 'tools/emulation/probe_olmsmoother2_switch_reachability_20261001.py'
REPORT = ROOT / 'reports/olmsmoother2_switch_reachability_20261001.json'
spec = importlib.util.spec_from_file_location('sm2_reachability', PROBE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

def replay_retained_and_missing_indices_current_source():
    report = json.loads(REPORT.read_text())
    retained = json.loads(probe.RETAINED.read_text())
    missing = sorted(set(range(256)) - set(retained['distinct_switch_indices']))
    assert len(missing) == 65
    assert report['native_emulation'] is True
    assert report['missing_indices_before'] == report['target_indices'] == missing
    assert len(report['cases']) == 390
    assert report['probe_sha256'] == probe.sha(PROBE.read_bytes())
    assert report['harness_sha256'] == probe.sha(probe.HARNESS.read_bytes())
    assert report['retained_report_sha256'] == probe.sha(probe.RETAINED.read_bytes())
    # Keep the capture's original source binding. This test replays the
    # retained native oracle against the current source after the safe-access
    # fix; it must not relabel an old native capture as a new execution.
    assert report['production_source_sha256'] == 'b7420807a37ce318b6eedc6285af5735cb344020a84ed2ef869cbb5b448d5ae1'
    assert report['loader_sha256'] == probe.sha((ROOT/'tools/emulation/aex_loader.py').read_bytes())
    assert report['aex_sha256'] == '7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7'
    assert len(report['retained_replay']) == 114
    assert all(r['raw_exact'] and r['histogram_exact'] for r in report['retained_replay'])
    seen = set()
    with tempfile.TemporaryDirectory(prefix='sm2_reachability_replay_') as td:
        old = Path(td)/'old'
        probe.compile_harness(probe.REPLAY_HARNESS, old)
        replay = probe.replay(old, retained)
        assert all(r['raw_exact'] and r['histogram_exact'] for r in replay)
        # Every 4x3 witness also checks source immutability and padded rows.
        # Sanitizers exercise the cardinal/diagonal scans at these boundaries.
        binary = Path(td)/'sanitized'
        probe.compile_harness(probe.HARNESS, binary, sanitize=True)
        optimized = Path(td)/'optimized'
        probe.compile_harness(probe.HARNESS, optimized)
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
        for row in report['cases']:
            target,version,depth = row['target_index'],row['version'],row['depth']
            seen.add((target,version,depth))
            data = probe.typed_input(probe.fixture(target),depth)
            assert probe.sha(data) == row['input_sha256']
            assert row['target_reached'] and row['native_center_reached']
            assert row['native_center_index'] == target
            assert row['raw_exact'] and row['histogram_exact']
            assert set(row['executed_imports']) <= {
                '_vcomp_fork', '_vcomp_for_static_simple_init',
                '_vcomp_for_static_end', '_vcomp_for_dynamic_init',
                '_vcomp_for_dynamic_next',
            }
            for executable in (optimized,binary):
                raw,hist = probe.parse(subprocess.run([str(executable),'4','3',depth,str(version)],input=data,check=True,capture_output=True,env=env))
                assert probe.sha(raw) == row['native_raw_sha256'] == row['production_raw_sha256']
                assert hist == {int(k):v for k,v in row['native_histogram'].items()}
    assert seen == {(i,v,d) for i in missing for v in (1,2) for d in ('PF8','PF16','PF32')}

class SwitchReachabilityTests(unittest.TestCase):
    def test_retained_and_missing_indices_current_source(self):
        replay_retained_and_missing_indices_current_source()

if __name__ == '__main__': unittest.main()
