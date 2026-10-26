"""Fail-closed release decisions; no emulation required."""
import importlib.util
import copy
import json
import tempfile
from unittest.mock import patch
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('gate',Path(__file__).resolve().parents[1]/'scripts/run_olm_release_gate_v2.py')
gate=importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)

class Decisions(unittest.TestCase):
    def test_mixed_corpus_configuration_and_retry(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            corpus = root/'tests/fuzz_corpus/mixed'; corpus.mkdir(parents=True)
            state = root/'state'; state.mkdir()
            saved = {'plugin':'colorkeep', 'max_size':32,
                     'result':{'oracle':{'status':'ok','raw_sha256':'ref'},
                               'routes':{'smart':{'status':'exact','raw_sha256':'ref'}}}}
            for index, config in enumerate(({}, {'max_size':1920, 'size_sampler':'odd-even-v1',
                    'size_max_height':1080, 'geometry_sampler':'realistic-v1', 'color_sampler':'default'})):
                (corpus/f'{index}.json').write_text(json.dumps(dict(saved, **config)))
            runner = object.__new__(gate.Gate); runner.state = state
            calls = []
            def fuzz(label, plugin, flags):
                options = dict(zip(flags[::2], flags[1::2])); calls.append(options)
                target = Path(options['--replay'])
                paths = sorted(target.glob('*.json')) if target.is_dir() else [target]
                rows = []
                for path in paths:
                    data = json.loads(path.read_text())
                    self.assertEqual(options['--max-size'], str(data['max_size']))
                    retry = '--case-timeout' in options
                    result = copy.deepcopy(data['result'])
                    if not retry:
                        result['oracle'] = {'status':'budget'}
                    rows.append({'path':str(path), 'matches_saved':retry, 'result':result})
                return 0, {'status':'replay_complete', 'replays':rows}
            runner.fuzz = fuzz
            with patch.object(gate, 'ROOT', root):
                details, passed = runner.replays()
            self.assertTrue(passed)
            self.assertEqual(details['counts']['PASS'], 2)
            self.assertEqual(len(calls), 4)
            for call in calls[2:]:
                self.assertEqual(call['--geometry'], 'realistic')
                self.assertEqual(call['--size-sampler'], 'odd-even-v1')
                self.assertEqual(call['--size-max-height'], '1080')
            verdicts = json.loads((state/'replay-verdicts.json').read_text())
            self.assertEqual({row['path'] for row in verdicts},
                             {'tests/fuzz_corpus/mixed/0.json', 'tests/fuzz_corpus/mixed/1.json'})

    def test_persistent_stop_requires_saved_original_hash(self):
        saved={'oracle':{'status':'ok','raw_sha256':'reference'},'routes':{'smart':{'status':'exact','raw_sha256':'reference'}}}
        now={'oracle':{'status':'reject','diagnostic':'guest UC_ERR_READ_UNMAPPED'},'routes':{'smart':{'status':'uncompared','raw_sha256':'reference'}}}
        self.assertTrue(gate.persistent_stop_matches(now,saved))
        now['routes']['smart']['raw_sha256']='changed'
        self.assertFalse(gate.persistent_stop_matches(now,saved))
        now['routes']['smart']['raw_sha256']='reference'
        now['oracle']['status']='harness_error'
        self.assertFalse(gate.persistent_stop_matches(now,saved))

    def test_stop_exception_preserves_other_route_results(self):
        saved={'oracles':{'smart':{'status':'ok','raw_sha256':'ref'},
                          'classic':{'status':'ok','raw_sha256':'classic'}},
               'routes':{'smart':{'status':'exact','raw_sha256':'ref'},
                         'classic':{'status':'refusal','error':-1}}}
        now=copy.deepcopy(saved)
        now['oracles']['smart']={'status':'budget'}
        now['routes']['smart']['status']='uncompared'
        self.assertTrue(gate.persistent_stop_matches(now,saved))
        now['routes']['classic']['error']=-2
        self.assertFalse(gate.persistent_stop_matches(now,saved))

    def test_saved_candidate_hash_cannot_replace_missing_reference(self):
        saved={'oracle':{'status':'reject'},'routes':{'smart':{'raw_sha256':'mac'}}}
        now={'oracle':{'status':'budget'},'routes':{'smart':{'status':'uncompared','raw_sha256':'mac'}}}
        self.assertFalse(gate.persistent_stop_matches(now,saved))

    def test_unknown_or_missing_routes_never_pass(self):
        self.assertFalse(gate.persistent_stop_matches({'routes':{}},{'routes':{'smart':{}}}))
        self.assertFalse(gate.campaign_counts({},'olmblur',300)[1])

    def test_counts_and_completion_are_both_required(self):
        report={'status':'complete','completed':1,'cases':[{'result':{'routes':{'smart':{'status':'mismatch'},'classic':{'status':'exact'}}}}]}
        counts,passed=gate.campaign_counts(report,'olmblur',1)
        self.assertEqual(counts['M'],1);self.assertFalse(passed)
        report['cases'][0]['result']['routes']['smart']['status']='exact'
        self.assertTrue(gate.campaign_counts(report,'olmblur',1)[1])
        self.assertFalse(gate.campaign_counts(report,'olmblur',2)[1])
        report['cases'][0]['result']['routes']['smart']['status']='refusal'
        self.assertEqual(gate.campaign_counts(report,'olmblur',1)[0]['R'],1)

if __name__=='__main__': unittest.main()
