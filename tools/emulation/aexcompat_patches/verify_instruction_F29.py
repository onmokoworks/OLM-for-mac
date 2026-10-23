#!/usr/bin/env python3
"""Compare full instruction matrices and independently check SDM NaN selection."""
import argparse
import collections
import json
from pathlib import Path


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--scratch',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    paths=[args.scratch/n for n in ('uc214.jsonl','uc215.jsonl','patched.jsonl')]
    matrices=[[json.loads(s) for s in p.read_text().splitlines()] for p in paths]
    assert all(len(m)==3200 for m in matrices)
    checks=collections.Counter(); disagreements=[]; first=None
    for old,worker,new in zip(*matrices):
        assert old==worker, 'Existing Unicorn variants differ'
        assert all(old[k]==new[k] for k in ('op','code','bits','a','b','rosetta'))
        assert new['equal'], new
        if not old['equal']:
            first=first or old
            disagreements.append(dict(old,patched=new['unicorn']))
        bits=old['bits']; size=bits//8
        if not old['op'].startswith(('add','sub','mul','div','sqrt')): continue
        lanes=128//bits if old['op'].endswith(('ps','pd')) else 1
        exponent=0x7f800000 if bits==32 else 0x7ff0000000000000
        fraction=0x7fffff if bits==32 else 0xfffffffffffff
        quiet=1<<(22 if bits==32 else 51)
        isnan=lambda x:(x&exponent)==exponent and bool(x&fraction)
        for lane in range(lanes):
            words=[int.from_bytes(bytes.fromhex(old[k])[lane*size:(lane+1)*size],'little') for k in ('a','b','rosetta')]
            a,b,ref=words
            if old['op'].startswith('sqrt'): a=b
            if not (isnan(a) or isnan(b)): continue
            expected=(a if isnan(a) else b)|quiet
            assert ref==expected,(old['op'],lane,hex(a),hex(b),hex(ref),hex(expected))
            checks[old['op']]+=1
    controls=[json.loads((args.scratch/f'controls-{variant}.json').read_text()) for variant in ('baseline','patched')]
    assert controls[0]['default_sse_addss']=='ffc12346'
    assert controls[1]['default_sse_addss']=='7fc12345'
    assert controls[0]['rows']==controls[1]['rows']
    assert all(c['x87_rows']==144 and c['x87_rosetta_differences']==0 for c in controls)
    report=dict(x87_rows_unchanged=144,x87_rosetta_disagreements=0,default_initialization_fixed=True,rows=3200,old_disagreements=len(disagreements),patched_disagreements=0,
        sdm_nan_lane_checks=sum(checks.values()),sdm_nan_lane_checks_by_op=checks,
        sdm_rosetta_disagreements=0,first_mismatch=first,
        source='Intel SDM Vol. 1 revision 090, Table 4-8 and section 4.8.3.5',
        source_url='https://cdrdv2-public.intel.com/874241/253665-090-sdm-vol-1.pdf',
        scope='MXCSR 0x1f80, output bits only. FMA/AVX not advertised by Rosetta; not executed. MIN/MAX use separate instruction rules, not Table 4-8.',
        disagreements=disagreements)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('disagreements','sdm_nan_lane_checks_by_op')},sort_keys=True))

if __name__=='__main__': main()
