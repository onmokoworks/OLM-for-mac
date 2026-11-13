"""Old-domain range comparison and nontrivial Oklab/gamma fractional probes."""
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import copy,json,sys
from pathlib import Path
from verify_upstream_leaves import ROOT,WORK,ORIGINAL,save
sys.path.insert(0,str(ROOT/'rust/tools/oracle'))
import olm_oracle as o

def run(name,reference,candidate,cases):
    out=WORK/name;out.mkdir(exist_ok=False)
    identities={k:o.identity(v) for k,v in dict(reference=reference,candidate=candidate,harness=o.DEFAULT_HARNESS,tool=o.__file__).items()}
    save(out/'cases.json',cases)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(o.run_case,out,c,r,identities,(),None,120) for c in cases for r in ['smart8','smart16','smart32']]
        rows=[f.result() for f in futures]
    report=dict(identities=identities,rows=rows,counts=dict(Counter(r['status'] for r in rows)))
    save(out/'summary.json',report);print(name,report['counts'],flush=True)
    return report

def main():
    inv=json.loads((WORK/'smoke/reference.inventory.json').read_text())
    baseline=o.generate_cases(inv['parameters'],1,20261118,[(31,19)],['1'])[0]
    old_cases=[]
    for version in (1,2):
        for value in (0,1,2,3,50,100):
            c=copy.deepcopy(baseline);c.update(index=len(old_cases),assignments=[dict(slot=7,value=version),dict(slot=6,value=value)])
            c['untouched_defaults']=[v for v in c['untouched_defaults'] if v['slot'] not in (6,7)]
            old_cases.append(c)
    old=ROOT.parent/'ghidra_windows_aex/OLMSmoother2.aex'
    report=run('old-domain',old,ORIGINAL,old_cases)
    assert set(report['counts'])<={'exact','mismatched'}
    cases=[]
    for value in (.1,1.7,2.9):
        for mode in (1,2,3):
            c=copy.deepcopy(baseline);c.update(index=len(cases),assignments=[dict(slot=7,value=3),dict(slot=6,value=value),dict(slot=8,value=mode),dict(slot=9,value=2.4),dict(slot=10,value=5)])
            c['untouched_defaults']=[v for v in c['untouched_defaults'] if v['slot'] not in (6,7,8,9,10)]
            cases.append(c)
    report=run('oklab-gamma',ORIGINAL,WORK/'OLMSmoother2-final.aex',cases)
    assert report['counts']=={'exact':27}
    # Same source/range and only gamma settings vary. Check all raw output bits.
    for start in (0,3,6):
        for route,depth in [('smart8',8),('smart16',16),('smart32',32)]:
            outputs=[o.load_output(WORK/'oklab-gamma'/f'case-{i:04d}-{route}'/'reference.png',depth) for i in range(start,start+3)]
            assert all((v==outputs[0]).all() for v in outputs[1:])
    save(WORK/'oklab-gamma-invariance.json',dict(exact=True,range_values=[.1,1.7,2.9],gamma_modes=[1,2,3],depths=[8,16,32]))

if __name__=='__main__':main()
