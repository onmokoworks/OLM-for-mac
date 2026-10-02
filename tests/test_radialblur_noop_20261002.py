"""Actual public no-op restoration, original copy witnesses and world contracts."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/emulation'))
probe = importlib.import_module('probe_radialblur_noop_20261002')
current = importlib.import_module('radialblur_current_public_20261001')
public = probe.public
WORLD_HARNESS = ROOT/'tools/emulation/radialblur_noop_world_contract_harness_20261002.cpp'
COPY_WORKER_DEFAULT = Path('/tmp/radial_noop_bound_reference_20261002/target/release/aex-guest-worker')


class NoOpTests(unittest.TestCase):
    def report(self):
        report = current.capture()
        self.assertEqual(current.PATH.name, 'radialblur_noop_public_20261002.json')
        self.assertEqual(public.SOURCE.read_text(), probe.candidate_source(probe.before_source()))
        return report

    def test_actual_public_noop_and_retained_cases(self):
        report = self.report()
        self.assertFalse(report['pilot'])
        generated = probe.independent_cases()
        self.assertEqual(len(generated), 82)
        self.assertEqual(generated, [{k: row[k] for k in generated[0]} for row in report['independent_rows']])
        for rel, expected in report['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/rel).read_bytes()), expected, rel)
        worker = Path(os.environ.get('RADIAL_NOOP_WORKER', str(COPY_WORKER_DEFAULT)))
        self.assertEqual(public.sha(worker.read_bytes()), report['copy_worker_sha256'])
        self.assertEqual(public.sha(public.initial.AEX.read_bytes()), report['aex_sha256'])
        retained = probe.retained_cases(); self.assertEqual(len(retained), 9563)
        native_count = replays = 0
        with tempfile.TemporaryDirectory(prefix='radial_noop_production_') as name:
            directory = Path(name)
            for row in report['independent_rows']:
                with probe.fixture_scope(row) as data:
                    raw, frame, _, close, _ = public.native_render(worker, directory, row)
                    self.assertEqual(raw, data)
                    self.assertEqual(public.sha(raw), row['reference_raw_sha256'])
                    self.assertTrue(frame['output']['guards_intact'])
                    self.assertTrue(close['session_clean'])
                    self.assertFalse(close['unsupported_suite_calls'])
                    native_count += 1
            for mode in ['o2', 'san', 'default']:
                binary = probe.build(directory/mode, public.SOURCE.read_text(), mode)
                for row in retained:
                    for route in ['classic', 'smart']:
                        error, raw, metadata = public.mac_render(binary, directory, row, route, probe.ENV)
                        expected = row['results'][route]
                        self.assertEqual(error, expected['error'], row)
                        self.assertEqual(public.sha(raw), expected['raw_sha256'], row)
                        self.assertEqual(metadata, expected['metadata'], row)
                        replays += 1
                    if replays%1000 == 0: print('NOOP_PRODUCTION_PROGRESS', mode, replays, flush=True)
                for row in report['independent_rows']:
                    with probe.fixture_scope(row):
                        for route in ['classic', 'smart']:
                            error, raw, metadata = public.mac_render(binary, directory, row, route, probe.ENV)
                            expected = row['results'][route]
                            self.assertFalse(error, row)
                            self.assertEqual(public.sha(raw), expected['raw_sha256'], row)
                            self.assertEqual(metadata, expected['metadata'], row)
                            replays += 1
        self.assertEqual(native_count, 82); self.assertEqual(replays, 57870)
        print('NOOP_PRODUCTION 57870 NATIVE 82', flush=True)

    def test_byte_misaligned_rows_and_atomic_world_rejections(self):
        self.report()
        results = {}
        with tempfile.TemporaryDirectory(prefix='radial_noop_world_actual_') as name:
            directory = Path(name)
            with probe.harness_scope(WORLD_HARNESS):
                for mode, sanitize in [('o2', False), ('san', True)]:
                    binary = public.build(directory/mode, public.SOURCE.read_text(), sanitize)
                    run = subprocess.run([str(binary)], capture_output=True, text=True, env=probe.ENV)
                    self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
                    self.assertFalse(run.stderr)
                    self.assertEqual(run.stdout.strip(), 'NOOP_WORLD_CONTRACT 84 BYTE_COPY_AND_ATOMIC_REJECTIONS')
                    results[mode] = run.stdout.strip()
        self.assertEqual(results['o2'], results['san'])
        print('NOOP_WORLD_CONTRACT 84 BOTH_BUILDS', flush=True)

    def test_public_odd_byte_rowbytes_preserve_original_copy(self):
        report = self.report(); replays = 0
        with tempfile.TemporaryDirectory(prefix='radial_noop_oddrows_actual_') as name:
            directory = Path(name)
            for mode in ['o2', 'san', 'default']:
                binary = probe.build(directory/mode, public.SOURCE.read_text(), mode, odd_rowbytes=True)
                for row in report['independent_rows']:
                    with probe.fixture_scope(row):
                        for route in ['classic', 'smart']:
                            error, raw, _ = public.mac_render(binary, directory, row, route, probe.ENV)
                            self.assertFalse(error, row)
                            self.assertEqual(public.sha(raw), row['reference_raw_sha256'], row)
                            replays += 1
        self.assertEqual(replays, 492)
        print('NOOP_ODD_BYTE_ROWS 82 CASES 492 REPLAYS', flush=True)

    def test_original_zero_controls_and_bound_copy_reference(self):
        report = self.report()
        self.assertEqual(report['original_zero_copy_rule'], probe.strength.original_rule()['zero_control_copy_branch_code_sha256'])
        build = report['copy_reference_build']
        self.assertTrue(build['copy_and_math_callbacks_unchanged'])
        self.assertTrue(build['parent_source_and_worker_unchanged'])
        self.assertEqual(build['fixture_dimensions'], [8192, 4096])
        self.assertEqual(build['data_arena_bytes'], 288*1024*1024)
        self.assertTrue(build['data_mapping_ends_at_stub_base_without_overlap'])
        self.assertEqual(set(build['changed']), {'crates/aex-guest-worker/src/classic.rs', 'crates/aex-guest-worker/src/x64.rs'})
        parent = Path('/tmp/radial_windows_reference_v2_20261001')
        for rel, expected in build['source_files_sha256'].items():
            self.assertEqual(public.sha((parent/rel).read_bytes()), expected, rel)
        self.assertEqual(public.sha((parent/'target/release/aex-guest-worker').read_bytes()), build['parent_worker_sha256'])
        print('NOOP_ORIGINAL_TYPED_COPY_AND_BOUND_REFERENCE', flush=True)


if __name__ == '__main__': unittest.main()
