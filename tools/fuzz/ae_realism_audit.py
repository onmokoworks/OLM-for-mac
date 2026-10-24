#!/usr/bin/env python3
"""Oracle-free, sequential audit of actual Mach-O bundles in the P00 SDK host."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path.home()/'.cache/olm-emu/P00'
STATE = ROOT/'orchestra/state/P00-ae-realism-refusal-audit'
PLUGINS = dict(olmblur='OLMBlur', colorkeep='ColorKeep', olmcolorkey='OLMColorKey',
    olmdirectionalblur='OLMDirectionalBlur', olmdistancegradation='OLMDistanceGradation',
    olmkirakira='OLMKiraKira', olmsmoother2='OLMSmoother2', olmtoondilate='OLMToonDilate',
    radialblur='OLMRadialBlur', olmsmoother='OLMSmoother')

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def memory():
    text=subprocess.check_output(['memory_pressure'],text=True)
    return int(re.search(r'System-wide memory free percentage: (\d+)%',text)[1])

def situations():
    # Independent host-shape probes, not a Cartesian product of all axes.
    base=dict(w=1920,h=1080,dx=1,dy=1,pad=0,extent=0,roi=0,an=1,ad=1,expand=0)
    changes=[('full',{}),('half',dict(dx=2,dy=2)),('quarter',dict(dx=4,dy=4)),
        ('third',dict(dx=3,dy=3)),('eighth',dict(dx=8,dy=8)),('asymmetric',dict(dx=2)),
        ('4k',dict(w=3840,h=2160)),('square',dict(w=1000,h=1000)),
        ('odd',dict(w=1279,h=719)),('odd-half',dict(w=1279,h=719,dx=2,dy=2)),
        ('large-layer',dict(w=2560,h=1440,roi=2)),
        ('aligned-odd',dict(w=1279,h=719,pad=-1)),('padded',dict(pad=256)),
        ('extent',dict(extent=1)),('roi',dict(roi=1)),('expanded',dict(expand=1)),
        ('cropped-expand',dict(extent=2,expand=1)),
        ('aspect09',dict(an=9,ad=10)),('aspect2',dict(an=2))]
    return [(n,dict(base,**v)) for n,v in changes]

def samples(plugin):
    eligible=[]
    for p in sorted((ROOT/'tests/fuzz_corpus'/plugin).glob('*.json')):
        v=json.loads(p.read_text())
        route='classic' if plugin=='olmsmoother' else 'smart'
        if v.get('result',{}).get('routes',{}).get(route,{}).get('status')=='exact':
            eligible.append((p,v))
    if not eligible:
        return [],0
    rng=random.Random(0)
    chosen=rng.sample(eligible,min(10,len(eligible)))
    # Some directories contain fewer than 10 records; explicitly sample with replacement.
    while len(chosen)<10: chosen.append(rng.choice(eligible))
    return chosen,len(eligible)

def build_host(state,cache):
    cache.mkdir(parents=True,exist_ok=True)
    source=ROOT/'tools/emulation/aexcompat_patches/P00-host-realism.cpp'
    command=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',
        '-Wno-pragma-pack','-I'+str(ROOT/'Headers'),'-I'+str(ROOT/'Headers/SP'),
        str(source),'-o',str(cache/'plugin-host')]
    env=dict(os.environ,TMPDIR=str(state),TMP=str(state),TEMP=str(state))
    with (state/'host-build.log').open('w') as log:
        subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    record=dict(name='P00',worker_path=str(cache/'plugin-host'),worker_sha256=sha(cache/'plugin-host'),
        build_json=str(cache/'build.json'),bundles_path=str(cache),command=command,
        source_sha256=sha(source),capability='plugin-only AE realism host; arm64; no oracle',
        recipe='python3 tools/fuzz/ae_realism_audit.py --build-host',bundle_sha256={})
    for name in PLUGINS.values():
        exe=cache/'xcode'/name/'products'/(name+'.plugin')/'Contents/MacOS'/name
        if exe.exists():record['bundle_sha256'][name]=sha(exe)
    (cache/'build.json').write_text(json.dumps(record,indent=2)+'\n')
    index=cache.parent/'INDEX.json'
    data=json.loads(index.read_text())
    data['links']=[r for r in data['links'] if r['name']!='P00']+[record]
    index.write_text(json.dumps(data,indent=2)+'\n')
    print('Built and registered',record['worker_sha256'])

def summarize(state):
    summary={}
    for phase in ('baseline','matrix'):
        counts=collections.Counter(); groups={};n=0;identities=set()
        with (state/(phase+'.jsonl')).open() as rows:
            for line in rows:
                r=json.loads(line);n+=1;counts[r['status']]+=1
                identity=(r['plugin'],r['case'],r['situation'],r['depth'])
                assert identity not in identities,identity
                identities.add(identity)
                key=r['plugin']+'/'+r['situation']
                group=groups.setdefault(key,collections.Counter())
                group[r['status']]+=1
                for tag in r['tags']:group[tag]+=1
                if r['status']=='ok' and not r['result']['nonzero']:group['ok_all_zero']+=1
        manifest=json.loads((state/(phase+'-manifest.json')).read_text())
        expected=(len(manifest['bundles'])*9 if phase=='baseline' else sum(len(situations())*3*(1+len(v['paths'])) for v in manifest['samples'].values()))
        assert n==expected,(phase,n,expected)
        assert dict(counts)==manifest['counts']
        summary[phase]=dict(rows=n,counts=dict(counts),groups={k:dict(v) for k,v in groups.items()})
    (state/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print({k:dict(rows=v['rows'],counts=v['counts']) for k,v in summary.items()})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phase',choices=['baseline','matrix'])
    p.add_argument('--build-host',action='store_true')
    p.add_argument('--summarize',action='store_true')
    p.add_argument('--resume',action='store_true',help='Resume rows with matching baseline binary identities')
    p.add_argument('--state',type=Path,default=STATE)
    p.add_argument('--cache',type=Path,default=CACHE)
    p.add_argument('--timeout',type=float,default=15)
    p.add_argument('--jobs',type=int,choices=[1],default=1)
    p.add_argument('--plugins',nargs='+',choices=PLUGINS,default=list(PLUGINS))
    a=p.parse_args();a.state.mkdir(parents=True,exist_ok=True)
    if a.build_host:
        build_host(a.state,a.cache)
        return
    if a.summarize:
        summarize(a.state)
        return
    if not a.phase:p.error('--phase, --build-host or --summarize is required')
    env={k:v for k,v in os.environ.items() if not k.startswith(('OLM','DBLUR','COLORKEEP'))}
    env.update(TMPDIR=str(a.state),TMP=str(a.state),TEMP=str(a.state))
    trace=a.state/'refusal.txt';env['OLM_REFUSAL_TRACE']=str(trace)
    host=a.cache/'plugin-host';manifest=dict(source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),host_sha256=sha(host),bundles={},samples={},memory=[],phase=a.phase,timeout=a.timeout)
    dst=a.state/(a.phase+'.jsonl');counts=collections.Counter()
    existing={}
    if a.resume:
        baseline=json.loads((a.state/'baseline-manifest.json').read_text())
        assert baseline['host_sha256']==sha(host),'host changed'
        with dst.open() as rows:
            for line in rows:
                r=json.loads(line);existing[(r['plugin'],r['case'],r['situation'],r['depth'])]=r
                counts[r['status']]+=1
    with dst.open('a' if a.resume else 'w') as rows:
        for plugin in a.plugins:
            free=memory();manifest['memory'].append(dict(plugin=plugin,free_percent=free))
            if free<30: raise RuntimeError(f'memory free {free}% <30%; stopping')
            name=PLUGINS[plugin];exe=a.cache/'xcode'/name/'products'/(name+'.plugin')/'Contents/MacOS'/name
            manifest['bundles'][plugin]=sha(exe)
            if a.resume:assert baseline['bundles'][plugin]==sha(exe),'bundle changed'
            cases=[('default',[])]
            if a.phase=='matrix':
                chosen,eligible=samples(plugin)
                manifest['samples'][plugin]=dict(eligible=eligible,paths=[str(f.relative_to(ROOT)) for f,v in chosen],sha256=[sha(f) for f,v in chosen])
                cases += [(f'corpus{i:02d}',v['case']['parameters']) for i,(f,v) in enumerate(chosen)]
            for identity,params in cases:
                config=a.state/'parameters.txt';lines=[]
                for q in params:
                    kind=q['kind'];val=q['value']
                    if plugin=='olmkirakira' and kind=='a':kind='s';val=val*65536
                    lines.append(f"{q['slot']} {kind} "+(' '.join(map(str,val)) if isinstance(val,list) else str(val))+'\n')
                config.write_text(''.join(lines))
                for situation,g in (situations()[:3] if a.phase=='baseline' else situations()):
                    for depth in (8,16,32):
                        if (plugin,identity,situation,depth) in existing:
                            assert existing[(plugin,identity,situation,depth)]['geometry']==g
                            continue
                        if counts.total()%100==0:
                            free=memory()
                            if free<30: raise RuntimeError(f'memory free {free}% <30%; stopping')
                        pad=g['pad']
                        if pad<0:pad=(-g['w']*(depth//8)*4)%64
                        command=[str(host),str(exe),*[str(g[k]) for k in ('w','h')],str(depth),*[str(g[k]) for k in ('dx','dy')],str(pad),*[str(g[k]) for k in ('extent','roi','an','ad','expand')],str(config),str(int(plugin=='olmsmoother'))]
                        trace.unlink(missing_ok=True);start=time.monotonic()
                        with (a.state/'host.stdout').open('w') as out,(a.state/'host.stderr').open('w') as err:
                            try:
                                proc=subprocess.run(command,stdout=out,stderr=err,env=env,timeout=a.timeout)
                                status='exit';rc=proc.returncode
                            except subprocess.TimeoutExpired:status='timeout';rc=None
                        wall=time.monotonic()-start
                        stdout=(a.state/'host.stdout').read_text();stderr=(a.state/'host.stderr').read_text()
                        result={}
                        if stdout.strip():result=json.loads(stdout.splitlines()[0])
                        tags=trace.read_text().splitlines() if trace.exists() else []
                        callbacks=re.findall(r'unsupported/invalid callback: ([^\n]+)',stderr)
                        if status!='timeout':
                            status='crash' if rc<0 else 'host_error' if callbacks or not result else 'ok' if rc==0 else 'refusal' if tags else 'pf_error'
                        row=dict(plugin=plugin,case=identity,situation=situation,geometry=g,depth=depth,padding=pad,status=status,returncode=rc,wall_seconds=wall,tags=tags,callbacks=callbacks,result=result,prerender=re.findall(r'P00 prerender ([^\n]+)',stderr),final_error=re.findall(r'P00 final_error=(\d+)',stderr))
                        if status in ('host_error','crash','timeout'):row['diagnostic']=stderr[-3000:]
                        rows.write(json.dumps(row,sort_keys=True)+'\n');rows.flush();counts[status]+=1
            print(plugin,dict(counts),flush=True)
    manifest['counts']=dict(counts)
    (a.state/(a.phase+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    print(dict(counts),flush=True)

if __name__=='__main__':main()
