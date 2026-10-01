"""Zoom fade uses the actual B680 vector/scalar table rule and worker pipeline."""
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


class ZoomFadeTests(unittest.TestCase):
    def test_current_matrix_and_independent_all_inner_fade_lengths(self):
        report=current.capture();before=json.loads(probe.BEFORE.read_text());extra=json.loads(probe.EXTRA.read_text())
        self.assertEqual(public.SOURCE.read_text(),probe.candidate_source(probe.before_source()))
        self.assertEqual(report['summary'],{'case_count':694,'both_commands_exact':610,'different':0,'mac_rejected':84,'became_exact':3,'lost_exact':0,'raw_changed':3})
        self.assertEqual(report['summary'],probe.writer.summarize(report['rows']))
        generated=probe.independent_cases();self.assertEqual(generated,[{key:r[key] for key in generated[0]} for r in report['independent_rows']])
        self.assertEqual(report['independent_summary'],probe.writer.summarize(report['independent_rows']))
        self.assertEqual(report['independent_summary'],{'case_count':199,'both_commands_exact':199,'different':0,'mac_rejected':0,'became_exact':147,'lost_exact':0,'raw_changed':147})
        for path,expected in report['dependencies_sha256'].items():self.assertEqual(public.sha((ROOT/path).read_bytes()),expected,path)
        parent=Path(os.environ['RADIAL_PARENT_WORKER']);self.assertEqual(public.sha(parent.read_bytes()),report['controlled_worker_sha256'])
        native_count=replays=0
        with tempfile.TemporaryDirectory(prefix='radial_zoom_fade_production_') as name:
            directory=Path(name)
            for row in report['independent_rows']:
                raw,frame,_,close,_=public.native_render(parent,directory,row)
                self.assertEqual(public.sha(raw),row['reference_raw_sha256']);self.assertFalse(frame['render_error']);self.assertTrue(frame['output']['guards_intact']);self.assertTrue(close['session_clean']);self.assertFalse(close['unsupported_suite_calls']);native_count+=1
            for row,old in zip(report['rows'],before['rows']):
                for key in ['family','parameters','geometry','depth','pattern','state','group','matrix','row_index','input_sha256','reference_raw_sha256']:self.assertEqual(row[key],old[key])
                for command in ['classic','smart']:
                    if old['results'][command]['raw_exact']:self.assertEqual(row['results'][command]['raw_sha256'],old['results'][command]['raw_sha256'])
                if row['results']['classic']['raw_exact'] and not old['results']['classic']['raw_exact']:
                    raw,frame,_,close,_=public.native_render(parent,directory,row);self.assertEqual(public.sha(raw),row['reference_raw_sha256']);self.assertFalse(frame['render_error']);self.assertTrue(frame['output']['guards_intact']);self.assertTrue(close['session_clean']);self.assertFalse(close['unsupported_suite_calls']);native_count+=1
            for sanitize in [False,True]:
                binary=public.build(directory/('san' if sanitize else 'o2'),public.SOURCE.read_text(),sanitize)
                for row in report['rows']+extra['rows']+report['independent_rows']:
                    for command in ['classic','smart']:
                        error,raw,metadata=public.mac_render(binary,directory,row,command,probe.ENV);expected=row['results'][command]
                        self.assertEqual(error,expected['error']);self.assertEqual(public.sha(raw) if not error else None,expected['raw_sha256']);self.assertEqual(metadata,expected['metadata']);replays+=1
        self.assertEqual(native_count,202);self.assertEqual(replays,3956)
        print('ZOOM_FADE_PRODUCTION_REPLAYS',replays,'NATIVE',native_count,flush=True)

    def test_natural_prepass_scatter_and_normalized_fields(self):
        report=current.capture();worker=Path(os.environ['RADIAL_WINDOWS_WORKER']);self.assertEqual(public.sha(worker.read_bytes()),report['window_worker_sha256'])
        with tempfile.TemporaryDirectory(prefix='radial_zoom_fade_planes_') as name:
            results=probe.natural(worker,Path(name),[r['case'] for r in report['natural_witnesses']],probe.before_source(),public.SOURCE.read_text())
            self.assertEqual(len(results),3)
            for observed,saved in zip(results,report['natural_witnesses']):
                for key in ['case','field_comparisons','gaussian_comparison','mac_raw_sha256','candidate_raw_exact']:self.assertEqual(observed[key],saved[key])
                self.assertTrue(observed['candidate_raw_exact'])
                for field in ['polar','span','eligible']:self.assertEqual(observed['field_comparisons']['before'][field]['native_sha256'],observed['field_comparisons']['before'][field]['mac_sha256'])
                self.assertEqual(observed['gaussian_comparison']['different_words'],0)
        print('ZOOM_FADE_NATURAL',3,'WORDS',report['natural_field_words'],flush=True)


if __name__=='__main__':unittest.main()
