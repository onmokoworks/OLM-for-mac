"""Native natural fields, independent frames and row-end area/factor maps."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
probe=importlib.import_module('probe_radialblur_rotation_size_noise_20261001')
independent=importlib.import_module('probe_radialblur_rotation_size_noise_independent_20261001')
components=importlib.import_module('probe_radialblur_size_run_boundary_20261001')
current=importlib.import_module('radialblur_current_public_20261001')
public=probe.public


def saved(name): return json.loads((ROOT/'reports'/name).read_text())
ENV=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')


class RotationSizeNoiseTests(unittest.TestCase):
    def test_production_matrix_and_independent_combinations(self):
        report=current.capture();before=json.loads(probe.BEFORE.read_text());extra=saved('radialblur_rotation_size_noise_independent_20261001.json')
        self.assertEqual(public.SOURCE.read_text(),probe.candidate_source(probe.before_source()))
        self.assertEqual(report['summary'],{'case_count':694,'both_commands_exact':601,'different':9,'mac_rejected':84,'became_exact':36,'lost_exact':0,'raw_changed':36})
        self.assertEqual(report['summary'],probe.writer.summarize(report['rows']))
        self.assertEqual(extra['source_sha256'],report['source_sha256'])
        self.assertEqual(extra['summary'],{'case_count':96,'both_commands_exact':96,'mac_rejected':0,'before_classic_exact':0,'became_exact':96})
        for data in [report,extra]:
            for name,expected in data['dependencies_sha256'].items(): self.assertEqual(public.sha((ROOT/name).read_bytes()),expected,name)
        parent=Path(os.environ['RADIAL_PARENT_WORKER']);self.assertEqual(public.sha(parent.read_bytes()),report['controlled_worker_sha256'])
        with tempfile.TemporaryDirectory(prefix='radial_size_noise_production_') as name:
            directory=Path(name);new_count=0;native_count=0;replays=0
            for row,old in zip(report['rows'],before['rows']):
                for key in ['parameters','geometry','depth','pattern','state','family','group','matrix','row_index','input_sha256','reference_raw_sha256']: self.assertEqual(row[key],old[key])
                self.assertEqual(public.sha(public.fixture(row)),row['input_sha256'])
                for command in ['classic','smart']:
                    if old['results'][command]['raw_exact']: self.assertEqual(row['results'][command]['raw_sha256'],old['results'][command]['raw_sha256'])
                if row['results']['classic']['raw_exact'] and not old['results']['classic']['raw_exact']:
                    raw,frame,_,close,_=public.native_render(parent,directory,row)
                    self.assertEqual(public.sha(raw),row['reference_raw_sha256']);self.assertFalse(frame['render_error']);self.assertTrue(frame['output']['guards_intact'])
                    self.assertTrue(close['session_clean']);self.assertFalse(close['unsupported_suite_calls']);new_count+=1
            generated=independent.cases()
            self.assertEqual(generated,[{key:row[key] for key in generated[0]} for row in extra['rows']])
            for row in extra['rows']:
                raw,frame,_,close,_=public.native_render(parent,directory,row)
                self.assertEqual(public.sha(raw),row['reference_raw_sha256']);self.assertFalse(frame['render_error']);self.assertTrue(frame['output']['guards_intact'])
                self.assertTrue(close['session_clean']);self.assertFalse(close['unsupported_suite_calls']);native_count+=1
            for sanitize in [False,True]:
                binary=public.build(directory/('san' if sanitize else 'o2'),public.SOURCE.read_text(),sanitize)
                for row in report['rows']+extra['rows']:
                    for command in ['classic','smart']:
                        error,raw,metadata=public.mac_render(binary,directory,row,command,ENV);expected=row['results'][command]
                        self.assertEqual(error,expected['error']);self.assertEqual(public.sha(raw) if not error else None,expected['raw_sha256']);self.assertEqual(metadata,expected['metadata']);replays+=1
                print('SIZE_NOISE_PRODUCTION_REPLAYS',replays,flush=True)
        self.assertEqual(new_count,36);self.assertEqual(native_count,96);self.assertEqual(replays,2776+384)

    def test_natural_owned_planes_all_twelve_inputs(self):
        report=current.capture();worker=Path(os.environ['RADIAL_WINDOWS_WORKER']);self.assertEqual(public.sha(worker.read_bytes()),report['window_worker_sha256'])
        before=json.loads(probe.BEFORE.read_text());self.assertEqual(report['natural_owned_field_words'],3934002)
        with tempfile.TemporaryDirectory(prefix='radial_size_noise_planes_') as name:
            observed=probe.natural(worker,Path(name),before,probe.before_source(),public.SOURCE.read_text())
            self.assertEqual(len(observed),12)
            for actual,expected in zip(observed,report['natural_witnesses']):
                for key in ['field_comparisons','mac_raw_sha256','mac_dimensions','candidate_raw_exact','legacy_comparison_planes']: self.assertEqual(actual[key],expected[key])
                self.assertEqual(set(actual['field_comparisons']['before']),{'polar','normalized','span'})
                self.assertTrue(all(value['different_words']==0 for value in actual['field_comparisons']['candidate'].values()))

    def test_run_count_overwrite_and_typed_factor_maps(self):
        report=saved('radialblur_size_run_boundary_20261001.json');live=current.capture()
        self.assertEqual(report['source_sha256'],live['source_sha256']);self.assertEqual(report['summary'],{'case_count':28,'native_source_maps_exact':28,'typed_sdk_replays':168})
        self.assertEqual([row['case'] for row in report['rows']],components.fixtures())
        for name,expected in report['dependencies_sha256'].items():self.assertEqual(public.sha((ROOT/name).read_bytes()),expected,name)
        worker=Path(os.environ['RADIAL_WINDOWS_WORKER']);self.assertEqual(public.sha(worker.read_bytes()),report['window_worker_sha256'])
        with tempfile.TemporaryDirectory(prefix='radial_size_run_production_') as name:
            directory=Path(name);harness=public.initial.HARNESS
            try:
                public.initial.HARNESS=ROOT/'tools/emulation/radialblur_size_factor_sdk_harness_20261001.cpp'
                binaries={name:public.build(directory/name,public.SOURCE.read_text(),name=='san') for name in ['o2','san']}
            finally:public.initial.HARNESS=harness
            for row in report['rows']:
                case=row['case'];temp=directory/f"case_{case['row_index']}";temp.mkdir()
                area,factor,maximum,trace=components.trace(worker,temp,case)
                model_area,model_factor,model_maximum,areas=components.component_model(*case['geometry'],case['mask'],case['size'])
                self.assertEqual(area,model_area);self.assertEqual(factor,model_factor);self.assertEqual(maximum,model_maximum)
                self.assertEqual(maximum,row['maximum_area']);self.assertEqual(areas,row['component_areas'])
                self.assertEqual(public.sha(area),row['area_sha256']);self.assertEqual(public.sha(factor),row['factor_sha256']);self.assertEqual(trace['mask_guard_byte'],0)
                for binary in binaries.values():
                    for depth in [8,16,32]:
                        path=temp/f'input_{depth}.raw';path.write_bytes(components.source(case,depth))
                        run=subprocess.run([str(binary),*map(str,case['geometry']),str(depth),str(case['size']),str(path)],capture_output=True,check=True,env=ENV)
                        self.assertEqual(run.stdout,factor);self.assertEqual(run.stderr.decode().strip(),'AREAS'+''.join(' '+str(a) for a in areas))
        print('SIZE_RUN_NATIVE_MAPS',28,'TYPED_SDK',168,flush=True)


if __name__=='__main__':unittest.main()
