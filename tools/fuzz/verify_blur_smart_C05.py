#!/usr/bin/env python3
"""Validate C05 monotonic campaigns, paired contexts, retained controls and corpus.

--rebaseline changes only corpus records proven mismatch -> exact; the previous
complete result is retained. No partial improvements are rebaselined.
"""
import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import tempfile
import time
from adapters.olmblur import Adapter, HOST, SOURCE, CORES
from core import command, sha
from run import ROOT, main_checkout

WORKER=Path.home()/'.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker'
BASE='ad206f003a9908e1c7a77bdda1de665d543dd996'


def load(path):return json.loads(path.read_text())


def retained(scratch):
    class Sanitized(Adapter):
        def compile(self,argv,deadline):
            if argv[0]=='clang++':argv=[argv[0],'-fsanitize=address,undefined','-fno-sanitize-recover=all',*argv[1:]]
            return super().compile(argv,deadline)
    a=Sanitized(argparse.Namespace(max_size=256,case_timeout=20,main=main_checkout(),worker=WORKER))
    a.env.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),
                 ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    body=HOST.read_text().replace('../../mac/OLMBlur/OLMBlur.cpp',str(SOURCE))
    body=body.split('  const NegSpec negatives[]={',1)[0]+'  return ok ? 0 : 4;\n}\n'
    fixture=ROOT/'tools/emulation/fixtures/olmblur_amount_repeat_legacy_matrix_20260810'
    with tempfile.TemporaryDirectory(dir=scratch) as td:
        binary=a.compile_sdk(Path(td),body,SOURCE,time.monotonic()+120,CORES)
        status,out,err=command([binary,fixture],timeout=60,deadline=time.monotonic()+60,env=a.env)
        report={'source_sha256':sha(SOURCE.read_bytes()),'candidate_sha256':sha(binary.read_bytes()),
                'original_host_sha256':sha(HOST.read_bytes()),'fixture_manifest_sha256':sha((fixture/'manifest.json').read_bytes()),
                'status':status,'lines':out.decode().splitlines(),'stderr':err.decode()}
    assert status['status']=='ok' and len(report['lines'])==12 and all('pass=1' in line for line in report['lines']),report
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--rebaseline',action='store_true')
    args=p.parse_args();s=args.scratch.resolve()
    assert s.is_relative_to(ROOT/'orchestra/state/C05-olmblur-smart')
    os.environ.update(TMPDIR=str(s),TMP=str(s),TEMP=str(s))
    report={'schema':'olmblur-smart-C05/1','base':BASE,'source_sha256':sha(SOURCE.read_bytes()),'seeds':{}}
    for seed in (1,3):
        paths={k:s/f'{v}-seed{seed}{suffix}.json' for k,v,suffix in
               [('before','before',''),('after','smooth',''),('sanitized','smooth','-sanitized'),
                ('gateoff_before','gateoff',''),('gateoff_after','smooth-gateoff','')]}
        data={k:load(v) for k,v in paths.items()}
        assert all(d['completed']==300 and d['jobs']==2 and d['seed']==seed for d in data.values())
        for label in ('after','sanitized'):
            assert data[label]['provenance']['dependencies_sha256']['mac/OLMBlur/OLMBlur.cpp']==report['source_sha256']
        changes=[];transitions=Counter();preserved=0
        for b,a,z in zip(*(data[k]['cases'] for k in ('before','after','sanitized'))):
            assert b['input_sha256']==a['input_sha256']==z['input_sha256']
            assert b['result']['oracles']==a['result']['oracles']==z['result']['oracles']
            assert a['result']['routes']==z['result']['routes'],(seed,a['index'],'sanitizer drift')
            assert b['result']['routes']['classic']==a['result']['routes']['classic']
            br=b['result']['routes']['smart'];ar=a['result']['routes']['smart']
            assert ar['status'] in ('exact','mismatch','refusal')
            transitions[br['status']+' -> '+ar['status']]+=1
            if br['status']=='exact':assert br==ar;preserved+=1
            if br!=ar:
                assert br['status']=='mismatch'
                if ar['status']=='mismatch':
                    assert all(ar['diff'][k]<br['diff'][k] for k in ('different_words','different_bytes'))
                else:assert ar['status']=='exact'
                changes.append({k:a[k] for k in ('index','geometry','depth','parameters','input_sha256')}|
                               {'before':br,'after':ar,'oracle':a['result']['oracles']['smart']})
        report['seeds'][str(seed)]={'counts':{k:d['summary'] for k,d in data.items()},
            'provenance':{k:d['provenance'] for k,d in data.items()},
            'report_sha256':{k:sha(v.read_bytes()) for k,v in paths.items()},
            'transitions':dict(transitions),'base_exact_preserved':preserved,'sanitized_routes':600,
            'sanitizer_errors':0,'changed_cases':changes}
    before=load(s/'before-replay.json');after=load(s/'smooth-replay.json')
    assert before['completed']==after['completed']==39
    corpus=[];transitions=Counter();clusters=defaultdict(list);updates=[]
    for b,a in zip(before['replays'],after['replays']):
        assert b['path']==a['path'];path=Path(a['path']).resolve();saved=load(path)
        assert path.resolve().is_relative_to(ROOT/'tests/fuzz_corpus/olmblur')
        historical=saved.get('C05_smart_update',{}).get('previous_result',saved['result'])
        assert historical==b['result'],path
        for route in ('classic','smart'):
            br=b['result']['routes'][route];ar=a['result']['routes'][route]
            transitions[route+': '+br['status']+' -> '+ar['status']]+=1
            if br!=ar:assert route=='smart' and br['status']=='mismatch' and ar['status']=='exact'
        assert b['result']['oracles']==a['result']['oracles']
        params=saved['case']['parameters'];defaults={1:5.,2:100.,3:2,4:1,5:0}
        signature=json.dumps([[p['slot'] for p in params if p['value']!=defaults[p['slot']]],saved['case']['depth']])
        clusters[signature].append((b['result']['routes']['smart']['status'],a['result']['routes']['smart']['status']))
        corpus.append({'path':str(path.relative_to(ROOT)),'cluster':signature,
                       'input_sha256':saved['input_sha256'],'before':b['result'],'after':a['result']})
        if b['result']!=a['result'] and saved['result']!=a['result']:
            assert saved['result']==b['result']
            saved['C05_smart_update']={'report':'orchestra/reports/C05-olmblur-smart.md','previous_result':saved['result']}
            saved['result']=a['result'];saved['provenance']=after['provenance'];updates.append((path,saved))
    closed={k:len(v) for k,v in clusters.items() if all(x=='mismatch' and y=='exact' for x,y in v)}
    assert len(closed)>=3,closed
    report['corpus']={'transitions':dict(transitions),'closed_clusters':closed,'cases':corpus}
    for name in ('context-before','context-smooth','context-boundaries'):
        report[name]=load(s/f'{name}.json')
    for b,a in zip(report['context-before']['rows'],report['context-smooth']['rows']):
        assert b['first_stage']=='worker_context' and a['first_stage'] is None
        assert a['original_context']['bits']==a['mac_context']['bits']
        assert a['original_public_trace']['active_sha256']==b['original_public_trace']['active_sha256']
    boundaries=report['context-boundaries']['rows']
    assert len(boundaries)==30 and all(r['first_stage'] is None and r['output_exact'] for r in boundaries)
    report['retained_controls']=retained(s)
    if (s/'final-replay.json').exists():
        final=load(s/'final-replay.json')
        assert final['completed']==39 and final['replay_matches_saved']
        assert [r['result'] for r in final['replays']]==[r['result'] for r in after['replays']]
        report['final_sanitized_replay']={'completed':39,'matches_saved':True,
                                         'provenance':final['provenance']}
    if args.rebaseline:
        for path,data in updates:path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    report['tool_sha256']={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in
        (Path(__file__),ROOT/'tools/fuzz/blur_admission_campaign_C05.py',ROOT/'tools/emulation/trace_olmblur_smart_C05.py')}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PASS', {k:v['transitions'] for k,v in report['seeds'].items()},
          'corpus',dict(transitions),'closed',closed,'12 retained controls; 30 context boundaries; 1200 sanitized routes')


if __name__=='__main__':main()
