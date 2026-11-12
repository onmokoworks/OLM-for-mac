import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import olm_oracle as o
import oracle_workflows as w


class WorkflowTests(unittest.TestCase):
    def test_check_build_stage_and_campaign(self):
        for full in (False, True):
            with self.subTest(full=full), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                original, dll = root / 'Original.aex', root / 'new.dll'
                original.write_bytes(b'original')
                dll.write_bytes(b'candidate')
                args = SimpleNamespace(out=root/'check', crate='new-plugin', full=full,
                    reference=original, originals=root, rust_root=root, harness=original,
                    jobs=3, timeout=120, build_timeout=30, lib_name=None, seed=3)
                build = dict(returncode=0, timeout=False, stdout=json.dumps({'reason':'compiler-artifact',
                    'target':{'name':'new_plugin','crate_types':['cdylib']}, 'filenames':[str(dll)]}))
                inventory = {'parameters':[], 'host':{}}
                def render(a):
                    self.assertEqual(a.cases, 20 if full else 6)
                    self.assertEqual(a.candidate.name, original.name)
                    self.assertEqual(a.candidate.read_bytes(), b'candidate')
                    self.assertEqual(a.jobs, 3)
                    a.out.mkdir()
                    o.write_json(a.out/'summary.json', {'routes':{'smart8':{'cases_run':a.cases}}})
                    return 0
                with patch.object(o, 'run_process', return_value=build) as run, patch.object(o, 'inspect', return_value=inventory), patch.object(o, 'render', side_effect=render):
                    self.assertEqual(w.check(args, o), 0)
                argv = run.call_args.args[0]
                self.assertEqual(argv[:5], ['cargo','build','--release','-p','new-plugin'])
                self.assertIn('--locked', argv)
                self.assertEqual(run.call_args.kwargs['cwd'], root)
                self.assertEqual(original.read_bytes(), b'original')
                self.assertEqual(json.loads((args.out/'summary.json').read_text())['verdict'], 'PASS')
                # A render claiming success without evidence must fail closed.
                args.out=root/'missing-summary'
                with patch.object(o,'run_process',return_value=build), patch.object(o,'inspect',return_value=inventory), patch.object(o,'render',return_value=0):
                    self.assertEqual(w.check(args,o),2)
                self.assertEqual(json.loads((args.out/'summary.json').read_text())['verdict'],'ERROR')

    def test_check_build_failure_does_not_inspect_or_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root/'OLMBlur.aex'
            original.write_bytes(b'aex')
            args = SimpleNamespace(out=root/'check', crate='olm-blur', full=False, reference=None,
                originals=root, rust_root=root, harness=original, jobs=1, build_timeout=1)
            with patch.object(o, 'run_process', return_value={'returncode':1,'timeout':False}), patch.object(o, 'inspect') as inspect:
                self.assertEqual(w.check(args, o), 2)
                inspect.assert_not_called()
            with self.assertRaises(ValueError):
                w.dll_from_build('{}', 'missing')
        self.assertEqual(len(w.CRATES), 10)

    def bundle(self, root):
        executable = root/'dummy.aex'
        executable.write_bytes(b'dummy')
        case = {'index':0,'size':[16,8],'downsample':'1/2','assignments':[], 'untouched_defaults':[]}
        requests = {s:{'schema_version':1,'assignments':[], 'host_context':{'spatial':{
            'downsample_x':{'numerator':1,'denominator':2},'downsample_y':{'numerator':1,'denominator':2},
            'full_resolution_width':32,'full_resolution_height':16}}} for s in ('reference','candidate')}
        requests['reference']['assignments'] = [{'slot':2,'value':9}]
        requests['candidate']['assignments'] = [{'slot':1,'value':1},{'slot':2,'value':9}]
        state = {'manifest':{'case':case, 'route':'smart8','tool':o.identity(o.__file__),
                 **{s:o.identity(executable) for s in ('harness','reference','candidate')}},
                 'assets':{},'requests':requests,'images':{'input.png':Image.fromarray(o.input_pixels(16,8,2))}}
        w.write_bundle(root/'source', state, o)
        # Original run_case uses OS-native path separators on Windows.
        manifest_path = root/'source/case.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['assets'] = {str(Path(k)): v for k,v in manifest['assets'].items()}
        o.write_json(manifest_path, manifest)
        return root/'source'

    def fake_evaluate(self, directory, manifest, timeout):
        a = np.asarray(Image.open(directory/'input.png')).copy()
        req = json.loads((directory/'requests/candidate.json').read_text())
        mismatch = a.shape[1] >= 2 and any(x['slot']==1 for x in req['assignments'])
        b = a.copy()
        if mismatch:
            b[0,0,0] ^= 1
        Image.fromarray(a).save(directory/'reference.png')
        Image.fromarray(b).save(directory/'candidate.png')
        result = {'status':'mismatched' if mismatch else 'exact'}
        o.write_json(directory/'diff.json', result)
        return result

    def test_minimize_preserves_only_mismatch_and_replayable_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=self.bundle(root)
            original_hash=o.sha256(source/'case.json')
            args=SimpleNamespace(case_dir=source,out=root/'min',timeout=1,max_attempts=80,confirmations=2)
            with patch.object(o,'evaluate_case',side_effect=self.fake_evaluate):
                self.assertEqual(w.minimize(args,o),0)
            report=json.loads((args.out/'summary.json').read_text())
            self.assertEqual(report['final_size'],[2,1])
            self.assertEqual(report['minimality'],'local_minimum_under_documented_moves')
            self.assertEqual(report['first_difference']['channel'],'R')
            loaded=w.load_bundle(Path(report['minimal_case_dir']),o)
            self.assertEqual(loaded['requests']['reference']['assignments'],[])
            self.assertEqual(loaded['requests']['candidate']['assignments'],[{'slot':1,'value':1}])
            self.assertEqual(loaded['requests']['candidate']['host_context']['spatial']['downsample_x'],{'numerator':1,'denominator':1})
            self.assertEqual(o.sha256(source/'case.json'),original_hash)
            self.assertTrue(any(not s['accepted'] for s in report['steps']))
            self.assertTrue(all(len(s['results'])==2 for s in report['steps'] if s['accepted']))

    def test_minimize_refuses_unstable_baseline_and_changed_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=self.bundle(root)
            args=SimpleNamespace(case_dir=source,out=root/'min',timeout=1,max_attempts=4,confirmations=2)
            with patch.object(o,'evaluate_case',side_effect=[{'status':'mismatched'},{'status':'reference_unrenderable'}]):
                self.assertEqual(w.minimize(args,o),2)
            (root/'dummy.aex').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                w.load_bundle(source,o)

    def test_sweep_defaults_one_slot_and_identical_input_seed(self):
        params=[dict(slot=1,kind='float',minimum=1,maximum=100,value=.1,color=[0]*4,components=[0]*3),
                dict(slot=2,kind='integer',minimum=0,maximum=1,value=0,color=[0]*4,components=[0]*3)]
        before=copy.deepcopy(params)
        cases=o.generate_sweep_cases(params,seed=33)
        self.assertEqual(cases,o.generate_sweep_cases(params,seed=33))
        self.assertEqual(cases[0]['assignments'],[])
        self.assertTrue(all(len(c['assignments'])==1 for c in cases[1:]))
        self.assertEqual(len({c['input_seed'] for c in cases}),1)
        self.assertEqual(params,before)
        self.assertTrue(all(1<=a['value']<=100 for c in cases for a in c['assignments'] if a['slot']==1))

    def test_float_first_difference_reports_raw_signed_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for side in ('reference','candidate'):
                Image.new('RGBA',(1,1)).save(root/(side+'.png'))
            a=np.array([0,0,0,0],dtype='<u4')
            b=a.copy()
            b[2]=0x80000000
            (root/'reference.rgba32f-le').write_bytes(a.tobytes())
            (root/'candidate.rgba32f-le').write_bytes(b.tobytes())
            first=w.first_difference(root,'smart32',o)
            self.assertEqual(first['channel_index'],2)
            self.assertEqual(first['channel'],'G')
            self.assertEqual(first['reference_bits'],'0x00000000')
            self.assertEqual(first['candidate_bits'],'0x80000000')

    def test_minimize_budget_does_not_claim_minimality(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=self.bundle(root)
            args=SimpleNamespace(case_dir=source,out=root/'min',timeout=1,max_attempts=1,confirmations=2)
            with patch.object(o,'evaluate_case',side_effect=self.fake_evaluate):
                self.assertEqual(w.minimize(args,o),0)
            report=json.loads((args.out/'summary.json').read_text())
            self.assertEqual(report['final_size'],[16,8])
            self.assertEqual(report['minimality'],'attempt_budget_exhausted')


if __name__ == '__main__':
    unittest.main()
