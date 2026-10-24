#!/usr/bin/env python3
"""Summarize only recorded T15b observations; never infer missing campaigns."""
import json
from collections import Counter,defaultdict
from pathlib import Path
from core import sha
from sweep_T15b import ROOT,E,PLUGINS,write

def reason(row,route):
    oracle=row['result'].get('oracles',{}).get(route,row['result']['oracle'])
    candidate=row['result']['routes'][route]
    if oracle['status']=='ok':return 'candidate:'+candidate['status']+':'+str(candidate.get('returncode',candidate.get('error','')))
    d=oracle.get('diagnostic','')
    if oracle['status']=='budget':return 'oracle:budget'
    for tag in ('data arena exhausted','VCRUNTIME exception owned string','UC_ERR_WRITE_UNMAPPED','UC_ERR_READ_UNMAPPED','medianBlur','inv_scale_x','IwException@ipp','guard','unsupported','pixel format','render_error','dimensions'):
        if tag in d:return 'oracle:'+oracle['status']+':'+tag
    return 'oracle:'+oracle['status']+':'+d[:100]

def main():
    allresults={}
    for name in PLUGINS:
        path=E/(name+'-summary.json')
        if not path.exists():continue
        summary=json.loads(path.read_text());route=summary['route']
        seeds=defaultdict(Counter);unavailable=Counter();classes=defaultdict(list);coverage=Counter();first_u={}
        count=0
        for line in (E/(name+'-cases.jsonl')).open():
            r=json.loads(line);c=r['case'];count+=1;k=r['category'];seeds[str(c['seed'])][k]+=1
            w,h=c['full_geometry'];coverage['width_odd']+=w%2;coverage['height_odd']+=h%2
            coverage['square']+=w==h;coverage['wide']+=w>h;coverage['tall']+=h>w;coverage['one_pixel_strip']+=(min(w,h)==1 and max(w,h)>1)
            if k=='U':
                key=reason(r,route);unavailable[key]+=1;first_u.setdefault(key,dict(seed=c['seed'],index=c['index'],result=r['result']))
            if r['failure_class']:classes[r['failure_class']].append(dict(seed=c['seed'],index=c['index']))
        summary.update(completed=count,seeds=dict(seeds),unavailable=dict(unavailable),first_unavailable=first_u,classes=dict(classes),coverage=dict(coverage))
        allresults[name]=summary
    write(E/'counts.json',allresults)
    write(E/'framework-sha256.json',{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted((ROOT/'tools/fuzz').rglob('*')) if p.is_file() and p.suffix in ('.py','.cpp','.hpp')})
    def counts(c):return '/'.join(str(c.get(k,0)) for k in 'EMRU')
    lines=['| Plugin | E/M/R/U | 2026 | 2027 | Full-comp ceiling |','|---|---|---|---|---|']
    for n,s in allresults.items():lines.append(f"| {n} | {counts(s['counts'])} | {counts(s['seeds'].get('2026',{}))} | {counts(s['seeds'].get('2027',{}))} | {s['maximum']}x{s['height_maximum']} |")
    for field,keys in [('parity',['odd/odd','odd/even','even/odd','even/even']),('downsample',['1/1','2/2','3/3','4/4','8/8','2/3'])]:
        lines+=['', '| Plugin | '+' | '.join(keys)+' |','|---|'+'---|'*len(keys)]
        for n,s in allresults.items():lines.append('| '+n+' | '+' | '.join(counts(s[field].get(k,{})) for k in keys)+' |')
    (E/'tables.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines[:len(allresults)+2]))
if __name__=='__main__':main()
