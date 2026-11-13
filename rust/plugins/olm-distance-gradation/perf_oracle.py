"""Bounded performance regression corpus; original failures remain failures."""
import copy
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'rust/tools/oracle'))
sys.path.insert(0,str(ROOT/'rust/plugins/olm-directional-blur'))
import olm_oracle as o
from perf_storage import install
install(o)
generate = o.generate_cases
def bounded(parameters, *args):
    parameters=copy.deepcopy(parameters)
    for p in parameters:
        if p['slot'] in (3,4): p['maximum']=128
        if p['slot']==12: p['maximum']=12
    return generate(parameters,*args)
o.generate_cases=bounded
if __name__=='__main__': raise SystemExit(o.main(sys.argv[1:]))
