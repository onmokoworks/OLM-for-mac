#!/usr/bin/env python3
"""Compare every default seed-1 candidate output to the ticket base, and reject exact-to-non-exact transitions."""
import json
import os
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace
import adapters.olmcolorkey as module
from core import sha
from run import main_checkout
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/P01c-colorkey-downsample/regression'
BASE='22f8f802'

def main():
    S.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
    deadline=time.monotonic()+1800
    options=SimpleNamespace(max_size=256,case_timeout=10,main=main_checkout(),
        worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker')
    source=module.SOURCE
    base=S/'baseline-source/mac/OLMColorKey';base.mkdir(parents=True,exist_ok=True)
    for name in ('OLMColorKey.cpp','OLMColorKey.h','OLMColorKey_Strings.cpp','OLMColorKey_Strings.h'):
        data=subprocess.check_output(['git','show',BASE+':mac/OLMColorKey/'+name],cwd=ROOT).decode()
        for include in ('ucrtmath/include/ucrtmath.h','core/x86_float.h'):
            data=data.replace('"../../'+include+'"','"'+str(ROOT/include)+'"')
        (base/name).write_text(data)
    adapters=[]
    for label,src in [('base',base/'OLMColorKey.cpp'),('final',source)]:
        d=S/(label+'-build');d.mkdir(exist_ok=True)
        module.SOURCE=src
        adapter=module.Adapter(options)
        adapter.env.update(TMPDIR=str(d),TMP=str(d),TEMP=str(d))
        adapter.binary,_=adapter.build(d,deadline)
        adapters.append(adapter)
    module.SOURCE=source
    failures=[];changed=[];count=0
    for i in range(2000):
        case=adapters[1].generate(1,i)
        for route in ('classic','smart'):
            outputs=[a.candidate(case,S,route,deadline) for a in adapters]
            if outputs[0][0]['status'] != outputs[1][0]['status'] or outputs[0][1] != outputs[1][1]:
                oracle,ref=adapters[1].oracle(case,S,deadline,route)
                before=oracle['status']=='ok' and outputs[0][0]['status']=='ok' and outputs[0][1]==ref
                after=oracle['status']=='ok' and outputs[1][0]['status']=='ok' and outputs[1][1]==ref
                row=dict(index=i,route=route,before_exact=before,after_exact=after,
                    oracle=oracle,hashes=[sha(o[1]) for o in outputs],reference_sha256=sha(ref))
                changed.append(row)
                if before and not after or oracle['status']!='ok':failures.append(row)
            count+=1
        if i%250==249:print(i+1,'failures',len(failures),flush=True)
    report=dict(base=BASE,cases=2000,route_comparisons=count,failures=failures,changed=changed,
        candidate_sha256=[sha(a.binary.read_bytes()) for a in adapters],
        final_source_sha256=sha(source.read_bytes()))
    (S/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(count,'route comparisons; failures',len(failures),flush=True)
    assert not failures

if __name__=='__main__':main()
