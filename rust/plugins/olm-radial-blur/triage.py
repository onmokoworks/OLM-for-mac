"""Replay saved mismatches, preserving artifacts and testing reference stability."""
import argparse
import concurrent.futures
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
sys.dont_write_bytecode=True

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('oracle',ROOT/'rust/tools/oracle/olm_oracle.py')
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)

def digest_output(directory,side,route):
    data=oracle.load_output(directory/f'{side}.png',oracle.ROUTES[route][0])
    return hashlib.sha256(data.tobytes()).hexdigest()

def one(source,out,candidate,repeats):
    source=source.resolve(); manifest=json.loads((source/'case.json').read_text())
    route=manifest['route']
    for side in ['reference','harness']:
        assert oracle.sha256(manifest[side]['path'])==manifest[side]['sha256']
    before=copy.deepcopy(manifest)
    if candidate: manifest['candidate']=oracle.identity(candidate)
    original=[digest_output(source,'reference',route)]
    rust=[];rows=[]
    if before['candidate']['sha256']==manifest['candidate']['sha256']:
        rust.append(digest_output(source,'candidate',route))
    for number in range(repeats):
        directory=out/f'{source.parent.name}-{source.name}-{number}'
        directory.mkdir()
        for relative,expected in manifest['assets'].items():
            asset=(source/relative).resolve();assert asset.is_relative_to(source)
            assert oracle.sha256(asset)==expected
            dest=directory/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(asset,dest)
        manifest['triage_source']=str(source);manifest['triage_tool']=oracle.identity(__file__)
        oracle.write_json(directory/'case.json',manifest)
        row=oracle.evaluate_case(directory,manifest,600);rows.append(row)
        if row['processes']['reference']['ok']: original.append(digest_output(directory,'reference',route))
        if row['processes']['candidate']['ok']: rust.append(digest_output(directory,'candidate',route))
    result={'source':str(source),'route':route,'baseline_candidate':before['candidate'],'replay_candidate':manifest['candidate'],
            'reference_output_hashes':original,'candidate_output_hashes':rust,'reference_unique':len(set(original)),
            'candidate_unique':len(set(rust)),'replays':rows,
            'all_replays_succeeded':all(r['processes'][side]['ok'] for r in rows for side in ['reference','candidate']),
            'has_exact_replay':any(r['status']=='exact' for r in rows)}
    result['classification']='reference_nondeterministic' if len(set(original))>1 else 'unresolved' if any(r['status']!='exact' for r in rows) else 'exact_on_replay'
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('sources',type=Path,nargs='+');ap.add_argument('--out',type=Path,required=True);ap.add_argument('--candidate',type=Path);ap.add_argument('--repeats',type=int,default=3)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    directories=[]
    for source in args.sources:
        if (source/'case.json').exists(): directories.append(source)
        else:
            summary=json.loads((source/'summary.json').read_text())
            directories.extend(source/r['directory'] for r in summary['results'] if r['status']=='mismatched')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(one,s,args.out,args.candidate,args.repeats) for s in directories]
        rows=[]
        for f in concurrent.futures.as_completed(futures):
            r=f.result();rows.append(r);print(r['source'],r['classification'],r['reference_unique'],flush=True)
            oracle.write_json(args.out/'summary.json',{'results':rows,'complete':False})
    oracle.write_json(args.out/'summary.json',{'results':rows,'complete':True})
