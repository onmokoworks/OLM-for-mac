"""Reacquire original Gain witnesses and replay the actual public SDK source."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/emulation'))
probe = importlib.import_module('probe_radialblur_gain_20261002')
current = importlib.import_module('radialblur_current_public_20261001')
public = probe.public


class GainTests(unittest.TestCase):
    def test_actual_public_gain_and_retained_cases(self):
        report = current.capture()
        self.assertEqual(public.SOURCE.read_text(), probe.candidate_source(probe.before_source()))
        self.assertEqual(report['summary'], json.loads(probe.BEFORE.read_text())['summary'])
        generated = probe.independent_cases()
        self.assertEqual(generated, [{k: r[k] for k in generated[0]} for r in report['independent_rows']])
        for rel, expected in report['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/rel).read_bytes()), expected, rel)
        parent = Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(parent.read_bytes()), report['controlled_worker_sha256'])
        self.assertEqual(public.sha(public.initial.AEX.read_bytes()), report['aex_sha256'])
        retained = probe.retained_cases(); self.assertEqual(len(retained), 6601)
        native_count = replays = 0
        with tempfile.TemporaryDirectory(prefix='radial_gain_production_') as name:
            directory = Path(name)
            for row in report['independent_rows']:
                raw, frame, _, close, _ = public.native_render(parent, directory, row)
                self.assertEqual(public.sha(raw), row['reference_raw_sha256'])
                self.assertFalse(frame['render_error']); self.assertTrue(frame['output']['guards_intact'])
                self.assertTrue(close['session_clean']); self.assertFalse(close['unsupported_suite_calls'])
                native_count += 1
                if native_count % 100 == 0: print('GAIN_PRODUCTION_NATIVE', native_count, flush=True)
            for name in ['o2', 'san', 'default']:
                source = public.SOURCE.read_text()
                binary = (probe.profiles.default_contract_build(directory/name, source) if name == 'default'
                          else public.build(directory/name, source, name == 'san'))
                for row in report['rows']+retained+report['independent_rows']:
                    for command in ['classic', 'smart']:
                        error, raw, metadata = public.mac_render(binary, directory, row, command, probe.ENV)
                        expected = row['results'][command]
                        self.assertEqual(error, expected['error'], row)
                        self.assertEqual(public.sha(raw), expected['raw_sha256'], row)
                        self.assertEqual(metadata, expected['metadata'], row)
                        replays += 1
                    if replays % 1000 == 0: print('GAIN_PRODUCTION_PROGRESS', name, replays, flush=True)
        self.assertEqual(native_count, 1140); self.assertEqual(replays, 50610)
        print('GAIN_PRODUCTION', replays, 'NATIVE', native_count, flush=True)

    def test_original_gain_getter_and_declaration(self):
        report = current.capture(); worker = Path(os.environ['RADIAL_WINDOWS_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()), report['window_worker_sha256'])
        self.assertEqual(public.sha(public.initial.AEX.read_bytes()), report['aex_sha256'])
        self.assertEqual(probe.original_rule(), report['original_gain_rule'])
        declaration = report['native_parameter_declarations'][0]
        self.assertEqual((declaration['slot'], declaration['param_type'], declaration['valid_min'],
            declaration['valid_max'], declaration['slider_max'], declaration['precision']), (21, 10, 0, 10, 2, 1))
        with tempfile.TemporaryDirectory(prefix='radial_gain_native_fields_') as name:
            actual = probe.native_fields(worker, Path(name)/'fields')
            self.assertEqual(len(actual), 64)
            for row, expected in zip(actual, report['native_setup_fields']):
                self.assertEqual({k: v for k, v in row.items() if k != 'trace_sha256'},
                                 {k: v for k, v in expected.items() if k != 'trace_sha256'})
        print('GAIN_NATIVE_GETTER 64 FLOAT32_WORDS', flush=True)


    def test_rotation_noise_sampler_against_original_leaf(self):
        live = current.capture()
        report = json.loads((ROOT/'reports/radialblur_gain_sampler_20261002.json').read_text())
        self.assertEqual(live['source_sha256'], report['source_sha256'])
        self.assertEqual(public.sha(public.initial.AEX.read_bytes()), report['aex_sha256'])
        for rel, expected in report['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/rel).read_bytes()), expected, rel)
        sampler = importlib.import_module('probe_radialblur_gain_sampler_20261002')
        with tempfile.TemporaryDirectory(prefix='radial_gain_sampler_actual_') as name:
            actual = sampler.probe(Path(name)/'leaf', public.SOURCE.read_text())
        self.assertEqual(actual, {k: report[k] for k in actual})
        self.assertEqual(actual['case_count'], 1936)
        self.assertEqual(actual['comparisons']['before']['different_words'], 249)
        print('GAIN_NOISE_SAMPLER 1936 ORIGINAL_EXACT OLD_DIFFERENT 249', flush=True)


if __name__ == '__main__': unittest.main()
