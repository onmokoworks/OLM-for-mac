"""Replay older corpora plus T17's three cases without modifying gate files."""
import json, os, subprocess, sys
from collections import defaultdict
from pathlib import Path
from aliasing import ROOT, STATE, EVIDENCE, memory
T17='8bb478938cf7fd968cd3fdb8dcc92b97665e37be'
paths=[p for p in (ROOT/'tests/fuzz_corpus').rglob('*.json') if p.relative_to(ROOT/'tests/fuzz_corpus').parts[0].startswith('olmdirectionalblur')]
retained=STATE/'realscale-corpus';retained.mkdir(exist_ok=True)
for name in ('32x18','1920x1080','3840x2160'):
    p=retained/(name+'.json')
    p.write_bytes(subprocess.check_output(['git','show',f'{T17}:mac/OLMDirectionalBlur/tests/realscale-corpus/{name}.json'],cwd=ROOT));paths.append(p)
corpora=defaultdict(list)
for p in paths:
    d=json.loads(p.read_text());corpora[(p.parent,d['max_size'],d.get('size_sampler','default'),d.get('size_max_height'))].append(p)
commands=[]
for (directory,maximum,sampler,height),files in sorted(corpora.items(),key=lambda item:str(item[0])):
    mixed=sum(k[0]==directory for k in corpora)>1
    for target in files if mixed else [directory]:
        free=memory();label=target.name.replace('.json','')
        report=EVIDENCE/f'replay-{label}.json'
        cmd=[sys.executable,str(ROOT/'tools/fuzz/run.py'),'--plugin','olmdirectionalblur','--jobs','1','--replay',str(target),
             '--max-size',str(maximum),'--size-sampler',sampler,'--case-timeout','60','--scratch',str(STATE/'replay'),'--report',str(report)]
        if height is not None:cmd+=['--size-max-height',str(height)]
        with (STATE/f'replay-{label}.log').open('w') as log:r=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        commands.append(dict(command=cmd,returncode=r.returncode,memory_free_percent=free))
        (EVIDENCE/'replay-commands.json').write_text(json.dumps(commands,indent=2)+'\n');print(label,r.returncode,flush=True)
        data=json.loads(report.read_text());assert data['replays'],report
rows=[]
for c in commands:
    path=Path(c['command'][c['command'].index('--report')+1])
    rows+=json.loads(path.read_text())['replays']
summary=dict(cases=len(rows),strict_matches=sum(r['matches_saved'] for r in rows),differences=[])
def diff(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        return [d for k in sorted(a.keys()|b.keys()) for d in diff(a.get(k),b.get(k),path+'/'+k)]
    return [] if a==b else [dict(path=path,saved=a,observed=b)]
for r in rows:
    saved=json.loads(Path(r['path']).read_text())['result']
    differences=diff(saved,r['result'])
    if differences:summary['differences'].append(dict(case=r['path'],differences=differences))
(EVIDENCE/'replay-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('Strict saved matches',summary['strict_matches'],'/',len(rows),flush=True)
sys.exit(summary['strict_matches']!=len(rows))
