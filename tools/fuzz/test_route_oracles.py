"""Route ownership regressions; no emulator/compiler required."""
import tempfile
import contextlib
import io
import json
import sys
from unittest.mock import patch
import time
import unittest
from pathlib import Path
from core import evaluate, mismatch_routes
from test_framework import Synthetic


class Split(Synthetic):
    oracle_routes = {'classic':'classic', 'smart':'smart'}
    original_routes = {'classic':'render', 'smart':'render'}

    def oracle(self, case, directory, deadline, route=None):
        return {'status':'ok'}, bytes([1 if route == 'classic' else 2])*len(case['pixels'])

    def candidate(self, case, directory, route, deadline):
        return self.oracle(case, directory, deadline, route)


class RouteOracles(unittest.TestCase):
    def run_case(self, adapter):
        # Synthetic methods perform no filesystem operations.
        return evaluate(adapter, adapter.generate(1, 0), Path('.'), time.monotonic()+5)

    def test_distinct_original_routes_are_both_exact(self):
        result = self.run_case(Split())
        self.assertEqual([r['status'] for r in result['routes'].values()], ['exact','exact'])
        self.assertNotEqual(result['oracles']['classic']['raw_sha256'],
                            result['oracles']['smart']['raw_sha256'])

    def test_rejected_classic_does_not_borrow_successful_smart(self):
        class Reject(Split):
            def oracle(self, case, directory, deadline, route=None):
                return ({'status':'reject'}, b'') if route == 'classic' else super().oracle(case,directory,deadline,route)
            def candidate(self, case, directory, route, deadline):
                return {'status':'ok'}, bytes([2])*len(case['pixels'])
        result = self.run_case(Reject())
        self.assertEqual(result['routes']['classic']['status'], 'uncompared')
        self.assertEqual(result['routes']['smart']['status'], 'exact')

    def test_no_write_has_a_separate_verdict_and_detects_writes(self):
        class NoWrite(Split):
            original_routes = {'classic':'no-write', 'smart':'render'}
            no_write_fill = 0xee
            def oracle(self, case, directory, deadline, route=None):
                return {'status':'ok'}, bytes([0 if route == 'classic' else 2])*len(case['pixels'])
            def candidate(self, case, directory, route, deadline):
                return {'status':'ok'}, bytes([self.no_write_fill if route == 'classic' else 2])*len(case['pixels'])
        adapter = NoWrite()
        result = self.run_case(adapter)
        self.assertEqual(result['routes']['classic']['status'], 'no_write')
        adapter.candidate = lambda c,d,r,t: ({'status':'ok'}, bytes(len(c['pixels'])))
        result = self.run_case(adapter)
        self.assertEqual(result['routes']['classic']['status'], 'no_write_violation')
        self.assertIn('classic', mismatch_routes(result))

    def test_no_write_reference_change_is_a_harness_error(self):
        class BadNoWrite(Split):
            original_routes = {'classic':'no-write', 'smart':'render'}
            no_write_fill = 0xee
        result = self.run_case(BadNoWrite())
        self.assertEqual(result['oracles']['classic']['status'], 'harness_error')
        self.assertEqual(result['routes']['classic']['status'], 'uncompared')

    def test_single_owner_remains_explicit_without_changing_legacy_results(self):
        class One(Split):
            oracle_routes = {'classic':'classic', 'smart':'classic'}
            def candidate(self,c,d,r,t):
                return self.oracle(c,d,t,'classic')
        result = self.run_case(One())
        self.assertEqual([v['status'] for v in result['routes'].values()], ['exact','exact'])
        self.assertNotIn('oracles', result)  # Existing v1 corpus remains replayable.


class RouteMigration(unittest.TestCase):
    def test_correction_preserves_previous_result_and_preflights_every_file(self):
        import rebaseline_corpus
        scratch=Path(__file__).resolve().parents[2]/'orchestra/state/F17-fuzz-per-route-oracle'
        scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as td:
            root=Path(td)
            old={'oracle':{'status':'ok','raw_sha256':'smart'},
                 'routes':{'classic':{'status':'exact','raw_sha256':'mac'},
                           'smart':{'status':'exact','raw_sha256':'smart'}}}
            new={'oracle':old['oracle'],'oracles':{'classic':{'status':'ok','raw_sha256':'classic'},
                 'smart':old['oracle']},'routes':{'classic':{'status':'mismatch','raw_sha256':'mac','diff':{}},
                                                'smart':old['routes']['smart']}}
            paths=[root/'a.json',root/'b.json']
            for path in paths:path.write_text(json.dumps({'plugin':'synthetic','result':old}))
            report={'plugin':'synthetic','status':'replay_complete','requested':2,'completed':2,
                    'provenance':{'oracle_routes':{'classic':'classic','smart':'smart'}},
                    'replays':[{'path':str(path),'result':json.loads(json.dumps(new))} for path in paths]}
            report['replays'][1]['result']['routes']['classic']['raw_sha256']='changed'
            rp=root/'report.json';rp.write_text(json.dumps(report))
            argv=['rebaseline_corpus','--plugin','synthetic','--corpus',str(root),'--report',str(rp),'--route-correction']
            with patch.object(sys,'argv',argv), self.assertRaises(SystemExit):
                rebaseline_corpus.main()
            self.assertEqual(json.loads(paths[0].read_text())['result'],old)
            report['replays'][1]['result']=new;rp.write_text(json.dumps(report))
            with patch.object(sys,'argv',argv), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(rebaseline_corpus.main(),0)
            updated=json.loads(paths[0].read_text())
            self.assertEqual(updated['result'],new)
            self.assertEqual(updated['route_oracle_update']['previous_result'],old)


if __name__ == '__main__':
    unittest.main()
