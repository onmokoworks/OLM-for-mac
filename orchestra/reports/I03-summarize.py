#!/usr/bin/env python3
"""Summarize recorded I03 results, preserving raw route status categories."""
import collections, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/I03-integration-check'
PLUGINS={'olmblur':'OLMBlur','colorkeep':'ColorKeep','olmcolorkey':'OLMColorKey','olmdirectionalblur':'OLMDirectionalBlur','olmdistancegradation':'OLMDistanceGradation','olmkirakira':'OLMKiraKira','olmsmoother2':'OLMSmoother2','olmtoondilate':'OLMToonDilate','radialblur':'OLMRadialBlur','olmsmoother':'OLMSmoother'}
def read(path): return json.loads(path.read_text()) if path.exists() else {}
def campaign(path,route):
    data=read(path)
    counts=collections.Counter(r.get('result',{}).get('routes',{}).get(route,{}).get('status','framework_error') for r in data.get('cases',[]))
    mismatch=[dict(index=r['index'],depth=r.get('depth'),geometry=r.get('geometry'),corpus=r.get('corpus'),result=r['result']['routes'][route]) for r in data.get('cases',[]) if r.get('result',{}).get('routes',{}).get(route,{}).get('status')=='mismatch']
    return dict(status=data.get('status','not_run'),completed=data.get('completed',0),counts=dict(counts),mismatches=mismatch,summary=data.get('summary',{}))
def main():
    result={'plugins':{},'corpora':{},'retry':{},'gates':{},'commands':[]}
    for plugin,name in PLUGINS.items():
        route='classic' if plugin=='olmsmoother' else 'smart'
        result['plugins'][plugin]={'name':name,'route':route,'fresh':campaign(S/('fresh-'+plugin+'.json'),route),'bundle':campaign(S/(plugin+'-plugin-bundle.json'),route)}
    for path in sorted(S.glob('replay-*.json')):
        data=read(path); rows=data.get('replays',[])
        changed=[]
        for row in rows:
            if row['matches_saved']: continue
            old=read(Path(row['path']))['result'];new=row['result']
            changed.append(dict(path=row['path'],oracles_unchanged=all(old.get(k)==new.get(k) for k in ('oracle','oracles')),routes={k:{'before':old['routes'][k],'after':v} for k,v in new['routes'].items() if old['routes'][k]!=v}))
        result['corpora'][path.stem[7:]]=dict(status=data.get('status'),replayed=len(rows),matches=sum(r['matches_saved'] for r in rows),changes=changed)
    for path in sorted(S.glob('retry-*.json')):
        data=read(path);result['retry'][path.stem]=dict(status=data.get('status'),matches=data.get('replay_matches_saved'),replays=data.get('replays'))
    generic=read(S/'generic.json')
    result['gates']['generic']={'status':generic.get('status'),'counts':generic.get('counts'),'failures':[r for r in generic.get('entries',[]) if r['status']!='PASS']}
    fixtures=read(S/'fixtures/results.json')
    result['gates']['fixtures']={'counts':dict(collections.Counter(r['returncode'] for r in fixtures)),'skipped':sum(r.get('skipped',0) for r in fixtures),'lanes':{lane:dict(collections.Counter(r['returncode'] for r in fixtures if r['lane']==lane)) for lane in sorted({r['lane'] for r in fixtures})}}
    result['slices']=read(S/'F51/summary.json')
    result['commands']=[json.loads(line) for line in (S/'commands.jsonl').read_text().splitlines()]
    (S/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    for plugin,row in result['plugins'].items():print(plugin,'fresh',row['fresh']['counts'],'bundle',row['bundle']['counts'])
if __name__=='__main__': main()
