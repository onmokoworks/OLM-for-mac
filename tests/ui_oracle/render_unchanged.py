#!/usr/bin/env python3
"""Compare pre-ticket and current production render bytes on seed1 n300 and all affected corpora."""
import argparse, importlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from core import load_corpus
MAIN=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
PLUGINS=['colorkeep','olmcolorkey','olmsmoother2','olmkirakira','radialblur']

def mirror(source,target,old):
    target.mkdir(parents=True,exist_ok=True)
    for child in source.iterdir():
        dest=target/child.name
        if child.is_dir() and any(p.is_relative_to(child) for p in old):mirror(child,dest,old)
        elif child in old:dest.write_bytes(subprocess.check_output(['git','show',f'{old[child]}:{child.relative_to(ROOT)}'],cwd=ROOT))
        else:dest.symlink_to(child,target_is_directory=child.is_dir())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scratch',type=Path,required=True);ap.add_argument('--base',required=True);args=ap.parse_args()
    scratch=args.scratch.resolve();scratch.mkdir(parents=True,exist_ok=True)
    os.environ['TMPDIR']=str(scratch)
    base=scratch/'base';base.mkdir(exist_ok=True)
    paths=['mac/ColorKeep/ColorKeep.cpp','mac/OLMColorKey/OLMColorKey.cpp','mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp','mac/OLMKiraKira/OLMKiraKira.cpp','mac/OLMRadialBlur/OLMRadialBlur.cpp']
    old={ROOT/p:args.base for p in paths}
    mirror(ROOT/'mac',base/'mac',old)
    for name in ['core','ucrtmath']: (base/name).symlink_to(ROOT/name,target_is_directory=True)
    results=[]
    for name in PLUGINS:
        module=importlib.import_module('adapters.'+name); options=SimpleNamespace(max_size=256,case_timeout=10,main=MAIN,worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker')
        owner=module.public if name=='radialblur' else module
        source=owner.SOURCE; candidates=[]
        for variant in ['before','after']:
            folder=scratch/name/variant;folder.mkdir(parents=True,exist_ok=True)
            owner.SOURCE=base/source.relative_to(ROOT) if variant=='before' else source
            adapter=module.Adapter(options);adapter.binary=adapter.build(folder,time.monotonic()+300)[0];candidates.append(adapter)
        owner.SOURCE=source
        checks=0;corpora=0
        def check(case,label):
            nonlocal checks
            for route in candidates[0].routes:
                observed=[]
                for variant,adapter in zip(['before','after'],candidates):
                    folder=scratch/name/('case-'+variant);folder.mkdir(exist_ok=True)
                    observed.append(adapter.candidate(case,folder,route,time.monotonic()+30));shutil.rmtree(folder)
                assert observed[0]==observed[1],(name,label,route,observed[0][0],observed[1][0])
                checks+=1
        for i in range(300):check(candidates[0].generate(1,i),f'seed1:{i}')
        for folder in sorted((ROOT/'tests/fuzz_corpus').glob(name+'*')):
            if not folder.is_dir():continue
            for path in sorted(folder.glob('*.json')):
                data=json.loads(path.read_text())
                if 'case' not in data or data.get('plugin')!=name:continue
                candidates[0].max_size=data['max_size']
                case,_=load_corpus(path,candidates[0]);check(case,str(path.relative_to(ROOT)));corpora+=1
        results.append({'plugin':name,'random_cases':300,'corpus_cases':corpora,'route_checks':checks,'changed_results':0})
        print(json.dumps(results[-1]),flush=True)
        (scratch/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
        shutil.rmtree(scratch/name)
    shutil.rmtree(base)
if __name__=='__main__':main()
