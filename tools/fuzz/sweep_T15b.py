#!/usr/bin/env python3
"""Serial, resumable T15b measurement. One emulator/candidate process at a time."""
import argparse, copy, importlib, json, os, shutil, struct, sys, time
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode = True
from core import evaluate, sha, proposals, apply_operation, save_corpus
from geometry import sample, require_host
from run import ROOT, main_checkout
PLUGINS = ('olmcolorkey','olmdirectionalblur','colorkeep','olmblur','olmtoondilate',
           'olmsmoother2','olmsmoother','olmdistancegradation','olmkirakira','radialblur')
S = ROOT/'orchestra/state/T15b-odd-even-random-comp-sweep'
E = ROOT/'orchestra/reports/T15b-evidence'
WORKER = Path.home()/'.cache/olm-emu/worker-F52c-geom/aex-guest-worker'

def write(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')

def category(result, route):
    oracle = result.get('oracles',{}).get(route,result['oracle'])
    value = result['routes'][route]
    if oracle['status'] != 'ok': return 'U'
    return {'exact':'E','mismatch':'M','refusal':'R'}.get(value['status'],'U')

def failure_key(result, route, attr, case=None):
    k = category(result,route)
    if k not in ('M','R'): return None
    v = result['routes'][route]
    if k == 'M':
        symptom='rectangle' if 'geometry_diff' in v else 'pixels'
        return symptom + (':PF'+str(case['depth'])+':'+case['profile'] if case else '')
    return 'refusal:'+','.join(attr.get(route,[]) or [str(v.get('error'))])

def calibration_case(a, n, depth, height=None):
    h = height or n
    c = a.generate(2026,0)
    c.update(geometry=[n,h],depth=depth,profile='sdr',parameters=a.defaults(n,h))
    # Fixed varying 4-pixel SDR pattern; full output, no padding, unit downsample.
    values=[(255,51,102,153),(128,255,0,64),(0,0,0,0),(255,255,255,255)]
    pixels=b''.join(bytes(v) if depth==8 else struct.pack('<4H',*(round(x*32768/255) for x in v)) if depth==16 else struct.pack('<4f',*(x/255 for x in v)) for v in values)
    c['pixels']=(pixels*((n*h+3)//4))[:n*h*(depth//8*4)]
    c.update(geometry_sampler='realistic-v1',full_geometry=[n,h],downsample=[[1,1],[1,1]],
             extent_hint=[0,0,n,h],request_rect=[0,0,n,h],pixel_aspect=[1,1],
             input_padding=0,output_padding=0,rowbytes_padding=0)
    return c

def calibrate(a, stage, route):
    rows=[]; maxima={}
    for depth in (8,16,32):
        lo=0; hi=None
        for n in (1,16,32,64,128,256,512,1024,2048,4096):
            c=calibration_case(a,n,depth);start=time.monotonic()
            r,raw=a.oracle(c,stage,time.monotonic()+12,route)
            rows.append(dict(depth=depth,size=n,seconds=round(time.monotonic()-start,4),result=r,sha256=sha(raw)))
            print('CAL',a.name,depth,n,rows[-1]['seconds'],r['status'],flush=True)
            if r['status']=='ok':lo=n
            else:hi=n;break
        # Refine this observed bracket. Runtime is NOT assumed monotone; this
        # finds the largest tested success, not a universal integer threshold.
        if hi and lo:
            while hi-lo>1:
                n=(lo+hi)//2;c=calibration_case(a,n,depth);start=time.monotonic()
                r,raw=a.oracle(c,stage,time.monotonic()+12,route)
                rows.append(dict(depth=depth,size=n,seconds=round(time.monotonic()-start,4),result=r,sha256=sha(raw)))
                print('CAL',a.name,depth,n,rows[-1]['seconds'],r['status'],flush=True)
                if r['status']=='ok':lo=n
                else:hi=n
        maxima[str(depth)]=dict(largest_completed=lo,first_noncompletion=hi)
    result=dict(workload='defaults, fixed varying 4-pixel SDR, square full output, unit downsample/aspect, zero padding; bounded search to 4096; nonmonotone timing, largest tested success only, not a universal performance ceiling',maxima=maxima,rows=rows)
    write(E/(a.name+'-calibration.json'),result)
    return max(v['largest_completed'] for v in maxima.values()) or 1

def reduce_witness(a, original, route, key, stage):
    single=copy.copy(a);single.routes=(route,);single.oracle_routes={route:route}
    c=original;accepted=[];attempts=0;until=time.monotonic()+100
    while attempts<40 and time.monotonic()<until:
        improved=False
        for op in proposals(single,c):
            if attempts>=40 or time.monotonic()>=until:break
            cc=apply_operation(single,c,op)
            if cc==c:continue
            attempts+=1;attr={};rr=evaluate(single,cc,stage,time.monotonic()+25,attr)
            if failure_key(rr,route,attr,cc)==key:
                c=cc;accepted.append(op);improved=True;break
        if not improved:break
    return c,dict(attempts=attempts,accepted=accepted,bounded=True,minimality_claimed=False)

def campaign(name, args):
    stage=S/name;stage.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(stage),TMP=str(stage),TEMP=str(stage),PYTHONDONTWRITEBYTECODE='1')
    a=importlib.import_module('adapters.'+name).Adapter(SimpleNamespace(main=main_checkout(),worker=WORKER,max_size=256,case_timeout=10,size_sampler='default'))
    route='classic' if name=='olmsmoother' else 'smart'
    require_host(a,{'geometry_sampler':'realistic-v1'})
    a.routes=(route,);a.oracle_routes={route:route}
    provenance=a.prepare(stage,time.monotonic()+300);provenance['case_timeout_seconds']=10
    write(E/(name+'-provenance.json'),provenance)
    cal=E/(name+'-calibration.json')
    if cal.exists(): maximum=max(v['largest_completed'] for v in json.loads(cal.read_text())['maxima'].values()) or 1
    else: maximum=calibrate(a,stage,route)
    calibration=json.loads(cal.read_text())
    if 'wide' not in calibration:
        calibration['wide']=[]
        for depth in (8,16,32):
            c=calibration_case(a,1920,depth,1080);start=time.monotonic()
            r,raw=a.oracle(c,stage,time.monotonic()+12,route)
            calibration['wide'].append(dict(depth=depth,geometry=[1920,1080],seconds=round(time.monotonic()-start,4),result=r,sha256=sha(raw)))
        write(cal,calibration)
    height_maximum=maximum
    if any(r['result']['status']=='ok' for r in calibration['wide']):maximum=1920;height_maximum=1080
    if args.calibrate_only:
        shutil.rmtree(stage);return
    a.max_size=maximum;a.size_max_height=height_maximum;a.size_sampler='odd-even-v1'
    first={};counts=Counter();parity=defaultdict(Counter);ds=defaultdict(Counter);depths=defaultdict(Counter)
    path=E/(name+'-cases.jsonl')
    with path.open('w') as out:
        for seed in (2026,2027):
            for i in range(args.n):
                c=sample(a.generate(seed,i),'realistic');require_host(a,c)
                # require_host restores the Classic-only contract for Smoother.
                attr={};start=time.monotonic();r=evaluate(a,c,stage,time.monotonic()+30,attr)
                k=category(r,route);counts[k]+=1
                parity['/'.join('odd' if n%2 else 'even' for n in c['full_geometry'])][k]+=1
                ds['/'.join(str(x[1]) for x in c['downsample'])][k]+=1;depths[str(c['depth'])][k]+=1
                key=failure_key(r,route,attr,c)
                row=dict(case={k:v for k,v in c.items() if k!='pixels'},input_sha256=sha(c['pixels']),result=r,refusals=attr,category=k,failure_class=key,elapsed_seconds=round(time.monotonic()-start,4))
                out.write(json.dumps(row,sort_keys=True)+'\n');out.flush()
                if key and key not in first:first[key]=c
                if (i+1)%25==0:print('SWEEP',name,seed,i+1,dict(counts),flush=True)
    summary=dict(route=route,maximum=maximum,height_maximum=height_maximum,counts=dict(counts),parity=dict(parity),downsample=dict(ds),depth=dict(depths),witnesses=[])
    write(E/(name+'-summary.json'),summary)
    for key,original in first.items():
        c,reduction=reduce_witness(a,original,route,key,stage)
        # Standard replay evaluates both routes (Classic only for Smoother v1).
        both=copy.copy(a);both.routes=('classic',) if name=='olmsmoother' else ('classic','smart')
        both.oracle_routes={rt:rt for rt in both.routes}
        attr={};r=evaluate(both,c,stage,time.monotonic()+50,attr)
        unavailable=[rt for rt,oo in r.get('oracles',{'primary':r['oracle']}).items() if oo['status']!='ok']
        # Non-renderable Classic is allowed in saved results; timeouts are not.
        timeout=any(oo['status']=='budget' for oo in r.get('oracles',{'primary':r['oracle']}).values())
        witness=dict(failure_class=key,first_seed=original['seed'],first_index=original['index'],geometry=c['geometry'],result=r,refusals=attr,reduction=reduction,unavailable_routes=unavailable)
        if not timeout:
            corpus=ROOT/'tests/fuzz_corpus'/name/'T15b-odd-even-realistic';corpus.mkdir(parents=True,exist_ok=True)
            p=corpus/(sha(key.encode())[:12]+'.json')
            save_corpus(p,a,original,c,r,reduction,provenance)
            witness['path']=str(p.relative_to(ROOT))
        else:witness['omission']='oracle timeout on one route; not saved'
        summary['witnesses'].append(witness);write(E/(name+'-summary.json'),summary)
        print('WITNESS',name,key,c['geometry'],witness.get('path',witness.get('omission')),flush=True)
    shutil.rmtree(stage)
    print('DONE',name,dict(counts),flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--plugin',choices=PLUGINS);ap.add_argument('--n',type=int,default=150);ap.add_argument('--jobs',type=int,choices=[1],default=1);ap.add_argument('--calibrate-only',action='store_true');args=ap.parse_args()
    S.mkdir(parents=True,exist_ok=True);E.mkdir(parents=True,exist_ok=True)
    for name in ([args.plugin] if args.plugin else PLUGINS):
        campaign(name,args)
if __name__=='__main__':main()
