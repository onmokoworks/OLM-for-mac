"""Sequential two-seed campaign; each oracle owns at most three route-case jobs."""
from pathlib import Path
import json, os, subprocess, sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ORIGINAL=ROOT.parent/'ghidra_windows_aex/OLMSmoother2.aex'
env=dict(os.environ,AEXCOMPAT_FRAME_DEADLINE_MS='120000')
records=[]
for seed in [20261116,20261117]:
    out=HERE/f'campaign-{seed}'
    args=[sys.executable,str(ROOT/'rust/tools/oracle/olm_oracle.py'),'render',
          '--reference',str(ORIGINAL),'--candidate',str(HERE/'OLMSmoother2-verified.aex'),
          '--routes','smart8,smart16,smart32','--cases','103','--seed',str(seed),
          '--jobs','3','--downsample','1,1/2,1/4','--timeout','120','--out',str(out)]
    print(f'Starting seed {seed}',flush=True)
    with (HERE/f'campaign-{seed}.log').open('w',encoding='utf-8') as log:
        p=subprocess.Popen(args,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        records.append({'seed':seed,'pid':p.pid,'argv':args,'exit_code':None})
        (HERE/'campaign-processes.json').write_text(json.dumps(records,indent=2))
        code=p.wait()
    records[-1]['exit_code']=code
    (HERE/'campaign-processes.json').write_text(json.dumps(records,indent=2))
    print(f'Seed {seed} exited {code}',flush=True)
    if code!=0:raise SystemExit(code)
