#!/usr/bin/env python3
"""Serial existing DG/Kira corpus replays, capture explicitly disabled."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
from targets import T23, TICKET, PLUGINS
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--t23',action='store_true')
p.add_argument('--resume',action='store_true')
p.add_argument('--worker',type=Path,help='Override the saved corpus worker')
p.add_argument('--scratch',type=Path,default=ROOT/'orchestra/state'/TICKET/'regression')
args=p.parse_args()
worker_hash=None
if args.worker:
    with args.worker.open('rb') as stream:worker_hash=hashlib.file_digest(stream,'sha256').hexdigest()
S=args.scratch.resolve();S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
env.pop('OLM_LIVE_CAPTURE_DIR',None)
failed=False
for directory in sorted((ROOT/'tests/fuzz_corpus').iterdir()):
    if not directory.name.startswith(tuple('radialblur' if p=='OLMRadialBlur' else p.lower() for p in PLUGINS)):continue
    cases=sorted(directory.glob('*.json'))
    if not cases:continue
    sizes={json.loads(p.read_text())['max_size'] for p in cases}
    targets=cases if len(sizes)>1 else [directory]
    for target in targets:
        sample=target if target.is_file() else cases[0]
        saved=json.loads(sample.read_text());plugin=saved['plugin']
        name=directory.name+('-'+target.stem if target.is_file() else '')
        report=S/(name+'.json')
        if args.resume and report.exists():
            previous=json.loads(report.read_text())
            groups=previous.get('replay_groups',[])
            same_worker=worker_hash is None or (groups and all(g['provenance']['worker_sha256']==worker_hash for g in groups))
            if previous.get('replay_matches_saved') is True and same_worker:
                print(name,'already verified',flush=True);continue
        cmd=[sys.executable,str(ROOT/'tools/fuzz/run.py'),'--plugin',plugin,'--jobs','1','--replay',str(target),
             '--scratch',str(S/'scratch'),'--report',str(report),'--budget-minutes','30','--max-size',str(saved['max_size'])]
        if saved.get('size_sampler'):cmd+=['--size-sampler',saved['size_sampler']]
        if saved.get('size_max_height'):cmd+=['--size-max-height',str(saved['size_max_height'])]
        if args.worker:cmd+=['--worker',str(args.worker.resolve())]
        with (S/(name+'.log')).open('w') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
        print(name,1 if target.is_file() else len(cases),r.returncode,flush=True)
        if r.returncode:failed=True
if failed:raise SystemExit(1)
