"""Restore the AEX vector fade path while exposing the unresolved scalar tail."""
import importlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/emulation'))
probe = importlib.import_module('probe_radialblur_rotation_fade_20261001')
public = probe.public
current = importlib.import_module('radialblur_current_public_20261001')


class RotationFadeTests(unittest.TestCase):
    def test_live_matrix_preserves_previous_exact_and_reacquires_new_exact(self):
        saved = current.capture(); before = json.loads(probe.BEFORE.read_text())
        self.assertEqual(public.SOURCE.read_text(), probe.candidate_source(probe.before_source()))
        self.assertEqual(saved['summary'], probe.writer.summarize(saved['rows']))
        self.assertEqual(saved['summary'], {'case_count': 694, 'both_commands_exact': 565, 'different': 45,
                                            'mac_rejected': 84, 'became_exact': 6, 'lost_exact': 0, 'raw_changed': 6})
        for path, expected in saved['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/path).read_bytes()), expected, path)
        worker = Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()), saved['controlled_worker_sha256'])
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        with tempfile.TemporaryDirectory(prefix='radial_fade_production_') as directory:
            temp = Path(directory); native_count = live_count = 0
            for row, old in zip(saved['rows'], before['rows']):
                for key in ['parameters', 'group', 'matrix', 'row_index', 'family', 'depth', 'geometry', 'pattern',
                            'state', 'input_sha256', 'reference_raw_sha256']:
                    self.assertEqual(row[key], old[key])
                self.assertEqual(public.sha(public.fixture(row)), row['input_sha256'])
                for command in ['classic', 'smart']:
                    if old['results'][command]['raw_exact']:
                        self.assertEqual(row['results'][command]['raw_sha256'], old['results'][command]['raw_sha256'])
                if row['results']['classic']['raw_exact'] and not old['results']['classic']['raw_exact']:
                    raw, frame, _, close, _ = public.native_render(worker, temp, row)
                    self.assertEqual(public.sha(raw), row['reference_raw_sha256'])
                    self.assertEqual(frame['render_error'], 0); self.assertTrue(frame['output']['guards_intact'])
                    self.assertTrue(close['session_clean']); self.assertFalse(close['unsupported_suite_calls']); native_count += 1
            for sanitize in [False, True]:
                binary = public.build(temp/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize)
                for case in saved['rows']:
                    for command in ['classic', 'smart']:
                        error, raw, metadata = public.mac_render(binary, temp, case, command, env)
                        expected = case['results'][command]
                        self.assertEqual(error, expected['error'])
                        self.assertEqual(public.sha(raw) if not error else None, expected['raw_sha256'])
                        self.assertEqual(metadata, expected['metadata']); live_count += 1
                for row in saved['fade_tables']:
                    for command in ['classic', 'smart']:
                        error, raw, metadata = public.mac_render(binary, temp, row['case'], command, env)
                        expected = row['public_results'][command]
                        self.assertEqual(error, expected['error']); self.assertEqual(public.sha(raw), expected['raw_sha256'])
                        self.assertEqual(metadata, expected['metadata']); live_count += 1
                print('FADE_PRODUCTION_PUBLIC', live_count, flush=True)
            self.assertEqual(native_count, 6); self.assertEqual(live_count, 2776+396)
        print('FADE_NEW_EXACT_NATIVE', native_count, flush=True)

    def test_natural_planes_and_all_legal_table_lengths(self):
        saved = current.capture(); before = json.loads(probe.BEFORE.read_text())
        worker = Path(os.environ['RADIAL_WINDOWS_WORKER']); parent = Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()), saved['window_worker_sha256'])
        self.assertEqual(public.sha(parent.read_bytes()), saved['controlled_worker_sha256'])
        self.assertEqual(saved['table_summary']['length_count'], 99)
        self.assertEqual(saved['table_summary']['vector_words'], 4800)
        self.assertEqual(saved['table_summary']['scalar_words'], 150)
        self.assertEqual(saved['table_summary']['vector_different_words'], 0)
        self.assertEqual(saved['table_summary']['scalar_different_words'], 3)
        self.assertEqual([(r['length'], r['scalar_comparison']['different_words']) for r in saved['fade_tables']
                          if r['scalar_comparison']['different_words']], [(10, 1), (19, 1), (51, 1)])
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        with tempfile.TemporaryDirectory(prefix='radial_fade_natural_') as directory:
            temp = Path(directory)
            observed = probe.natural(worker, temp, before, probe.before_source(), public.SOURCE.read_text())
            for result, expected in zip(observed, saved['natural_witnesses']):
                for key in ['mac_dimensions', 'field_comparisons', 'mac_raw_sha256', 'candidate_raw_exact']:
                    self.assertEqual(result[key], expected[key])
            harness = public.initial.HARNESS
            try:
                public.initial.HARNESS = ROOT/'tools/emulation/radialblur_rotation_fade_sdk_harness_20261001.cpp'
                payload = ''.join(f'{length}\n' for length in range(1, 100)); expected = []
                for row in saved['fade_tables']:
                    data, math_record = probe.model(row['length'])
                    self.assertEqual(math_record, row['math'])
                    expected.append(''.join(f'{n:08x}' for n in struct.unpack('<%dI'%row['length'], data)))
                for sanitize in [False, True]:
                    binary = public.build(temp/('helper_san' if sanitize else 'helper_o2'), public.SOURCE.read_text(), sanitize)
                    run = subprocess.run([str(binary)], input=payload, text=True, capture_output=True, check=True, env=env)
                    self.assertEqual(run.stderr, ''); self.assertEqual(run.stdout.splitlines(), expected)
            finally:
                public.initial.HARNESS = harness
            for row in saved['fade_tables']:
                directory = temp/f"table_{row['length']}"; directory.mkdir()
                raw, frame, _, close, _ = public.native_render(parent, directory, row['case'])
                self.assertEqual(public.sha(raw), row['case']['reference_raw_sha256'])
                self.assertFalse(frame['render_error']); self.assertTrue(frame['output']['guards_intact'])
                self.assertTrue(close['session_clean']); self.assertFalse(close['unsupported_suite_calls'])
                native, _ = probe.table_trace(worker, directory, row['case'], row['length'])
                model, _ = probe.model(row['length']); end = (row['length'] & ~3)*4
                self.assertEqual(probe.fields.compare_words(native[:end], model[:end]), row['vector_comparison'])
                self.assertEqual(probe.fields.compare_words(native[end:], model[end:]), row['scalar_comparison'])
        print('FADE_TABLE_NATIVE_LENGTHS', 99, 'SDK', 198, 'VECTOR_WORDS', 4800, 'OPEN_SCALAR_WORDS', 3, flush=True)


if __name__ == '__main__':
    unittest.main()
