#!/usr/bin/env python3
"""Audit the committed C54 measured evidence, without claiming native AE proof."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'orchestra/reports/C54-evidence'

def read(name):
    return json.loads(gzip.decompress((E/(name+'.json.gz')).read_bytes()))

def main():
    manifest=json.loads((E/'manifest.json').read_text())
    for name,digest in manifest.items():
        assert hashlib.sha256((E/name).read_bytes()).hexdigest()==digest,name
    summary={}
    for seed in (1,105):
        base=read(f'seed{seed}')
        assert base['completed']==300
        for prefix in ('box-','area-','final-'):
            if not (E/f'{prefix}seed{seed}.json.gz').exists():continue
            after=read(f'{prefix}seed{seed}');assert after['completed']==300
            for b,a in zip(base['cases'],after['cases']):
                assert b['index']==a['index'] and b['input_sha256']==a['input_sha256']
                br=b['result']['routes']['smart'];ar=a['result']['routes']['smart']
                if br['status']=='exact':assert ar['status']=='exact' and br['raw_sha256']==ar['raw_sha256']
            counts=Counter(r['result']['routes']['smart']['status'] for r in after['cases'])
            assert counts['mismatch']==0
            summary[f'{prefix}seed{seed}']=dict(counts)
    leaf=read('leaf')
    assert all(b['output']=='cases=432 certified=248 fallback=184 differing=0' for b in leaf['builds'])
    target=read('target')['rows'][0]
    assert target['exact'] and target['before_equal'] and target['sanitized_equal']
    assert target['seconds']<10 and target['before_seconds']>10
    for name in ('box-final','area-matrix','area-boundaries','bilateral-matrix','bilateral-extreme'):
        if not (E/(name+'.json.gz')).exists():continue
        d=read(name);assert d['completed']
        assert all(r['exact'] and r['sanitized_equal'] for r in d['rows'])
        summary[name]=len(d['rows'])
    for name in ('box-verify','area-verify','bilateral-verify'):
        if not (E/(name+'.json.gz')).exists():continue
        d=read(name);assert d['completed']
        rows=[r for campaign in d['campaigns'] for r in campaign['rows']]+d['corpus']
        assert all(r['sanitized_equal'] for r in rows)
        assert all(not r['before_exact'] or (r['after_exact'] and r['before_sha256']==r['after_sha256']) for r in rows)
        assert all(not r['changed'] or r['after_exact'] for r in rows)
        assert len(d['corpus'])==147
        summary[name]=len(rows)
    if (E/'trace16-after.json.gz').exists():
        before=read('trace16-before')['rows'][0];after=read('trace16-after')['rows'][0]
        assert before['pre_diff']['different_words']==0 and before['post_diff']['different_words']==110
        assert before['output_diff']['different_words']==32
        assert all(after[k]['different_words']==0 for k in ('pre_diff','post_diff','output_diff'))
    if (E/'corpus-final.json.gz').exists():
        d=read('corpus-final');assert d['completed']==147 and d['replay_matches_saved']
    print(json.dumps(dict(manifest_files=len(manifest),checks=summary,acceptance_met=True),sort_keys=True))

if __name__=='__main__':main()
