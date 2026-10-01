"""Actual SDK and original AEX for all100 outer fade lengths on opaque PF32."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
probe=importlib.import_module('probe_radialblur_zoom_fade_20261002')
current=importlib.import_module('radialblur_current_public_20261001')
public=probe.public


class ZoomOuterFadeTests(unittest.TestCase):
    def test_all_outer_fade_lengths_on_actual_public_sdk(self):
        report=json.loads((ROOT/'reports/radialblur_zoom_fade_outer_public_20261002.json').read_text());live=current.capture()
        self.assertEqual(report['source_sha256'],live['source_sha256']);self.assertEqual(report['summary'],{'case_count':100,'both_commands_exact':100,'typed_sdk_public_replays':400})
        for path,expected in report['dependencies_sha256'].items():self.assertEqual(public.sha((ROOT/path).read_bytes()),expected,path)
        parent=Path(os.environ['RADIAL_PARENT_WORKER']);self.assertEqual(public.sha(parent.read_bytes()),report['controlled_worker_sha256'])
        with tempfile.TemporaryDirectory(prefix='radial_zoom_outer_fade_') as name:
            directory=Path(name);binaries={name:public.build(directory/name,public.SOURCE.read_text(),name=='san') for name in ['o2','san']}
            for index,row in enumerate(report['rows']):
                self.assertEqual(row['geometry'],[20,14]);self.assertEqual(row['depth'],32);self.assertEqual(row['pattern'],'opaque')
                self.assertEqual(next(p['value'] for p in row['parameters'] if p['slot']==13),0)
                self.assertEqual(next(p['value'] for p in row['parameters'] if p['slot']==7),index+1)
                self.assertEqual(public.sha(public.fixture(row)),row['input_sha256'])
                native,frame,_,close,_=public.native_render(parent,directory,row)
                self.assertEqual(public.sha(native),row['reference_raw_sha256']);self.assertFalse(frame['render_error']);self.assertTrue(frame['output']['guards_intact']);self.assertTrue(close['session_clean']);self.assertFalse(close['unsupported_suite_calls'])
                for binary in binaries.values():
                    for command in ['classic','smart']:
                        error,raw,metadata=public.mac_render(binary,directory,row,command,probe.ENV);expected=row['results'][command]
                        self.assertFalse(error);self.assertEqual(raw,native);self.assertEqual(public.sha(raw),expected['raw_sha256']);self.assertEqual(metadata,expected['metadata'])
        print('ZOOM_OUTER_FADE_NATIVE',100,'SDK_PUBLIC',400,flush=True)


if __name__=='__main__':unittest.main()
