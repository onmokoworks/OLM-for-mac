#!/usr/bin/env python3
"""Validate retained C56 exactness, unchanged hashes, traces and timing evidence."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'orchestra/reports/C56-evidence'


def read(name):
    return json.loads(gzip.decompress((E/(name+'.json.gz')).read_bytes()))


def main():
    manifest=json.loads((E/'manifest.json').read_text())
    for name,digest in manifest.items():
        assert hashlib.sha256((E/name).read_bytes()).hexdigest()==digest,name
    summary={}
    expected_source=read('radius2-verify')['source_sha256']
    for name,n in [('matrix',108),('median-sdr',216),('radius2-wide',180),('radius2-extreme',180)]:
        d=read(name);assert d['completed'] and len(d['rows'])==n
        assert all(r['exact'] and r['sanitized_equal'] for r in d['rows']),name
        summary[name]=n
    for name,n in [('leaf',648),('median-leaf',324),('final-leaf',648),('final-median-leaf',324)]:
        d=read(name);assert len(d['builds'])==2
        assert all(b['output']==f'cases={n} differing=0' for b in d['builds']),name
    for name in ('target','median205','median296','median51'):
        r=read(name)['rows'][0]
        assert r['before_equal'] and r['sanitized_equal']
        assert r['seconds']<10<r['before_seconds'],name
        assert r['oracle']['status']!='ok' and not r['exact']
    for name,n in [('verify',744),('median-verify',1043),('radius2-verify',1043)]:
        d=read(name);assert d['completed']
        rows=[r for c in d['campaigns'] for r in c['rows']]+d['corpus']
        assert len(rows)==n and len(d['corpus'])==147
        assert all(r['sanitized_equal'] and not r['changed'] for r in rows),name
        assert all(not r['before_exact'] or r['after_exact'] for r in rows)
    negative=read('final-radius2-negative')
    assert negative['completed'] and len(negative['rows'])==8
    assert all(r['candidate']['status']=='refusal' and r['sanitized_equal'] for r in negative['rows'])
    admission=read('radius2-admission')
    assert admission['completed'] and len(admission['rows'])==360
    assert all(r['before']['status']=='refusal' and r['after']['status']=='ok' and
               r['after_sha256']==r['oracle_sha256'] and r['sanitized_equal'] for r in admission['rows'])
    for name,post,out in [('radius2-trace',11,20),('radius2-grouped-trace',1,2),('radius2-fixed-trace',0,0)]:
        r=read(name)['rows'][0]
        assert r['pre_diff']['different_words']==0
        assert r['post_diff']['different_words']==post and r['output_diff']['different_words']==out
    for name,count in [('radius2-grouped-loop',1),('radius2-fixed-leaf',0)]:
        d=read(name);assert d['dispatch']=={'0x1806bd9a0':1} and not d['original_imports']
        assert d['exp_count']==8201
        assert all(b['exp_diff']['different_words']==0 and b['post_diff']['different_words']==count and
                   b['loop_diff']['different_words']==count for b in d['builds'])
    for seed,exact,changed in [(1,290,[10]),(105,285,[205,296]),(156,284,[51])]:
        before=read(f'seed{seed}');after=read(f'final{seed}')
        assert before['completed']==after['completed']==300
        assert after['provenance']['dependencies_sha256']['mac/OLMDistanceGradation/OLMDistanceGradation.cpp']==expected_source
        different=[]
        for b,a in zip(before['cases'],after['cases']):
            assert b['index']==a['index'] and b['input_sha256']==a['input_sha256']
            assert all(b[k]==a[k] for k in ('geometry','depth','parameters','profile','input_padding','output_padding'))
            br=b['result']['routes']['smart'];ar=a['result']['routes']['smart']
            if br['status']=='exact':
                assert ar['status']=='exact' and br['raw_sha256']==ar['raw_sha256']
            if br!=ar:different.append(a['index'])
        assert different==changed,(seed,different)
        counts=Counter(r['result']['routes']['smart']['status'] for r in after['cases'])
        assert counts['exact']==exact and counts['mismatch']==counts['budget']==0
        assert all(r['result']['oracles']['smart']['status']!='ok' or
                   r['result']['routes']['smart']['status']=='exact' for r in after['cases'])
        summary[f'seed{seed}']=dict(counts)
    replay=read('corpus-final');assert replay['completed']==147 and replay['replay_matches_saved']
    print(json.dumps(dict(manifest_files=len(manifest),checks=summary,acceptance_met=True),sort_keys=True))


if __name__=='__main__':main()
