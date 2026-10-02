"""Replay actual public Strength paths and original same-input witnesses."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/emulation'))
probe = importlib.import_module('probe_radialblur_strength_20261002')
current = importlib.import_module('radialblur_current_public_20261001')
public = probe.public
witness = importlib.import_module('probe_radialblur_strength_witnesses_20261002')


class StrengthTests(unittest.TestCase):
    def report(self):
        live = current.capture()
        archived = json.loads(probe.public.ROOT.joinpath('reports/radialblur_strength_public_20261002.json').read_text())
        self.assertEqual(public.sha(probe.candidate_source(probe.before_source()).encode()), archived['source_sha256'])
        self.assertEqual(live['summary'], archived['summary'])
        return archived

    def test_actual_public_strength_and_retained_cases(self):
        report = self.report()
        self.assertFalse(report['pilot'])
        self.assertEqual(report['summary'], json.loads(probe.BEFORE.read_text())['summary'])
        generated = probe.independent_cases()
        self.assertEqual(generated, [{k: r[k] for k in generated[0]} for r in report['independent_rows']])
        for rel, expected in report['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/rel).read_bytes()), expected, rel)
        parent = Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(parent.read_bytes()), report['controlled_worker_sha256'])
        self.assertEqual(public.sha(public.initial.AEX.read_bytes()), report['aex_sha256'])
        retained = probe.retained_cases(); self.assertEqual(len(retained), 7741)
        native_count = replays = 0
        with tempfile.TemporaryDirectory(prefix='radial_strength_production_') as name:
            directory = Path(name)
            for row in report['independent_rows']:
                raw, frame, _, close, _ = public.native_render(parent, directory, row)
                self.assertEqual(public.sha(raw), row['reference_raw_sha256'])
                self.assertFalse(frame['render_error']); self.assertTrue(frame['output']['guards_intact'])
                self.assertTrue(close['session_clean']); self.assertFalse(close['unsupported_suite_calls'])
                if row['group'] == 'zero_copy': self.assertEqual(raw, public.fixture(row))
                native_count += 1
                if native_count % 100 == 0: print('STRENGTH_PRODUCTION_NATIVE', native_count, flush=True)
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
                    if replays % 1000 == 0: print('STRENGTH_PRODUCTION_PROGRESS', name, replays, flush=True)
        self.assertEqual(native_count, 1128); self.assertEqual(replays, 57378)
        print('STRENGTH_PRODUCTION', replays, 'NATIVE', native_count, flush=True)

    def test_original_strength_getters_and_quality_scaling(self):
        report = self.report(); saved = report['native_setup_fields']
        worker = Path(os.environ['RADIAL_WINDOWS_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()), report['window_worker_sha256'])
        self.assertEqual(probe.original_rule(), report['original_strength_rule'])
        self.assertEqual(len(report['native_parameter_declarations']), 2)
        for declaration in report['native_parameter_declarations']:
            self.assertEqual((declaration['valid_min'], declaration['valid_max'], declaration['slider_max']), (0, 2000, 2000))
        with tempfile.TemporaryDirectory(prefix='radial_strength_fields_actual_') as name:
            actual = witness.native_fields(worker, Path(name)/'fields')
        self.assertEqual(len(actual), 80)
        for row, expected in zip(actual, saved):
            self.assertEqual({k: v for k, v in row.items() if k != 'trace_sha256'},
                             {k: v for k, v in expected.items() if k != 'trace_sha256'})
        print('STRENGTH_NATIVE_FIELDS 80 RAW_INTEGER_AND_SCALED_CONTROLS', flush=True)

    def test_all_legal_positive_strength_weight_tables(self):
        report = self.report(); saved = report['strength_tables']
        tables = importlib.import_module('probe_radialblur_strength_tables_20261002')
        with tempfile.TemporaryDirectory(prefix='radial_strength_tables_actual_') as name:
            actual = tables.probe(Path(name)/'tables', public.SOURCE.read_text())
        self.assertEqual(actual, saved)
        self.assertEqual(actual['case_count'], 2000); self.assertEqual(actual['word_count'], 2001000)
        self.assertEqual(actual['import_call_count'], 3000)
        print('STRENGTH_TABLES 2000 LENGTHS 2001000 WORDS ORIGINAL_EXACT', flush=True)

    def test_historical_native_ucrt_strength290_public_hash(self):
        report = self.report()
        with tempfile.TemporaryDirectory(prefix='radial_strength290_actual_') as name:
            actual = witness.historical_replay(Path(name)/'historical', public.SOURCE.read_text())
        self.assertEqual(actual, report['historical_native_ucrt_replay'])
        self.assertTrue(all(r['native_raw_exact'] for r in actual['results'].values()))
        self.assertEqual(actual['previous_different_float_words'], 80)
        print('STRENGTH290 RETAINED_NATIVE_UCRT_HASH 6 PUBLIC_EXACT', flush=True)

    def test_natural_strength_table_and_rotation_cap_planes(self):
        report = self.report()
        planes = importlib.import_module('probe_radialblur_strength_planes_20261002')
        worker = Path(os.environ['RADIAL_WINDOWS_WORKER'])
        parent = Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()), report['window_worker_sha256'])
        self.assertEqual(public.sha(parent.read_bytes()), report['controlled_worker_sha256'])
        with tempfile.TemporaryDirectory(prefix='radial_strength_planes_actual_') as name:
            actual = planes.probe(worker, parent, Path(name)/'planes', public.SOURCE.read_text())
        for row, expected in zip(actual, report['natural_strength_witnesses']):
            for key in ['case', 'comparisons', 'raw_sha256', 'counterfactual_source_sha256',
                        'native_gaussian_sha256']:
                self.assertEqual(row[key], expected[key], key)
            self.assertEqual(row['candidate_source_sha256'], current.capture()['source_sha256'])
        self.assertEqual(len(actual), 2)
        print('STRENGTH_NATURAL 2 ALL_OWNED_PLANES_AND_RAW_EXACT', flush=True)


if __name__ == '__main__': unittest.main()
