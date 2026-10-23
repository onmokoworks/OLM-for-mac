#!/usr/bin/env python3
"""Bisect UCRT link failures with HEAD harnesses and isolated revision source trees.
Only core/ and mac/ vary; current read-only fixtures and SDK are shared.
No worker is rebuilt. Compilation success is distinct from numerical test success.
"""
import argparse, json, os, re, shutil, signal, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/I03-integration-check'
B=S/os.environ.get('I03_BISECT_LABEL','link-bisect');B.mkdir(exist_ok=True)
MODE=os.environ.get('I03_BISECT_MODE','link')
GOOD='passed' if MODE=='exit' else 'compiled'
BAD='failed' if MODE=='exit' else 'ucrt_link_failure'
SNAP=B/'checkout'
PY=str(ROOT.parent.parent/'tools/emulation/.venv/bin/python3')
ENV=dict(os.environ,OLM_TEST_JOBS='2',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(B),TMP=str(B),TEMP=str(B),OLM_MAIN_ASSETS=str(ROOT.parent.parent),PYTHONPATH=os.pathsep.join([str(SNAP),str(SNAP/'tools/emulation')]))
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def archive(rev,paths):
    with (B/'archive.log').open('a') as log:
        p=subprocess.Popen(['git','archive',rev,*paths],cwd=ROOT,stdout=subprocess.PIPE,stderr=log)
        q=subprocess.run(['tar','-xf','-','-C',str(SNAP)],stdin=p.stdout,stdout=log,stderr=log)
        p.stdout.close();assert p.wait()==0 and q.returncode==0
if SNAP.exists():shutil.rmtree(SNAP)
SNAP.mkdir()
archive('HEAD',['tools','tests','scripts','ucrtmath','refs/scripts','cli'])
for child in (ROOT/'refs').iterdir():
    if child.name!='scripts': (SNAP/'refs'/child.name).symlink_to(child,target_is_directory=child.is_dir())
for name in ('reports','Headers','Util','Resources'):(SNAP/name).symlink_to(ROOT/name,target_is_directory=True)
loaded=None;rows=[];boundaries=[]
def probe(test,rev):
    global loaded
    rev=git('rev-parse',rev)
    if loaded!=rev:
        for folder in ('core','mac'):shutil.rmtree(SNAP/folder,ignore_errors=True)
        archive(rev,['core','mac']);loaded=rev
    name=Path(test).stem+'-'+rev[:8]
    events=B/(name+'.json');log=B/(name+'.log')
    command=[PY,str(ROOT/'orchestra/reports/I03-probe-test.py'),str(SNAP),test]
    start=time.monotonic()
    with log.open('w') as stream:
        proc=subprocess.Popen(command,cwd=SNAP,env=dict(ENV,I03_COMPILE_EVENTS=str(events)),stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try: code=proc.wait(timeout=300)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL);proc.wait();code=124
        finally:
            try: os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError: pass
    text=log.read_text(errors='replace');observed=json.loads(events.read_text()) if events.exists() else []
    symbols=sorted(set(re.findall(r'"(_ucrt_[a-z0-9_]+)"',text)))
    bad=bool(symbols and 'linker command failed' in text)
    good=bool(observed) and all(r['exit']==0 for r in observed)
    row=dict(test=test,revision=rev,command=command,exit=code,compiler_events=observed,missing_symbols=symbols,outcome=(GOOD if code==0 else BAD) if MODE=='exit' else BAD if bad else GOOD if good else 'unresolved',seconds=round(time.monotonic()-start,3),log=str(log.relative_to(S)))
    rows.append(row);(B/'results.json').write_text(json.dumps(dict(probes=rows,boundaries=boundaries),indent=2)+'\n')
    print(test,rev[:8],row['outcome'],code,flush=True)
    return row['outcome']
parser=argparse.ArgumentParser();parser.add_argument('--tests',nargs='*');parser.add_argument('--boundary');args=parser.parse_args()
generic=json.loads((S/'generic.json').read_text())
tests=args.tests or [r['test'] for r in generic['entries'] if '_ucrt_' in r.get('stdout','')+r.get('stderr','')]
# Static retained worker executables also expose the missing link dependency.
if not args.tests:tests+=['refs/scripts/smoke_olmblur_worker_orchestration.py','refs/scripts/smoke_olmblur_worker32_nonlegacy.py','refs/scripts/smoke_olmblur_worker32_legacy.py','tools/emulation/smoke_olmblur_worker16_legacy.py']
base='c67a52fb388110966df4c8712cc570af69163929'
changes=git('log','--first-parent','--reverse','--format=%H',base+'..HEAD','--','core','mac').splitlines()
for test in tests:
    if args.boundary:
        at_head=probe(test,'HEAD');parent=probe(test,args.boundary+'^1');bad=probe(test,args.boundary)
        merge=git('rev-parse',args.boundary)
        boundaries.append(dict(test=test,status='bisected' if parent==GOOD and bad==BAD and at_head==BAD else 'unresolved',merge=merge,subject=git('show','-s','--format=%s',merge),parent=parent,at_merge=bad,head=at_head,method='adjacent controls; candidate nominated from source history and main bisection'))
        (B/'results.json').write_text(json.dumps(dict(probes=rows,boundaries=boundaries),indent=2)+'\n')
        continue
    lo_out=probe(test,base);hi_out=probe(test,'HEAD')
    if lo_out!=GOOD or hi_out!=BAD:
        boundaries.append(dict(test=test,status='unresolved',baseline=lo_out,head=hi_out));continue
    lo,hi=-1,len(changes)-1
    while hi-lo>1:
        mid=(lo+hi)//2;out=probe(test,changes[mid])
        if out==GOOD:lo=mid
        elif out==BAD:hi=mid
        else:break
    if hi-lo==1:
        parent=probe(test,changes[hi]+'^1');bad=probe(test,changes[hi])
        boundaries.append(dict(test=test,status='bisected' if parent==GOOD and bad==BAD else 'unresolved',merge=changes[hi],subject=git('show','-s','--format=%s',changes[hi]),parent=parent,at_merge=bad))
    else:boundaries.append(dict(test=test,status='unresolved',low=lo,high=hi))
    (B/'results.json').write_text(json.dumps(dict(probes=rows,boundaries=boundaries),indent=2)+'\n')
shutil.rmtree(SNAP)
(B/'results.json').write_text(json.dumps(dict(probes=rows,boundaries=boundaries),indent=2)+'\n')
