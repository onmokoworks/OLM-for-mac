"""Two-seed per-process qualification of the explicitly labelled reference bridge."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
TOOLS=HERE.parents[1]/'tools'
sys.path.insert(0,str(TOOLS/'autoport'))
from process import run
from autoport import digest

def campaign(candidate,original,reference,out):
    out.mkdir(parents=True,exist_ok=False)
    identity={k:{'path':str(v),'sha256':digest(v)} for k,v in [('candidate',candidate),('original_loaded_by_bridge',original),('bridge',reference)]}
    identity['scope']='diagnostic bridge; not a direct unmodified-host oracle pass'
    (out/'provenance.json').write_text(json.dumps(identity,indent=2))
    results=[]
    for seed in [20261113,20261114]:
        dest=out/f'seed-{seed}'
        r=run([sys.executable,TOOLS/'oracle/olm_oracle.py','render','--reference',reference,'--candidate',candidate,'--out',dest,'--cases','103','--seed',str(seed),'--jobs','3','--routes','smart8,smart16,smart32','--sizes','1x1,3x7,11x7,31x19','--downsample','1,1/2,1/4'],out/f'process-{seed}',600,env={'OLM_REFERENCE_ORIGINAL':str(original),'OLM_REFERENCE_REDUNDANT_CHECKIN':'1'})
        print((out/f'process-{seed}/stdout.txt').read_text(),flush=True)
        results.append({'seed':seed,'process':r,'summary':str(dest/'summary.json')})
    (out/'campaign.json').write_text(json.dumps({'identity':identity,'results':results},indent=2))
    return int(any(r['process']['returncode'] or r['process']['timeout'] or not r['process']['cleanup_verified'] for r in results))
if __name__=='__main__':
    p=argparse.ArgumentParser();[p.add_argument('--'+k,type=Path,required=True) for k in ['candidate','original','reference','out']];x=p.parse_args();raise SystemExit(campaign(*[getattr(x,k).resolve() for k in ['candidate','original','reference','out']]))
