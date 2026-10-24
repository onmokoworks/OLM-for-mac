"""Sampler and corpus contracts, independent of any unqualified geometry host."""
import copy
import importlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from core import apply_operation, evaluate, load_corpus, save_corpus, shrink
import time
from geometry import VERSION, require_host, sample
from run import main_checkout, ROOT

PLUGINS = ('colorkeep','olmdistancegradation','olmkirakira','radialblur',
           'olmtoondilate','olmsmoother2','olmsmoother','olmblur',
           'olmcolorkey','olmdirectionalblur')


def adapter(name):
    return importlib.import_module('adapters.'+name).Adapter(SimpleNamespace(
        max_size=256, case_timeout=10, main=main_checkout(), worker=Path('/usr/bin/true')))


class GeometryTests(unittest.TestCase):
    def assertGeometry(self, case):
        w,h = case['geometry']
        self.assertEqual([w,h],[(n*a+b-1)//b for n,(a,b) in zip(case['full_geometry'],case['downsample'])])
        self.assertEqual(len(case['pixels']),w*h*case['depth']//8*4)
        for key in ('extent_hint','request_rect'):
            l,t,r,b = case[key]
            self.assertTrue(0 <= l < r <= w and 0 <= t < b <= h)
        self.assertEqual(case['input_padding'],case['output_padding'])

    def test_all_plugin_sampling_and_crop(self):
        ratios,pads,aspects,partial = set(),set(),set(),0
        for name in PLUGINS:
            a = adapter(name)
            for index in range(100):
                original = a.generate(1,index); before = copy.deepcopy(original)
                self.assertIs(sample(original),original)
                case = sample(original,'realistic')
                self.assertEqual(original,before)
                self.assertEqual(case,sample(a.generate(1,index),'realistic'))
                self.assertGeometry(case)
                self.assertGeometry(apply_operation(a,case,{'kind':'crop','geometry':[1,1]}))
                ratios.add(tuple(map(tuple,case['downsample'])))
                pads.add(case['rowbytes_padding']);aspects.add(tuple(case['pixel_aspect']))
                partial += case['request_rect'] != [0,0,*case['geometry']]
        self.assertEqual(len(ratios),6);self.assertEqual(len(pads),6)
        self.assertEqual(len(aspects),4);self.assertGreater(partial,0)

    def test_replay_embedded_and_procedural(self):
        a = adapter('radialblur')
        original = sample(a.generate(1,3),'realistic')
        operations = [{'kind':'crop','geometry':[1,1]}, {'kind':'pixels','value':'zero'}]
        reduced = original
        for op in operations:
            reduced = apply_operation(a,reduced,op)
        scratch = Path(os.environ['OLM_FUZZ_TEST_SCRATCH']);scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as td:
            path = Path(td)/'case.json'
            saved = save_corpus(path,a,original,reduced,{}, {'accepted':operations},{})
            self.assertEqual(load_corpus(path,a)[0],reduced)
            saved.pop('pixels_zlib_base64')
            path.write_text(json.dumps(saved))
            self.assertEqual(load_corpus(path,a)[0],reduced)

    def test_unqualified_host_rejected(self):
        a = adapter('radialblur')
        a.geometry_samplers=()
        require_host(a,a.generate(1,0))
        with self.assertRaisesRegex(ValueError,'not qualified'):
            require_host(a,sample(a.generate(1,0),'realistic'))
        a.geometry_samplers = (VERSION,)
        require_host(a,sample(a.generate(1,0),'realistic'))

    def test_shrink_driver(self):
        from test_framework import Synthetic
        a = Synthetic()
        case = sample(a.generate(1,0),'realistic')
        # Use an index whose sampled dimensions preserve a shrinkable mismatch.
        for index in range(100):
            case = sample(a.generate(1,index),'realistic')
            if min(case['geometry']) >= 4:
                break
        scratch = Path(os.environ['OLM_FUZZ_TEST_SCRATCH'])
        scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as td:
            directory = Path(td); deadline = time.monotonic()+5
            observed = evaluate(a,case,directory,deadline)
            reduced,_,reduction = shrink(a,case,observed,directory,deadline,32)
            self.assertGreater(len(reduction['accepted']),0)
            self.assertGeometry(reduced)

    def test_oracle_geometry_arguments(self):
        from adapters.public import geometry_arguments
        case=sample(adapter('olmblur').generate(1,0),'realistic')
        smart=geometry_arguments(case,'smart');classic=geometry_arguments(case,'classic')
        self.assertIn('--negotiate-output',smart)
        self.assertIn('--request-rect',smart)
        self.assertNotIn('--request-rect',classic)  # Classic has no Smart request.
        self.assertIn('--extent-hint',classic)
        self.assertEqual(geometry_arguments(adapter('olmblur').generate(1,0)),[])

    def test_equal_bytes_different_rect_is_mismatch(self):
        class Rectangles:
            routes=('smart',)
            def oracle(self,*args):return {'status':'ok','output_rect':[0,0,1,1]},bytes(4)
            def candidate(self,*args):return {'status':'ok','output_rect':[1,0,2,1]},bytes(4)
            def first_stage(self,*args):return None
        result=evaluate(Rectangles(),{'depth':8,'pixels':bytes(4)},Path('.'),time.monotonic()+1)
        self.assertEqual(result['routes']['smart']['status'],'mismatch')
        self.assertEqual(result['routes']['smart']['geometry_diff']['actual'],[1,0,2,1])

    def test_classic_only_geometry_routes(self):
        a=adapter('olmsmoother')
        require_host(a,sample(a.generate(1,0),'realistic'))
        self.assertEqual(a.routes,('classic',))
        require_host(a,a.generate(1,0))
        self.assertEqual(a.routes,('classic','smart'))

    def test_unknown_version_rejected(self):
        with self.assertRaises(ValueError):
            sample(adapter('radialblur').generate(1,0),'realistic-v999')
