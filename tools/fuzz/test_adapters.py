#!/usr/bin/env python3
"""Builder-domain checks and retained public transport anchors for T04."""
from concurrent.futures import ThreadPoolExecutor
import importlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest

sys.dont_write_bytecode = True
from core import evaluate, sha
from run import ROOT, default_worker, main_checkout, run_one, disk_bytes

PLUGINS = ('olmdirectionalblur','olmcolorkey','olmsmoother2','olmkirakira','olmblur',
           'colorkeep','olmdistancegradation','olmsmoother','olmtoondilate')
SCRATCH = Path(os.environ.get('OLM_FUZZ_TEST_SCRATCH', ROOT/'orchestra/state/T04-fuzz-adapters-all-plugins'))


def adapter(name, max_size=32):
    return importlib.import_module('adapters.'+name).Adapter(SimpleNamespace(
        max_size=max_size,case_timeout=10,main=main_checkout(),worker=default_worker()))


class BuilderDomains(unittest.TestCase):
    def test_reproducible_legal_cases_all_plugins(self):
        for name in PLUGINS:
            with self.subTest(plugin=name):
                a = adapter(name)
                bounds = {d['slot']:d for d in a.controls}
                depths = set()
                for index in range(100):
                    c = a.generate(1,index)
                    self.assertEqual(c,a.generate(1,index))
                    depths.add(c['depth'])
                    self.assertEqual(len(c['pixels']),c['geometry'][0]*c['geometry'][1]*c['depth']//8*4)
                    for p in c['parameters']:
                        d = bounds[p['slot']]
                        if p['kind']=='c':
                            self.assertEqual(len(p['value']),4)
                            self.assertTrue(all(0<=v<=255 and int(v)==v for v in p['value']))
                        elif p['kind'] not in ('a','p'):
                            self.assertLessEqual(d['valid_min'],p['value'])
                            self.assertLessEqual(p['value'],d['valid_max'])
                        if p['kind'] in ('f','a'):
                            self.assertEqual(p['value']*65536,round(p['value']*65536))
                self.assertEqual(depths,{8,16,32})

    def test_default_builder_anomalies_are_not_sampled(self):
        for name,slot in [('olmkirakira',5),('olmdistancegradation',2)]:
            a = adapter(name)
            d = next(d for d in a.controls if d['slot']==slot)
            self.assertLess(d['default_value'],d['valid_min'])
            p = next(p for p in a.defaults(5,3) if p['slot']==slot)
            self.assertEqual(p['value'],d['valid_min'])

    def test_degenerate_and_large_geometry(self):
        a = adapter('olmdirectionalblur',256)
        dimensions = {tuple(a.generate(1,i)['geometry']) for i in range(300)}
        self.assertIn((1,1),dimensions)
        self.assertTrue(any(w==1 and h>1 for w,h in dimensions))
        self.assertTrue(any(h==1 and w>1 for w,h in dimensions))
        self.assertTrue(any(max(w,h)>200 for w,h in dimensions))


class CorpusBudget(unittest.TestCase):
    def test_parallel_mismatches_remain_measured_when_corpus_is_full(self):
        class Fake:
            name='test';generator_version=1;max_size=1;routes=('classic','smart')
            def defaults(self,w,h):return []
            def generate(self,seed,index):
                return dict(seed=seed,index=index,geometry=[1,1],depth=8,parameters=[],pixels=bytes(4))
            def oracle(self,*args):return {'status':'ok'},bytes(4)
            def candidate(self,*args):return {'status':'ok'},bytes([1])*4
            def first_stage(self,*args):return None
        SCRATCH.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as td:
            root=Path(td);corpus=root/'corpus';corpus.mkdir()
            args=SimpleNamespace(corpus=corpus,corpus_max_bytes=6000,shrink_seconds=0,shrink_attempts=0)
            deadline=time.monotonic()+10
            with ThreadPoolExecutor(max_workers=4) as pool:
                rows=list(pool.map(lambda i:run_one(Fake(),1,i,root,deadline,args,{}),range(12)))
            self.assertLessEqual(disk_bytes(corpus),6000)
            self.assertTrue(any(r['corpus_retained'] for r in rows))
            self.assertTrue(any(not r['corpus_retained'] for r in rows))
            self.assertTrue(all(r['result']['routes']['smart']['status']=='mismatch' for r in rows))
            self.assertEqual(len(list(corpus.glob('*.json'))),sum(r['corpus_retained'] for r in rows))


@unittest.skipUnless(os.environ.get('OLM_FUZZ_INTEGRATION')=='1','requires retained AEX worker and Mac compiler')
class PublicAnchors(unittest.TestCase):
    def test_kirakira_retained_mode1_three_depths(self):
        """Preserve the Mac/Smart anchor while checking original Classic separately."""
        retained = ROOT/'refs/conformance/olmkirakira_mode1_exported_effectmain_all_depths_20260812.json'
        records = json.loads(retained.read_text())['rows']
        a = adapter('olmkirakira',256)
        SCRATCH.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as td:
            directory = Path(td);deadline=time.monotonic()+90
            provenance = a.prepare(directory,deadline)
            observations = []
            for depth in (8,16,32):
                parameters = a.defaults(5,3)
                # Exact existing public anchor controls, including its captured
                # 0.1 gain. This is a transport regression, not a generated case.
                overrides = {2:1,3:1,5:.1,10:0,16:7,22:0,28:0,34:0,40:0}
                for p in parameters:
                    if p['slot'] in overrides:p['value']=overrides[p['slot']]
                rgba = [(64+i*11,i*15,i*11,i*7) for i in range(15)]
                pixels = b''.join(bytes(v) if depth==8 else struct.pack('<4H',*((c*32768+127)//255 for c in v))
                                  if depth==16 else struct.pack('<4f',*(c/255 for c in v)) for v in rgba)
                case = dict(parameters=parameters,geometry=[5,3],depth=depth,pixels=pixels,input_padding=12,output_padding=12)
                result = evaluate(a,case,directory,deadline)
                expected = next(r['actual_exported_raw_sha256'] for r in records if r['depth']==f'PF{depth}')
                self.assertEqual(result['oracles']['smart'].get('raw_sha256'),expected)
                self.assertEqual(result['routes']['smart']['status'],'exact')
                for route in a.routes:
                    self.assertEqual(result['routes'][route]['raw_sha256'],expected)
                self.assertEqual(result['oracles']['classic'].get('raw_sha256'),sha(bytes(len(pixels))))
                self.assertEqual(result['routes']['classic']['status'],'mismatch')
                observations.append({'depth':depth,'result':result,'expected_sha256':expected})
            (SCRATCH/'kirakira-anchor.json').write_text(json.dumps({
                'provenance':provenance,'retained_report_sha256':sha(retained.read_bytes()),'observations':observations},indent=2)+'\n')


if __name__=='__main__':
    unittest.main()
