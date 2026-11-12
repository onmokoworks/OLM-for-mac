"""Turn-wide durable Codex budget: reserve before launch; never refund interruptions."""
import argparse
import json
from pathlib import Path
import time
import msvcrt

import autoport as a
from process import run,codex_executable


def generate(root,key,prompt,schema=None,model=None,effort='medium'):
    root.mkdir(parents=True,exist_ok=True)
    lock=(root/'budget.lock').open('a+b'); lock.write(b'0'); lock.flush(); lock.seek(0)
    msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    try:
        ledger=a.read(root/'budget.json') if (root/'budget.json').exists() else {'limit':60,'per_function':4,'seconds_per_attempt':300,'calls':[]}
        previous=[c for c in ledger['calls'] if c['function']==key]
        if len(ledger['calls'])>=60 or len(previous)>=4: raise RuntimeError('Codex budget exhausted')
        entry={'number':len(ledger['calls'])+1,'function':key,'attempt':len(previous)+1,'status':'reserved','started':time.time()}
        ledger['calls'].append(entry); a.write(root/'budget.json',ledger)
        out=root/'generation'/f"{entry['number']:02d}-{key}"
        out.mkdir(parents=True,exist_ok=False)
        (out/'prompt.txt').write_text(prompt,encoding='utf-8')
        schema=schema or {'type':'object','properties':{'code':{'type':'string'},'notes':{'type':'string'}},'required':['code','notes'],'additionalProperties':False}
        a.write(out/'schema.json',schema)
        cmd=[codex_executable(),'exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','-C',out,
             '-s','read-only','--json','--color','never','-c','project_doc_max_bytes=0',
             '-c','features.shell_tool=false','-c','features.multi_agent=false','-c','features.apps=false',
             '-c','web_search="disabled"','-c',f'model_reasoning_effort="{effort}"',
             '--output-schema',out/'schema.json','-o',out/'answer.json']
        if model:cmd+=['-m',model]
        started=time.monotonic()
        try:
            result=run(cmd+['-'],out/'codex',240,cwd=out,stdin=out/'prompt.txt')
            entry.update(status='failed' if result['returncode'] or result['timeout'] else 'generated',generation_seconds=result['seconds'],artifacts=str(out))
            events=[]
            for line in (out/'codex/stdout.txt').read_text(encoding='utf-8',errors='replace').splitlines():
                try:events.append(json.loads(line))
                except ValueError:pass
            if any(e.get('item',{}).get('type') in ['command_execution','mcp_tool_call','web_search','file_change'] for e in events):
                entry['status']='invalid-tool-use'; raise RuntimeError('source-blind generator used tools')
            entry['usage']=[e['usage'] for e in events if 'usage' in e]
            if entry['status']!='generated':raise RuntimeError('Codex failed; retained logs')
            return out,a.read(out/'answer.json')
        finally:
            entry['generation_elapsed']=time.monotonic()-started
            a.write(root/'budget.json',ledger)
    finally:
        lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1); lock.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('prompt',type=Path); p.add_argument('--root',type=Path,required=True)
    p.add_argument('--function',required=True); p.add_argument('--schema',type=Path)
    p.add_argument('--model');p.add_argument('--effort',choices=['low','medium','high','xhigh'],default='medium')
    x=p.parse_args()
    out,answer=generate(x.root.resolve(),x.function,x.prompt.read_text(encoding='utf-8'),a.read(x.schema) if x.schema else None,x.model,x.effort)
    print(out,flush=True)
