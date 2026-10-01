"""Original enabled block, independent tiny Size and composite public outputs."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
probe=importlib.import_module('probe_radialblur_size_enabled_20261002')
current=importlib.import_module('radialblur_current_public_20261001')
public=probe.public


class SizeEnabledTests(unittest.TestCase):
    def test_original_enabled_block_and_actual_sdk_helper(self):
        report=json.loads((ROOT/'reports/radialblur_size_enabled_public_20261002.json').read_text());current.capture()
        self.assertEqual(public.sha(probe.candidate_source(probe.before_source()).encode()),report['source_sha256'])
        self.assertEqual(probe.native_rows(),report['native_enabled_rows'])
        self.assertEqual(len(report['native_enabled_rows']),20)
        for path,expected in report['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/path).read_bytes()),expected,path)
        with tempfile.TemporaryDirectory(prefix='radial_size_enabled_leaf_') as name:
            self.assertEqual(probe.sdk_replay(Path(name),public.SOURCE.read_text(),report['native_enabled_rows']),40)
        print('SIZE_ENABLED_ORIGINAL_BLOCK',20,'SDK',40,flush=True)

    def test_production_public_threshold_noise_and_fade(self):
        report=json.loads((ROOT/'reports/radialblur_size_enabled_public_20261002.json').read_text());current.capture();parent=Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(parent.read_bytes()),report['controlled_worker_sha256'])
        self.assertEqual(public.sha(public.initial.AEX.read_bytes()),report['aex_sha256'])
        cases=probe.independent_cases()
        self.assertEqual(cases,[{k:r[k] for k in cases[0]} for r in report['independent_rows']])
        self.assertEqual(len(cases),720)
        native_count=replays=0
        with tempfile.TemporaryDirectory(prefix='radial_size_enabled_production_') as name:
            directory=Path(name)
            for row in report['independent_rows']:
                raw,frame,_,close,_=public.native_render(parent,directory,row)
                self.assertEqual(public.sha(raw),row['reference_raw_sha256'])
                self.assertFalse(frame['render_error']);self.assertTrue(frame['output']['guards_intact'])
                self.assertTrue(close['session_clean']);self.assertFalse(close['unsupported_suite_calls']);native_count+=1
            for sanitize in [False,True]:
                binary=public.build(directory/('san' if sanitize else 'o2'),public.SOURCE.read_text(),sanitize)
                for row in report['independent_rows']:
                    for command in ['classic','smart']:
                        error,raw,metadata=public.mac_render(binary,directory,row,command,probe.ranges.ENV)
                        expected=row['results'][command]
                        self.assertEqual(error,expected['error']);self.assertEqual(public.sha(raw),expected['raw_sha256'])
                        self.assertEqual(metadata,expected['metadata']);replays+=1
        self.assertEqual(native_count,720);self.assertEqual(replays,2880)
        print('SIZE_ENABLED_PRODUCTION',replays,'NATIVE',native_count,flush=True)

    def test_original_disabled_factors_and_typed_sdk_worlds(self):
        current.capture();factors=importlib.import_module('probe_radialblur_size_disabled_factor_20261002')
        report=json.loads((ROOT/'reports/radialblur_size_disabled_factor_20261002.json').read_text())
        self.assertEqual(json.loads((ROOT/'reports/radialblur_size_enabled_public_20261002.json').read_text())['source_sha256'],report['source_sha256'])
        worker=Path(os.environ['RADIAL_WINDOWS_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()),report['window_worker_sha256'])
        for path,expected in report['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/path).read_bytes()),expected,path)
        with tempfile.TemporaryDirectory(prefix='radial_size_disabled_factors_') as name:
            actual=factors.factor_maps(worker,Path(name),public.SOURCE.read_text())
            self.assertEqual(len(actual),20)
            for row,saved in zip(actual,report['rows']):
                for key in ['case','factor_sha256','word_count','component_areas','typed_sdk_replays']:
                    self.assertEqual(row[key],saved[key])
                for key in ['enabled','normalized_float_word','component_scanner_reached','witness_count','requested_watch_count','guards_intact']:
                    self.assertEqual(row['trace'][key],saved['trace'][key])
        print('SIZE_DISABLED_FACTORS',20,'WORDS',700,'SDK',120,flush=True)


if __name__=='__main__':unittest.main()
