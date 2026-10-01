"""Reexecute legal Size, composition, original factor maps and open expf evidence."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/emulation'))
probe=importlib.import_module('probe_radialblur_size_range_20261002')
current=importlib.import_module('radialblur_current_public_20261001')
public=probe.public


class SizeRangeTests(unittest.TestCase):
    def test_actual_public_matrix_and_legal_size_compositions(self):
        report=json.loads((ROOT/'reports/radialblur_size_range_public_20261002.json').read_text());live=current.capture();before=json.loads(probe.BEFORE.read_text())
        self.assertEqual(public.sha(probe.candidate_source(probe.before_source()).encode()),report['source_sha256'])
        self.assertEqual(live['summary'],report['summary'])
        self.assertEqual(report['summary'],{'case_count':694,'both_commands_exact':694,'different':0,'mac_rejected':0,'became_exact':0,'lost_exact':0,'raw_changed':0})
        self.assertEqual(report['summary'],probe.topology.writer.summarize(report['rows']))
        self.assertEqual(report['independent_summary'],{'case_count':560,'both_commands_exact':560,'before_rejected':542,'before_exact':18})
        generated=probe.independent_cases()
        self.assertEqual(generated,[{k:r[k] for k in generated[0]} for r in report['independent_rows']])
        for path,expected in report['dependencies_sha256'].items():
            self.assertEqual(current.historical_dependency_sha256(path),expected,path)
        parent=Path(os.environ['RADIAL_PARENT_WORKER'])
        self.assertEqual(public.sha(parent.read_bytes()),report['controlled_worker_sha256'])
        retained=probe.retained_cases(before);self.assertEqual(len(retained),575)
        native_count=replays=0
        with tempfile.TemporaryDirectory(prefix='radial_size_range_production_') as name:
            directory=Path(name)
            for row,old in zip(report['rows'],before['rows']):
                for key in ['family','parameters','geometry','depth','pattern','state','group','matrix','row_index','input_sha256','reference_raw_sha256']:
                    self.assertEqual(row[key],old[key])
                for command in ['classic','smart']:
                    self.assertEqual(row['results'][command]['raw_sha256'],old['results'][command]['raw_sha256'])
                    self.assertEqual(row['results'][command]['metadata'],old['results'][command]['metadata'])
            for row in report['independent_rows']:
                raw,frame,_,close,_=public.native_render(parent,directory,row)
                self.assertEqual(public.sha(raw),row['reference_raw_sha256'])
                self.assertFalse(frame['render_error']);self.assertTrue(frame['output']['guards_intact'])
                self.assertTrue(close['session_clean']);self.assertFalse(close['unsupported_suite_calls']);native_count+=1
            for sanitize in [False,True]:
                binary=public.build(directory/('san' if sanitize else 'o2'),public.SOURCE.read_text(),sanitize)
                for row in live['rows']+retained+report['independent_rows']:
                    for command in ['classic','smart']:
                        error,raw,metadata=public.mac_render(binary,directory,row,command,probe.ENV)
                        expected=row['results'][command]
                        self.assertEqual(error,expected['error']);self.assertEqual(public.sha(raw),expected['raw_sha256']);self.assertEqual(metadata,expected['metadata']);replays+=1
        self.assertEqual(native_count,560);self.assertEqual(replays,7316)
        print('SIZE_RANGE_PRODUCTION',replays,'NATIVE',native_count,flush=True)

    def test_original_fade_fields_and_isolated_reference_policy(self):
        report=json.loads((ROOT/'reports/radialblur_size_range_public_20261002.json').read_text());current.capture();worker=Path(os.environ['RADIAL_WINDOWS_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()),report['window_worker_sha256'])
        candidate=public.SOURCE.read_text()
        start=candidate.index('static PF_Err RenderZoomTyped(');end=candidate.index('static PF_Err RenderZoom8(',start)
        marker='\tconst bool use_generic_size_fade = use_generic_baseline && RadialSizeVariationEnabled(info.size_variation) &&\n\t\t(info.outer_edge_fade != 0 || info.inner_edge_fade != 0);'
        part=candidate[start:end];self.assertEqual(part.count(marker),1)
        disconnected=candidate[:start]+part.replace(marker,'\tconst bool use_generic_size_fade = false;')+candidate[end:]
        with tempfile.TemporaryDirectory(prefix='radial_size_range_natural_') as name:
            directory=Path(name)
            results=probe.zoom_natural(worker,directory,report['independent_rows'],disconnected,candidate)
            self.assertEqual(len(results),4)
            for actual,saved in zip(results,report['zoom_natural_witnesses']):
                for key in ['case','field_comparisons','mac_raw_sha256','candidate_all_fields_exact','gaussian_tail_reference_difference','private_host_exp_is_diagnostic_only']:
                    self.assertEqual(actual[key],saved[key])
            self.assertEqual(sum(r['candidate_all_fields_exact'] for r in results),3)
            self.assertEqual(results[-1]['field_comparisons']['candidate']['normalized']['different_words'],27)
            compound=probe.topology.natural(worker,directory,[r['case'] for r in report['compound_natural_witnesses']],candidate)
            for actual,saved in zip(compound,report['compound_natural_witnesses']):
                for key in ['case','mac_dimensions','field_comparisons','mac_raw_sha256','all_owned_fields_and_raw_exact']:
                    self.assertEqual(actual[key],saved[key])
        print('SIZE_RANGE_NATURAL',6,'KNOWN_REFERENCE_TAIL_WORDS',1,'PRODUCTION_NORMALIZED_WORDS_OPEN',27,flush=True)

    def test_original_fractional_component_factors(self):
        report=json.loads((ROOT/'reports/radialblur_size_range_public_20261002.json').read_text());current.capture();worker=Path(os.environ['RADIAL_WINDOWS_WORKER'])
        self.assertEqual(public.sha(worker.read_bytes()),report['window_worker_sha256'])
        with tempfile.TemporaryDirectory(prefix='radial_size_range_factors_') as name:
            actual=probe.factor_maps(worker,Path(name),public.SOURCE.read_text())
            for row,saved in zip(actual,report['factor_map_witnesses']):
                for key in ['case','maximum_area','component_areas','area_sha256','factor_sha256','word_count','typed_sdk_replays']:
                    self.assertEqual(row[key],saved[key])
                self.assertTrue(row['trace']['guards_intact'])
                self.assertEqual(row['trace']['mask_guard_byte'],0)
                self.assertEqual(row['trace']['witness_count'],4)
        self.assertEqual(len(actual),12)
        self.assertEqual(sum(r['typed_sdk_replays'] for r in actual),72)
        print('SIZE_RANGE_ORIGINAL_FACTOR_MAPS',12,'SDK',72,flush=True)


if __name__=='__main__':unittest.main()
