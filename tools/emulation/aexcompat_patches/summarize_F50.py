#!/usr/bin/env python3
"""Summarize recorded F50b observations without treating failures as equality."""
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
E=ROOT/'orchestra/reports/F50b-evidence'

def rows(name):
    p=E/name
    return [json.loads(line) for line in p.read_text().splitlines()] if p.exists() else []

def main():
    summary={}
    grouped=defaultdict(Counter)
    failures=[]
    timings=defaultdict(lambda: defaultdict(list))
    for r in rows('corpus.jsonl'):
        grouped[r['plugin']][r['comparison']]+=1
        for o in r['observations']:
            timings[r['plugin']][o['version']].append((o['elapsed_seconds'], r['key']))
        if r['comparison']!='identical':
            failures.append(dict(key=r['key'],comparison=r['comparison'],
                statuses=[o['result']['status'] for o in r['observations']],first_difference=r['first_difference']))
    summary['corpus_by_plugin']=dict(grouped)
    summary['corpus_nonidentical']=failures
    summary['corpus_timings']={plugin:{version:dict(
        total_seconds=sum(t for t,k in samples), max_seconds=max(samples)[0],
        max_case=max(samples)[1]) for version,samples in versions.items()}
        for plugin,versions in timings.items()}
    transitions=defaultdict(Counter)
    for r in rows('s01.jsonl'):
        old=r['original'];new=r['result']
        old=old.get('oracles',{}).get('smart',old['oracle'])
        oracle=new.get('oracles',{}).get('smart',new['oracle'])
        transitions[r['key'].split(':')[0]][old['status']+' -> '+oracle['status']]+=1
    summary['s01_transitions']=dict(transitions)
    summary['campaigns']={}
    for p in sorted(E.glob('*-seed1-*.json.gz')):
        d=json.loads(gzip.decompress(p.read_bytes()))
        summary['campaigns'][p.name]={k:v for k,v in d.items() if k in ('status','completed','counts','route_counts','summary','elapsed_seconds')}
    (E/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('corpus_nonidentical', 'corpus_timings')},indent=2))
    print('Corpus nonidentical/uncompared rows:',len(failures))

if __name__=='__main__':main()
