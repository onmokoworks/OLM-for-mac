#!/usr/bin/env python3
"""S02: depth-stratified Smart float-colour campaign (original vs source host)."""
import argparse
import copy
import json
import os
import struct
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from adapters.olmsmoother2 import Adapter
from adapters.public import ROOT
from core import evaluate, sha, load_corpus


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker', type=Path, required=True)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--n', type=int, default=100)
    p.add_argument('--qualify-only', action='store_true')
    p.add_argument('--seeds', type=int, nargs='+', default=[1,2,3])
    a = p.parse_args()
    a.scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(a.scratch), TMP=str(a.scratch), TEMP=str(a.scratch))
    options = SimpleNamespace(max_size=256, case_timeout=10, main=ROOT.parent.parent,
                              worker=a.worker, color_sampler='float-v1')
    adapter = Adapter(options)
    adapter.routes = ('smart',)
    adapter.oracle_routes = {'smart':'smart'}
    deadline = time.monotonic()+7200
    summary = {'counts':{}, 'sensitive_cases':0, 'first_failure':None}
    with tempfile.TemporaryDirectory(dir=a.scratch) as td:
        directory = Path(td)
        summary['provenance'] = adapter.prepare(directory, deadline)
        byte_adapter = copy.copy(adapter)
        byte_adapter.color_sampler = 'default'
        for index in range(300):
            original = byte_adapter.generate(1,index)
            floated = adapter.generate(1,index)
            floated.pop('color_sampler')
            for param in floated['parameters']:
                param.pop('float_value',None)
            assert original == floated
        summary['sampler_base_unchanged'] = 300
        witness_path = ROOT/'tests/fuzz_corpus/olmsmoother2/seed1_case000067_65ee3b1d9cdf.json'
        witness, _ = load_corpus(witness_path,adapter)
        floats = {p['slot']:p['float_value'] for p in adapter.generate(1,67)['parameters'] if 'float_value' in p}
        for param in witness['parameters']:
            if param['kind']=='c':
                param['float_value'] = floats[param['slot']]
        summary['synthetic_A02h_witness'] = evaluate(adapter,witness,directory,deadline)
        summary['witness_scope'] = 'Original corpus pixels/parameters plus synthetic float-v1 suite values; actual AE values were not captured.'
        if a.qualify_only:
            summary['qualification'] = []
            for depth in (8,16,32):
                for fixture in ('key','invert','gamma'):
                    invert = int(fixture == 'invert')
                    case = byte_adapter.generate(1,0)
                    case.update(geometry=[3,3],depth=depth,profile='sdr',parameters=adapter.defaults(3,3))
                    fmt, top = {8:('B',255),16:('H',32768),32:('f',1.)}[depth]
                    low = (top/2 if depth==32 else top//2) if fixture=='gamma' else 0
                    case['pixels'] = b''.join(struct.pack('<4'+fmt,top,*([top if i%2 else low]*3)) for i in range(9))
                    for param in case['parameters']:
                        if param['slot']==1: param['value']=1
                        if param['slot']==2:
                            param['value']=[255,255,255,255]
                            param['float_value']=[1.,0.0005,0.0005,0.0005]
                        if param['slot']==3: param['value']=invert
                    if fixture=='gamma':
                        for param in case['parameters']:
                            param.pop('float_value',None)
                            if param['slot']==1: param['value']=0
                            if param['slot']==8: param['value']=2
                            if param['slot']==9: param['value']=2.4
                            if param['slot']==10: param['value']=1
                            if param['slot']==11:
                                param['value']=[255,255,0,0]
                                param['float_value']=[1.,low/top+0.0005,low/top+0.0005,low/top+0.0005]
                    result = evaluate(adapter,case,directory,deadline)
                    control = copy.deepcopy(case)
                    for param in control['parameters']: param.pop('float_value',None)
                    status, raw = adapter.oracle(control,directory,deadline,'smart')
                    sensitive = status['status']=='ok' and sha(raw)!=result['oracle'].get('raw_sha256')
                    summary['qualification'].append(dict(depth=depth,fixture=fixture,invert=invert,result=result,byte_control=status,byte_control_sha256=sha(raw),sensitive=sensitive))
            (a.scratch/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
            return int(summary['synthetic_A02h_witness']['routes']['smart']['status']!='exact' or not all(row['sensitive'] and row['result']['routes']['smart']['status']=='exact' for row in summary['qualification']))
        with (a.scratch/'cases.jsonl').open('w') as stream:
            for seed in a.seeds:
                counts = {depth:0 for depth in (8,16,32)}
                index = 0
                while min(counts.values()) < a.n:
                    case = adapter.generate(seed,index)
                    index += 1
                    depth = case['depth']
                    if counts[depth] >= a.n:
                        continue
                    counts[depth] += 1
                    result = evaluate(adapter,case,directory,deadline)
                    row = {'seed':seed,'index':case['index'],'depth':depth,
                           'pixels_sha256':sha(case['pixels']), 'parameters':case['parameters'],
                           'result':result}
                    # Paired original control proves some outputs actually depend on
                    # the independent suite values, not merely on byte parameters.
                    control = copy.deepcopy(case)
                    for param in control['parameters']:
                        param.pop('float_value',None)
                    status, raw = adapter.oracle(control,directory,deadline,'smart')
                    row['byte_control'] = status
                    row['byte_control_sha256'] = sha(raw)
                    if status['status']=='ok' and result['oracle']['status']=='ok' and sha(raw)!=result['oracle']['raw_sha256']:
                        summary['sensitive_cases'] += 1
                    key = f"seed{seed}/PF{depth}/"+result['routes']['smart']['status']
                    summary['counts'][key] = summary['counts'].get(key,0)+1
                    stream.write(json.dumps(row)+'\n'); stream.flush()
                    if sum(counts.values()) % 100 == 0:
                        print('progress', seed, counts, flush=True)
                    if result['routes']['smart']['status']!='exact' and summary['first_failure'] is None:
                        summary['first_failure'] = row
                print(seed, counts, summary['counts'], flush=True)
    (a.scratch/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return int(summary['first_failure'] is not None or summary['synthetic_A02h_witness']['routes']['smart']['status']!='exact')

if __name__=='__main__':
    raise SystemExit(main())
