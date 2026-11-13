"""Crate-scoped upstream evidence. Sparse fixtures work around broker limits.

They are full-frame, downsample-1 renders; no ordinary-oracle or high-slot
assignment coverage is implied. Original modules are always used in place.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import sys
from concurrent.futures import ThreadPoolExecutor

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / 'rust/tools/oracle'), str(ROOT / 'rust/tools/scaffold')]
import olm_oracle as oracle
import olm_scaffold as scaffold
from PIL import Image

ORIGINALS = {str(y): ROOT.parent / f'upstream_20261112/extracted/OLMColorKey/OLMColorKey/Plugins/64/{y}/OLMColorKey.aex' for y in (2025, 2026)}
ORIGINALS['old'] = ROOT.parent / 'ghidra_windows_aex/OLMColorKey.aex'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inventory(candidate, out):
    probe = ROOT / 'rust/tools/scaffold/local/all-ten-final/probe/capture.aex'
    captures, inventories = {}, {}
    for name, aex in dict(ORIGINALS, candidate=candidate).items():
        folder = out / name
        folder.mkdir()
        inv = oracle.inspect(oracle.DEFAULT_HARNESS, aex, 60)
        oracle.write_json(folder / 'inventory.json', inv)
        env = {'OLM_SCAFFOLD_ORIGINAL': str(aex), 'OLM_SCAFFOLD_ENTRY': 'entry_point',
               'OLM_SCAFFOLD_CAPTURE': str(folder / 'declarations.json')}
        process = oracle.run_process([oracle.DEFAULT_HARNESS, '--headless', '--inspect-experimental-with-deps', probe, aex.parent], 60, env)
        oracle.write_json(folder / 'process.json', process)
        if process['returncode'] != 0:
            raise RuntimeError(process)
        cap = json.loads((folder / 'declarations.json').read_text(encoding='utf-8'))
        scaffold.validate_capture(inv, cap)
        captures[name], inventories[name] = cap, inv
    report = {
        'sha256': {name: sha(p) for name, p in dict(ORIGINALS, candidate=candidate, harness=oracle.DEFAULT_HARNESS).items()},
        'controls': len(captures['candidate']['params']),
        'raw_declarations_equal_2025': captures['2025'] == captures['candidate'],
        'raw_declarations_equal_2026': captures['2026'] == captures['candidate'],
        'public_parameters_equal': inventories['2025']['parameters'] == inventories['candidate']['parameters'],
        'pipl_bytes_equal_2025': scaffold.resources(ORIGINALS['2025'])[0]['bytes'] == scaffold.resources(candidate)[0]['bytes'],
        'declaration_differences': [(a['slot'], [k for k in a if a[k] != b.get(k)]) for a,b in zip(captures['2025']['params'], captures['candidate']['params']) if a != b],
        'old_slot_ids_types_preserved': all(a['fields']['uu.id'] == b['fields']['uu.id'] and a['fields']['param_type'] == b['fields']['param_type'] for a,b in zip(captures['old']['params'], captures['candidate']['params'])),
    }
    oracle.write_json(out / 'summary.json', report)
    print(json.dumps(report, indent=2))

def fixture_case(candidate, original, out, case, parameters):
    folder = out / f"{case['index']:04}-{case['depth']}"
    folder.mkdir()
    Image.fromarray(oracle.input_pixels(*case['size'], case['seed']), 'RGBA').save(folder / 'input.png')
    fixture = {'schema': 'aexcompat.render_fixture', 'schema_version': 1,
               'primary_layer': 'input.png', 'parameters': parameters,
               'pixel_format': {8:'argb8',16:'argb16',32:'argb32f'}[case['depth']],
               'render_path':'smart', 'premultiplication':'straight',
               'timing': {'current_time':0,'time_step':1,'total_time':1,'time_scale':1},
               'final_artifact':'raw', 'checkpoints':[{'id':'output_world','stage':'smart-output'}]}
    oracle.write_json(folder / 'fixture.json', fixture)
    oracle.write_json(folder / 'case.json', case)
    processes = {}
    for label, aex in [('reference',original),('candidate',candidate)]:
        process = oracle.run_process([oracle.DEFAULT_HARNESS,'--headless','--render-fixture',aex,folder/'fixture.json',folder/label],60)
        oracle.write_json(folder / f'{label}-process.json', process)
        processes[label] = process['returncode']
    result = dict(case, processes=processes)
    if any(processes.values()):
        result['status'] = 'incomplete'
    else:
        a, b = [(folder/label/'final/output.bin').read_bytes() for label in ['reference','candidate']]
        result.update(status='exact' if a == b else 'mismatch', reference_sha256=hashlib.sha256(a).hexdigest(), candidate_sha256=hashlib.sha256(b).hexdigest())
    oracle.write_json(folder / 'comparison.json', result)
    return result

def sparse(candidate, out, seed, cases, year):
    original = ORIGINALS[str(year)]
    inv = oracle.inspect(oracle.DEFAULT_HARNESS, original, 60)
    oracle.write_json(out/'inventory.json', inv)
    slots = {p['slot']:p for p in inv['parameters']}
    rng = random.Random(seed)
    plans = []
    # Global controls plus eight complete palettes through color 125 (slot 1023).
    # Later colors retain upstream defaults; no assignment exceeds broker MAX_PARAMETERS.
    palette = [0, 1, 24, 25, 98, 99, 100, 124]
    for index in range(cases):
        changes = {}
        if index:
            for slot in [1,2,4,5,6,7,8,9,10,11,14,15,18,19,20,22,23]:
                p = slots[slot]
                if index == 1: value = p['minimum']
                elif index == 2: value = p['maximum']
                elif p['kind'] == 'float': value = rng.choice([0.0,p['maximum'],rng.uniform(p['minimum'],p['maximum'])])
                else: value = rng.randint(int(p['minimum']),int(p['maximum']))
                changes[slot] = dict(p, value=value)
            for n in palette:
                for j in range(8):
                    slot = 24 + n*8+j
                    p = slots[slot]
                    if p['kind'] == 'color':
                        color = rng.choice([[255,0,0,0],[255,255,255,255],[255,*[rng.randrange(256) for _ in range(3)]]])
                        changes[slot] = dict(p,color=color)
                    else:
                        value = rng.randint(0,1) if p['kind']=='integer' else rng.choice([0.0,1.0,rng.random()])
                        changes[slot] = dict(p,value=value)
        size = [(1,1),(3,7),(11,7),(31,19)][index%4]
        for depth in (8,16,32):
            plans.append((dict(index=index,depth=depth,seed=seed+index,size=size,kind=['default','minimum','maximum'][index] if index<3 else 'random',downsample=1), list(changes.values())))
    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(fixture_case,candidate,original,out,case,params) for case,params in plans]
        for n,future in enumerate(futures,1):
            results.append(future.result())
            if n%30 == 0: print(f'{n}/{len(plans)}',flush=True)
    report = {'seed':seed,'year':year,'cases_per_depth':cases,'random_per_depth':max(0,cases-3),
              'downsample':[1],'assignment_slots_max':1023,'palette_indices_1_based':[n+1 for n in palette],
              'sha256':{'original':sha(original),'candidate':sha(candidate),'harness':sha(oracle.DEFAULT_HARNESS)},
              'counts':{str(d):{s:sum(r['depth']==d and r['status']==s for r in results) for s in ('exact','mismatch','incomplete')} for d in (8,16,32)},'results':results}
    oracle.write_json(out/'summary.json',report)
    print(json.dumps(report['counts'],indent=2))
    return 0 if all(r['status']=='exact' for r in results) else 2

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['inventory','sparse'])
    p.add_argument('--candidate',type=Path,default=HERE/'validation/OLMColorKey.aex')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seed',type=int,default=20261113)
    p.add_argument('--cases',type=int,default=103)
    p.add_argument('--year',type=int,choices=[2025,2026],default=2025)
    args=p.parse_args();args.out=args.out.resolve();args.out.mkdir(parents=True,exist_ok=False)
    if args.mode=='inventory': inventory(args.candidate.resolve(),args.out)
    else: sys.exit(sparse(args.candidate.resolve(),args.out,args.seed,args.cases,args.year))
