"""Production Noise percentage, retained outputs and original scalar fields."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
probe=importlib.import_module('probe_radialblur_noise_range_20261002')
current=importlib.import_module('radialblur_current_public_20261001')
public=probe.public


class NoiseRangeTests(unittest.TestCase):
    def test_actual_public_percentage_and_retained_cases(self):
        report=current.capture();before=json.loads(probe.BEFORE.read_text())
        self.assertEqual(public.SOURCE.read_text(),probe.candidate_source(probe.before_source()))
        self.assertEqual(report['summary'],before['summary'])
        generated=probe.independent_cases()
        self.assertEqual(generated,[{k:r[k] for k in generated[0]} for r in report['independent_rows']])
        for rel,expected in report['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/rel).read_bytes()),expected,rel)
        parent=Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(parent.read_bytes()),report['controlled_worker_sha256'])
        self.assertEqual(public.sha(public.initial.AEX.read_bytes()),report['aex_sha256'])
        retained=probe.retained_cases();self.assertEqual(len(retained),1855)
        native_count=replays=0
        with tempfile.TemporaryDirectory(prefix='radial_noise_range_production_') as name:
            directory=Path(name)
            for row in report['independent_rows']:
                raw,frame,_,close,_=public.native_render(parent,directory,row)
                self.assertEqual(public.sha(raw),row['reference_raw_sha256'])
                self.assertFalse(frame['render_error']);self.assertTrue(frame['output']['guards_intact'])
                self.assertTrue(close['session_clean']);self.assertFalse(close['unsupported_suite_calls']);native_count+=1
            for sanitize in [False,True]:
                binary=public.build(directory/('san' if sanitize else 'o2'),public.SOURCE.read_text(),sanitize)
                for row in report['rows']+retained+report['independent_rows']:
                    for command in ['classic','smart']:
                        error,raw,metadata=public.mac_render(binary,directory,row,command,probe.ENV)
                        expected=row['results'][command]
                        self.assertEqual(error,expected['error']);self.assertEqual(public.sha(raw),expected['raw_sha256'])
                        self.assertEqual(metadata,expected['metadata']);replays+=1
        self.assertEqual(native_count,952);self.assertEqual(replays,14004)
        print('NOISE_RANGE_PRODUCTION',replays,'NATIVE',native_count,flush=True)

    def test_original_percentage_and_composition_fields(self):
        report=current.capture();worker=Path(os.environ['RADIAL_WINDOWS_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()),report['window_worker_sha256'])
        with tempfile.TemporaryDirectory(prefix='radial_noise_range_scalars_') as name:
            actual=probe.scalar_maps(worker,Path(name),report['independent_rows'],public.SOURCE.read_text())
            self.assertEqual(len(actual),16)
            for row,saved in zip(actual,report['scalar_maps']):
                for key in ['case','normalized_noise_float_word','native_noise_type','smooth_flag','base_sha256','mixed_sha256','word_count','guards_intact','base_and_mixed_exact']:
                    self.assertEqual(row[key],saved[key])
        self.assertEqual(report['scalar_map_words'],4080)
        print('NOISE_RANGE_ORIGINAL_SCALAR_MAPS',16,'WORDS_PER_PLANE',4080,flush=True)


if __name__=='__main__':unittest.main()
