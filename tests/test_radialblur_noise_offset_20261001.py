"""Signed SDK Angle -> native FLOAT32 noise phase -> public render regressions."""
import importlib
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/emulation'))
public = importlib.import_module('probe_radialblur_public_aligned_20261001')
latest = importlib.import_module('radialblur_current_public_20261001')
field = importlib.import_module('probe_radialblur_noise_offset_field_20261001')
cf = importlib.import_module('probe_radialblur_noise_offset_counterfactual_20261001')
SDK = ROOT/'tools/emulation/radialblur_noise_offset_sdk_harness_20261001.cpp'


def load(name):
    return json.loads((ROOT/'reports'/name).read_text())


class NoiseOffsetTests(unittest.TestCase):
    def test_sdk_phase_against_import_free_native_leaf(self):
        from aex_loader import AexLoader
        capture = load('radialblur_parameter_units_20261001.json')
        self.assertEqual(public.sha(public.initial.AEX.read_bytes()), capture['aex_sha256'])
        loader = AexLoader(str(public.initial.AEX), verbose=False, fast=False)
        # The getter's AD raw offset is grounded by the prior public/SDK traces.
        definition, output = loader.bump_alloc(0x100), loader.bump_alloc(16)
        rng = random.Random(20261001)
        values = sorted(set([r['raw_fixed'] for r in capture['leaf_rows']] + field.PHASE_RAW +
                            [rng.randint(-2147483648, 2147483647) for _ in range(128)]))
        expected = {}
        for raw in values:
            loader.write_bytes(definition, bytes(0x100))
            loader.write_bytes(definition+0x38, struct.pack('<i', raw))
            loader.write_bytes(output, bytes([0xa5])*16)
            loader.call_function(0x18001a2b0, int_args=[definition, output], max_instructions=32)
            self.assertFalse(loader.import_log)
            self.assertEqual(loader.read_bytes(output+4, 12), bytes([0xa5])*12)
            expected[raw] = loader.read_bytes(output, 4)
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        original = public.initial.HARNESS
        count = 0
        try:
            public.initial.HARNESS = SDK
            with tempfile.TemporaryDirectory(prefix='radial_offset_sdk_') as directory:
                for sanitize in (False, True):
                    binary = public.build(Path(directory)/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize)
                    for raw in values:
                        run = subprocess.run([str(binary), str(raw)], capture_output=True, text=True, check=True, env=env)
                        self.assertEqual(run.stderr, '')
                        decimal, bits = run.stdout.split()
                        self.assertEqual(struct.pack('<I', int(bits, 16)), expected[raw])
                        self.assertEqual(float(decimal), struct.unpack('<f', expected[raw])[0])
                        count += 1
        finally:
            public.initial.HARNESS = original
        self.assertEqual(count, 2*len(values))
        print('OFFSET_SDK_NATIVE_LEAF', len(values), 'raw inputs', count, 'SDK replays', flush=True)

    def test_initialized_native_grid_and_production_bindings(self):
        native = load('radialblur_noise_offset_field_20261001.json')
        counterfactual = load('radialblur_noise_offset_counterfactual_20261001.json')
        self.assertEqual(native['case_count'], 96)
        self.assertEqual(native['summary'], {'plane_raw_exact': 96, 'typed_resident_matches_trace': 96})
        self.assertEqual(json.loads((ROOT/'reports/radialblur_pf8_writer_public_20261001.json').read_text())['source_before_sha256'], counterfactual['candidate_source_sha256'])
        self.assertEqual(public.sha(cf.HEADER.read_bytes()), counterfactual['candidate_header_sha256'])
        for capture in (native, counterfactual):
            for path, expected in capture['dependencies_sha256'].items():
                if path == 'mac/OLMRadialBlur/OLMRadialBlur.cpp':
                    self.assertEqual(expected, json.loads((ROOT/'reports/radialblur_pf8_writer_public_20261001.json').read_text())['source_before_sha256'])
                elif path == 'core/dblur_noise.h':
                    # Preserve the archived capture's core epoch; the actual core
                    # below must still reproduce all 96 initialized native grids.
                    archived = subprocess.check_output(['git', 'show',
                        'a79c54d2df1e14e5fea585eb6fc77dad421bca42:'+path], cwd=ROOT)
                    self.assertEqual(public.sha(archived), expected, path)
                else:
                    self.assertEqual(public.sha((ROOT/path).read_bytes()), expected, path)
        with tempfile.TemporaryDirectory(prefix='radial_offset_grid_test_') as directory:
            binary = Path(directory)/'grid'
            subprocess.run(['clang++', '-std=c++17', '-O2', '-fno-fast-math', '-ffp-contract=off',
                            str(field.HARNESS), '-o', str(binary)], check=True)
            for row in native['rows']:
                self.assertTrue(row['core_plane_raw_exact'])
                self.assertTrue(row['native_plane_unchanged_by_sampler'])
                self.assertEqual(row['native_plane_sha256'], row['core_plane_sha256'])
                thickness = next(p['value'] for p in row['parameters'] if p['slot'] == 29)
                thickness_bits = struct.unpack('<I', struct.pack('<f', thickness))[0]
                phase_bits = struct.unpack('<I', bytes.fromhex(row['phase_f32_le_hex']))[0]
                seed = next(p['value'] for p in row['parameters'] if p['slot'] == 27)
                run = subprocess.run([str(binary), *map(str, row['geometry']), f'{thickness_bits:08x}',
                                      f'{phase_bits:08x}', str(seed)], capture_output=True, check=True)
                self.assertEqual(public.sha(run.stdout), row['native_plane_sha256'])
                self.assertEqual(list(map(int, run.stderr.split())), row['plane_dimensions'])
                self.assertEqual(public.sha(public.fixture(row)), row['input_sha256'])
        for group, expected in [('retained', (99, 127, 84)), ('independent', (129, 255, 0))]:
            summary = counterfactual['group_summaries'][group]['getter_and_profiles']
            self.assertEqual((summary['both_commands_exact'], summary['different'], summary['mac_rejected']), expected)
        # Check the full correction rather than accepting a getter-only patch.
        self.assertEqual(counterfactual['group_summaries']['independent']['getter_only']['mac_rejected'], 288)
        for row in counterfactual['rows']:
            before, after = row['results']['before'], row['results']['getter_and_profiles']
            for command in ('classic', 'smart'):
                if before[command]['raw_exact']:
                    self.assertTrue(after[command]['raw_exact'])
                offset = next(p['value'] for p in row['parameters'] if p['slot'] == 28)
                if offset == 0:
                    self.assertEqual(before[command]['raw_sha256'], after[command]['raw_sha256'])
                    self.assertEqual(before[command]['error'], after[command]['error'])

    def test_current_public_paths_o2_strict_sanitizers(self):
        capture = latest.capture()
        self.assertEqual(len(capture['rows']), 694)
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        count = 0
        with tempfile.TemporaryDirectory(prefix='radial_offset_public_test_') as directory:
            temp = Path(directory)
            for sanitize in (False, True):
                binary = public.build(temp/('san' if sanitize else 'o2'), public.SOURCE.read_text(), sanitize)
                for row in capture['rows']:
                    self.assertEqual(public.sha(public.fixture(row)), row['input_sha256'])
                    for command in ('classic', 'smart'):
                        error, raw, metadata = public.mac_render(binary, temp, row, command, env)
                        expected = row['results'][command]
                        self.assertEqual(error, expected['error'])
                        self.assertEqual(public.sha(raw) if not error else None, expected['raw_sha256'])
                        self.assertEqual(metadata, expected['metadata'])
                        self.assertEqual(not error and public.sha(raw) == row['reference_raw_sha256'], expected['raw_exact'])
                        count += 1
                print('OFFSET_PUBLIC', 'san' if sanitize else 'o2', count, flush=True)
        self.assertEqual(count, 2776)


if __name__ == '__main__':
    unittest.main()
