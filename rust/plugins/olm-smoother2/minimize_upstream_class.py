"""Use shared float-input minimization with a four-byte classifier output.

The shared reducer unnecessarily requires float *outputs*. Its input validation
already enforces identical whole-float buffers. Adapt only that guard locally;
keep native execution, bit comparison, budgets and replay unchanged.
"""
import hashlib,inspect,sys
from verify_upstream_leaves import ROOT,WORK,save
sys.path.insert(0,str(ROOT/'rust/tools/diverge'))
import minimize

def main():
    source=inspect.getsource(minimize.minimize)
    old="case['stages'][0]['dtype'] != 'f32'"
    assert source.count(old)==1
    namespace=dict(minimize.__dict__)
    exec(source.replace(old,"case['stages'][0]['dtype'] not in ('f32', 'u8')"),namespace)
    report=namespace['minimize'](WORK/'old-new-class/reproducer.json',WORK/'old-new-class-minimized-v2',budget=64)
    save(WORK/'minimizer-adaptation.json',dict(shared_source_sha256=hashlib.sha256(source.encode()).hexdigest(),change='Allow u8 output; f32 input checks, bounds, equality, process ownership unchanged',result=report))
    print({k:v for k,v in report.items() if k!='attempts'})

if __name__=='__main__':main()
