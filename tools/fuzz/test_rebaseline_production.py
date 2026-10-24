"""Production rebaseline guards, atomic preflight, provenance and history."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import rebaseline_corpus

class ProductionRebaseline(unittest.TestCase):
    def test_policy_and_history(self):
        scratch=Path(os.environ.get('OLM_FUZZ_TEST_SCRATCH', 'orchestra/state/F23-corpus-rebaseline-all')).resolve()
        scratch.mkdir(parents=True,exist_ok=True)
        for before, after, changed_hash, allowed in [
            ('mismatch','exact',True,True), ('mismatch','mismatch',True,True),
            ('refusal','exact',True,True), ('exact','exact',False,True),
            ('mismatch','refusal',True,True), ('refusal','refusal',False,True),
            ('refusal','refusal',True,False),
            ('exact','refusal',True,False), ('exact','mismatch',True,False),
            ('exact','exact',True,False),
            ('refusal','mismatch',True,False)]:
            with self.subTest(before=before,after=after), tempfile.TemporaryDirectory(dir=scratch) as td:
                root=Path(td); paths=[root/'a.json',root/'b.json']
                old={'oracle':{'status':'ok'},'routes':{'smart':{'status':before,'raw_sha256':'old'}}}
                new=copy.deepcopy(old)
                new['routes']['smart'].update(status=after,raw_sha256='new' if changed_hash else 'old',metadata='updated')
                initial={'plugin':'synthetic','result':old,'provenance':{'old':True},'rebaseline_history':[{'ticket':'previous'}]}
                for p in paths: p.write_text(json.dumps(initial))
                # First file is always safe: a rejected second file must prevent both writes.
                safe=copy.deepcopy(old);safe['routes']['smart']['status']='exact'
                report={'plugin':'synthetic','status':'replay_complete','requested':2,'completed':2,'provenance':None,
                        'replay_groups':[{'paths':[str(p) for p in paths],'provenance':{'worker':'group'}}],
                        'replays':[{'path':str(paths[0]),'result':safe,'group':0},{'path':str(paths[1]),'result':new,'group':0}]}
                rp=root/'report.json';rp.write_text(json.dumps(report))
                argv=['rebaseline','--plugin','synthetic','--corpus',str(root),'--report',str(rp),'--production-rebaseline','F23']
                with patch.object(sys,'argv',argv), contextlib.redirect_stdout(io.StringIO()):
                    if allowed: self.assertEqual(rebaseline_corpus.main(),0)
                    else:
                        with self.assertRaises(SystemExit):rebaseline_corpus.main()
                if allowed:
                    result=json.loads(paths[1].read_text())
                    self.assertEqual(result['result'],new)
                    self.assertEqual(result['provenance'],{'worker':'group'})
                    self.assertEqual(result['rebaseline_history'][-1]['previous_result'],old)
                    self.assertEqual(result['rebaseline_history'][-1]['previous_provenance'],{'old':True})
                    self.assertEqual(result['rebaseline_history'][0],{'ticket':'previous'})
                else:
                    for p in paths:self.assertEqual(json.loads(p.read_text()),initial)

    def test_oracle_and_route_drift(self):
        scratch = Path(os.environ.get('OLM_FUZZ_TEST_SCRATCH', 'orchestra/state/F23-corpus-rebaseline-all')).resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        for drift in ('oracle', 'route_oracle', 'route_set', 'duplicate'):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory(dir=scratch) as td:
                root = Path(td)
                path = root / 'case.json'
                old = {'oracle': {'status': 'ok', 'raw_sha256': 'oracle'},
                       'oracles': {'smart': {'status': 'ok', 'raw_sha256': 'oracle'}},
                       'routes': {'smart': {'status': 'mismatch', 'raw_sha256': 'old'}}}
                initial = {'plugin': 'synthetic', 'result': old, 'provenance': {}}
                path.write_text(json.dumps(initial))
                observed = copy.deepcopy(old)
                if drift == 'oracle': observed['oracle']['raw_sha256'] = 'changed'
                if drift == 'route_oracle': observed['oracles']['smart']['raw_sha256'] = 'changed'
                if drift == 'route_set': observed['routes']['classic'] = observed['routes']['smart']
                rows = [{'path': str(path), 'result': observed}]
                if drift == 'duplicate': rows *= 2
                report = {'plugin': 'synthetic', 'status': 'replay_complete',
                          'requested': len(rows), 'completed': len(rows),
                          'provenance': {}, 'replays': rows}
                rp = root / 'report.json'
                rp.write_text(json.dumps(report))
                argv = ['rebaseline', '--plugin', 'synthetic', '--corpus', str(root),
                        '--report', str(rp), '--production-rebaseline', 'F23']
                with patch.object(sys, 'argv', argv), self.assertRaises(SystemExit):
                    rebaseline_corpus.main()
                self.assertEqual(json.loads(path.read_text()), initial)

if __name__=='__main__':unittest.main()
