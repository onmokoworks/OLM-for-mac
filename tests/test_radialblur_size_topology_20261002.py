"""Original component factors and public Size topology admission/output."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
probe=importlib.import_module('probe_radialblur_size_topology_20261002')
current=importlib.import_module('radialblur_current_public_20261001')
public=probe.public


class SizeTopologyTests(unittest.TestCase):
    def test_current_matrix_retained_cases_and_independent_sizes(self):
        report=json.loads((ROOT/'reports/radialblur_size_topology_public_20261002.json').read_text());live=current.capture();before=json.loads(probe.BEFORE.read_text())
        self.assertEqual(public.sha(probe.candidate_source(probe.before_source()).encode()),report['source_sha256'])
        self.assertEqual(report['summary'],{'case_count':694,'both_commands_exact':694,'different':0,'mac_rejected':0,'became_exact':84,'lost_exact':0,'raw_changed':84})
        self.assertEqual(report['summary'],probe.writer.summarize(report['rows']))
        self.assertEqual(report['independent_summary'],{'case_count':180,'both_commands_exact':180})
        generated=probe.independent_cases();self.assertEqual(generated,[{k:r[k] for k in generated[0]} for r in report['independent_rows']])
        for path,expected in report['dependencies_sha256'].items():self.assertEqual(public.sha((ROOT/path).read_bytes()),expected,path)
        parent=Path(os.environ['RADIAL_PARENT_WORKER']);self.assertEqual(public.sha(parent.read_bytes()),report['controlled_worker_sha256'])
        retained=before['independent_rows']+[r for path in probe.RETAINED for r in json.loads(path.read_text())['rows']]
        self.assertEqual(len(retained),395);replays=native_count=0
        with tempfile.TemporaryDirectory(prefix='radial_size_topology_production_') as name:
            directory=Path(name)
            for row,old in zip(report['rows'],before['rows']):
                for key in ['family','parameters','geometry','depth','pattern','state','group','matrix','row_index','input_sha256','reference_raw_sha256']:self.assertEqual(row[key],old[key])
                for command in ['classic','smart']:
                    self.assertEqual(row['results'][command]['metadata'],old['results'][command]['metadata'])
                    if old['results'][command]['raw_exact']:self.assertEqual(row['results'][command]['raw_sha256'],old['results'][command]['raw_sha256'])
            fresh=[row for row,old in zip(report['rows'],before['rows']) if old['results']['classic']['error']]+report['independent_rows']
            for row in fresh:
                raw,frame,_,close,_=public.native_render(parent,directory,row);self.assertEqual(public.sha(raw),row['reference_raw_sha256']);self.assertFalse(frame['render_error']);self.assertTrue(frame['output']['guards_intact']);self.assertTrue(close['session_clean']);self.assertFalse(close['unsupported_suite_calls']);native_count+=1
            for sanitize in [False,True]:
                binary=public.build(directory/('san' if sanitize else 'o2'),public.SOURCE.read_text(),sanitize)
                for row in live['rows']+retained+report['independent_rows']:
                    for command in ['classic','smart']:
                        error,raw,metadata=public.mac_render(binary,directory,row,command,probe.ENV);expected=row['results'][command]
                        self.assertEqual(error,expected['error']);self.assertEqual(public.sha(raw),expected['raw_sha256']);self.assertEqual(metadata,expected['metadata']);replays+=1
        self.assertEqual(native_count,264);self.assertEqual(replays,5076)
        print('SIZE_TOPOLOGY_PUBLIC',replays,'NATIVE',native_count,flush=True)

    def test_original_natural_owned_fields(self):
        report=json.loads((ROOT/'reports/radialblur_size_topology_public_20261002.json').read_text());live=current.capture();worker=Path(os.environ['RADIAL_WINDOWS_WORKER']);self.assertEqual(public.sha(worker.read_bytes()),report['window_worker_sha256'])
        with tempfile.TemporaryDirectory(prefix='radial_size_topology_planes_') as name:
            results=probe.natural(worker,Path(name),[r['case'] for r in report['natural_witnesses']],public.SOURCE.read_text())
            self.assertEqual(len(results),6)
            for actual,saved in zip(results,report['natural_witnesses']):
                for key in ['case','mac_dimensions','field_comparisons','mac_raw_sha256','all_owned_fields_and_raw_exact']:self.assertEqual(actual[key],saved[key])
        print('SIZE_TOPOLOGY_OWNED_WORDS',report['natural_owned_field_words'],flush=True)

    def test_original_pf32_common_caller_and_production_trait(self):
        leaf=importlib.import_module('probe_radialblur_zoom_float_writer_20261002')
        report=json.loads((ROOT/'reports/radialblur_zoom_float_writer_20261002.json').read_text())
        self.assertEqual(report['source_sha256'],json.loads((ROOT/'reports/radialblur_size_topology_public_20261002.json').read_text())['source_sha256'])
        current.capture()
        self.assertEqual(report['header_sha256'],public.sha(public.SOURCE.with_suffix('.h').read_bytes()))
        self.assertEqual(report['aex_sha256'],public.sha(public.initial.AEX.read_bytes()))
        for path,expected in report['dependencies_sha256'].items():
            self.assertEqual(public.sha((ROOT/path).read_bytes()),expected,path)
        import pefile
        pe=pefile.PE(str(public.initial.AEX))
        self.assertEqual(public.sha(pe.get_data(0x83ed,0x3c)),report['native_code_sha256'])
        self.assertEqual(leaf.native_rows(),report['rows'])
        with tempfile.TemporaryDirectory(prefix='radial_zoom_float_writer_production_') as name:
            count=leaf.sdk_replay(Path(name),public.SOURCE.read_text(),report['rows'])
        self.assertEqual(report['summary'],{'native_caller_block_cases':18,'sdk_trait_replays':36})
        self.assertEqual(count,36)
        print('ZOOM_FLOAT_WRITER_NATIVE',18,'SDK',count,flush=True)


if __name__=='__main__':unittest.main()
