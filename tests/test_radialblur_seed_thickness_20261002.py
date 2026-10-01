"""Actual SDK legal profiles, original initialized grids and isolated core change."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
probe=importlib.import_module('probe_radialblur_seed_thickness_20261002')
grid=importlib.import_module('probe_radialblur_seed_thickness_grid_20261002')
current=importlib.import_module('radialblur_current_public_20261001')
public=probe.public


class SeedThicknessTests(unittest.TestCase):
    def test_actual_public_seed_thickness_and_retained_cases(self):
        live=current.capture();report=json.loads((ROOT/'reports/radialblur_seed_thickness_public_20261002.json').read_text())
        self.assertEqual(public.sha(probe.candidate_source(probe.before_source()).encode()),report['source_sha256'])
        self.assertEqual(live['summary'],report['summary'])
        self.assertEqual(report['summary'],json.loads(probe.BEFORE.read_text())['summary'])
        generated=probe.independent_cases()
        self.assertEqual(generated,[{k:r[k] for k in generated[0]} for r in report['independent_rows']])
        for rel,expected in report['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/rel).read_bytes()),expected,rel)
        parent=Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(parent.read_bytes()),report['controlled_worker_sha256'])
        self.assertEqual(public.sha(public.initial.AEX.read_bytes()),report['aex_sha256'])
        retained=probe.retained_cases();self.assertEqual(len(retained),2807)
        native_count=replays=0
        with tempfile.TemporaryDirectory(prefix='radial_seed_thickness_production_') as name:
            directory=Path(name)
            for row in report['independent_rows']:
                raw,frame,_,close,_=public.native_render(parent,directory,row)
                self.assertEqual(public.sha(raw),row['reference_raw_sha256'])
                self.assertFalse(frame['render_error']);self.assertTrue(frame['output']['guards_intact'])
                self.assertTrue(close['session_clean']);self.assertFalse(close['unsupported_suite_calls']);native_count+=1
            for name in ['o2','san','default']:
                binary=(probe.default_contract_build(directory/name,public.SOURCE.read_text()) if name=='default'
                        else public.build(directory/name,public.SOURCE.read_text(),name=='san'))
                for row in report['rows']+retained+report['independent_rows']:
                    for command in ['classic','smart']:
                        error,raw,metadata=public.mac_render(binary,directory,row,command,probe.ENV)
                        expected=row['results'][command]
                        self.assertEqual(error,expected['error']);self.assertEqual(public.sha(raw),expected['raw_sha256'])
                        self.assertEqual(metadata,expected['metadata']);replays+=1
                    if replays%1000==0:print('SEED_THICKNESS_PRODUCTION_PROGRESS',name,replays,flush=True)
        self.assertEqual(native_count,1532);self.assertEqual(replays,30198)
        print('SEED_THICKNESS_PRODUCTION',replays,'NATIVE',native_count,flush=True)

    def test_original_initialized_grid_against_actual_core(self):
        live=current.capture();report=json.loads((ROOT/'reports/radialblur_seed_thickness_grid_20261002.json').read_text())
        self.assertEqual(report['core_sha256'],live['core_sha256'])
        worker=Path(os.environ['RADIAL_WINDOWS_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()),report['worker_sha256'])
        self.assertEqual(public.sha(public.initial.AEX.read_bytes()),report['aex_sha256'])
        self.assertEqual(grid.original_rule(),report['native_dimension_rule'])
        declarations={p['slot']:p for p in report['native_parameter_declarations']}
        self.assertEqual((declarations[27]['param_type'],declarations[27]['valid_min'],declarations[27]['valid_max']),(1,1,1000))
        self.assertEqual((declarations[29]['param_type'],declarations[29]['valid_min'],declarations[29]['valid_max']),(10,1,100))
        for rel,expected in report['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/rel).read_bytes()),expected,rel)
        with tempfile.TemporaryDirectory(prefix='radial_seed_grid_actual_') as name:
            actual=grid.grid_maps(worker,Path(name)/'grid',probe.CORE.read_text())
            self.assertEqual(len(actual),20)
            for row,saved in zip(actual,report['rows']):
                self.assertEqual({k:v for k,v in row.items() if k!='trace_sha256'},
                                 {k:v for k,v in saved.items() if k!='trace_sha256'})
        self.assertEqual(sum(r['plane_word_count'] for r in actual),2080)
        self.assertEqual(sum(r['division_changes_dimensions'] for r in actual),16)
        print('SEED_THICKNESS_ORIGINAL_GRIDS 20 WORDS 2080 DIVISION_COUNTEREXAMPLES 16',flush=True)

    def test_core_change_is_isolated_to_radial_dimensions_and_contract(self):
        current.capture()
        before=probe.before_core();actual=probe.CORE.read_text()
        self.assertEqual(actual,probe.candidate_core(before))
        marker='inline bool generate_radial_noise_plane('
        self.assertEqual(before.split(marker)[0],actual.split(marker)[0])
        # All RNG conversion/interpolation statements remain byte-for-byte.
        self.assertEqual(before.split(marker)[1].split('    std::mt19937 random(seed);')[1],
                         actual.split(marker)[1].split('    std::mt19937 random(seed);')[1])


if __name__=='__main__':unittest.main()
