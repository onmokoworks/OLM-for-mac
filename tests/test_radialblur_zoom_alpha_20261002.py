"""Original Zoom sampler boundaries, natural intermediate values and SDK output."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
probe=importlib.import_module('probe_radialblur_zoom_alpha_20261002')
leaf=importlib.import_module('probe_radialblur_zoom_alpha_leaf_20261002')
current=importlib.import_module('radialblur_current_public_20261001')
public=probe.public


class ZoomAlphaTests(unittest.TestCase):
    def test_original_sampler_and_real_sdk_finite_boundaries(self):
        saved=json.loads((ROOT/'reports/radialblur_zoom_alpha_leaf_20261002.json').read_text())
        live=current.capture()
        self.assertEqual(saved['source_sha256'],live['source_sha256'])
        self.assertEqual(saved['header_sha256'],live['header_sha256'])
        self.assertEqual(saved['aex_sha256'],public.sha(public.initial.AEX.read_bytes()))
        self.assertEqual(saved['summary'],{'finite_alpha_boundaries':36,'finite_sampler_cases':44,'native_import_free_calls':44,'typed_sdk_replays':88})
        for path,expected in saved['dependencies_sha256'].items():self.assertEqual(public.sha((ROOT/path).read_bytes()),expected,path)
        rows=leaf.native_rows();self.assertEqual(rows,saved['rows'])
        with tempfile.TemporaryDirectory(prefix='radial_zoom_alpha_sdk_test_') as name:
            self.assertEqual(leaf.sdk_replay(Path(name),public.SOURCE.read_text(),rows),88)
        print('ZOOM_ALPHA_NATIVE_BOUNDARIES',36,'CASES',44,'SDK',88,flush=True)

    def test_current_public_matrix_and_natural_sampler_writer(self):
        report=current.capture();before=json.loads(probe.BEFORE.read_text());extra=json.loads(probe.EXTRA.read_text())
        self.assertEqual(public.SOURCE.read_text(),probe.candidate_source(probe.before_source()))
        self.assertEqual(report['summary'],{'case_count':694,'both_commands_exact':607,'different':3,'mac_rejected':84,'became_exact':6,'lost_exact':0,'raw_changed':6})
        self.assertEqual(report['summary'],probe.writer.summarize(report['rows']))
        for path,expected in report['dependencies_sha256'].items():self.assertEqual(public.sha((ROOT/path).read_bytes()),expected,path)
        worker=Path(os.environ['RADIAL_WINDOWS_WORKER']);parent=Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()),report['window_worker_sha256']);self.assertEqual(public.sha(parent.read_bytes()),report['controlled_worker_sha256'])
        for row,old in zip(report['rows'],before['rows']):
            self.assertEqual(row['input_sha256'],public.sha(public.fixture(row)))
            for key in ['parameters','geometry','depth','pattern','state','family','group','matrix','row_index','input_sha256','reference_raw_sha256']:self.assertEqual(row[key],old[key])
            for command in ['classic','smart']:
                if old['results'][command]['raw_exact']:self.assertEqual(row['results'][command]['raw_sha256'],old['results'][command]['raw_sha256'])
        with tempfile.TemporaryDirectory(prefix='radial_zoom_alpha_production_') as name:
            directory=Path(name);binaries={name:public.build(directory/name,public.SOURCE.read_text(),name=='san') for name in ['o2','san']}
            before_binary=public.build(directory/'before',probe.before_source());replays=0
            for binary in binaries.values():
                for row in report['rows']+extra['rows']:
                    for command in ['classic','smart']:
                        error,raw,metadata=public.mac_render(binary,directory,row,command,leaf.ENV);expected=row['results'][command]
                        self.assertEqual(error,expected['error']);self.assertEqual(public.sha(raw) if not error else None,expected['raw_sha256']);self.assertEqual(metadata,expected['metadata']);replays+=1
            observed=probe.natural(worker,parent,directory,before,before_binary,binaries['o2'])
            self.assertEqual(len(observed),6)
            for actual,saved in zip(observed,report['natural_witnesses']):
                for key in ['case','selected_points','before_raw_sha256','native_raw_sha256','after_raw_sha256','guard_intact','trace_resident_raw_exact','before_different_bytes']:self.assertEqual(actual[key],saved[key])
            self.assertEqual(replays,3160)
            print('ZOOM_ALPHA_PRODUCTION_REPLAYS',replays,'NATURAL_NATIVE',6,flush=True)


if __name__=='__main__':unittest.main()
