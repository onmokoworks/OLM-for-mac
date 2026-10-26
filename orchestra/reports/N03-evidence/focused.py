"""Standard fuzz runner with Bilateral mode forced; other sampling unchanged.

Every depth is retained. Kernel size uses the ordinary small-control sampler.
Saved cases contain actual parameter values and inputs, so replay uses run.py.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter
import run
original=Adapter.generate
def generate(self,seed,index):
    case=original(self,seed,index)
    for p in case['parameters']:
        if p['slot']==11:p['value']=5
    return case
Adapter.generate=generate
if __name__=='__main__':sys.exit(run.main())
