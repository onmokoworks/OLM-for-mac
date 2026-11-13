"""Replay captured native projection calls and compare every post-call byte.
Uses record's alias-preserving contract and diverge's exact word comparator.
"""
import argparse,copy,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
TOOLS=HERE.parents[1]/'tools'
sys.path[:0]=[str(TOOLS/'record'),str(TOOLS/'diverge'),str(TOOLS/'autoport')]
from contract import witness_spec,checked_blob
import olm_diverge as d
import autoport as a
from process import witness_module

def run(capture,candidate,out):
    out.mkdir(parents=True,exist_ok=False);w=witness_module();rows=[]
    records=[json.loads(x) for x in (capture/'calls.jsonl').read_text().splitlines()]
    for index,rec in enumerate(records):
        if a.digest(rec['module'])!=rec['module_sha256']:raise ValueError('original drift')
        spec,regions=witness_spec(rec,capture)
        results={}
        for side in ['original','rust']:
            this=copy.deepcopy(spec)
            if side=='rust':this['module']=str(candidate);this['calls'][0]['rva']=hex(a.exported_rva(candidate,'autoport_18000a630'))
            dest=out/f'{index:03}-{side}';m=w.run(this,dest,timeout=30)
            if m['classification']!='success' or not m['process']['cleanup_verified']:raise RuntimeError(m)
            result=json.loads((dest/'result.json').read_text())['calls'][0]
            checks=[d.compare_bytes(bytes.fromhex(rec['return']['bits_le']),bytes.fromhex(result['return']['bits_le']),'f32',[1])]
            for b in rec['buffers']:
                start=int(b['address'],0);j=next(j for j,(s,e) in enumerate(regions) if s<=start and start+b['size']<=e);off=start-regions[j][0]
                actual=(dest/result['buffers'][f'b{j}']).read_bytes()[off:off+b['size']]
                checks.append(d.compare_bytes(checked_blob(capture,b,'after'),actual,'f32',[b['size']//4]))
            results[side]=checks
        rows.append({'record':index,'exact':all(c['status']=='exact' for v in results.values() for c in v),'comparisons':results})
    a.write(out/'summary.json',{'candidate_sha256':a.digest(candidate),'records':rows,'exact':bool(rows) and all(r['exact'] for r in rows)})
    print(f"{sum(r['exact'] for r in rows)}/{len(rows)} captured calls exact against both original and Rust")
    return int(not rows or not all(r['exact'] for r in rows))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);x=p.parse_args();raise SystemExit(run(x.capture.resolve(),x.candidate.resolve(),x.out.resolve()))
