"""Run the shared oracle, retaining its RNG stream and excluding Noise Type 3.

--cases is the number of admitted plans (first two are default/minimum).
Rejected plans are recorded verbatim; no numeric ranges are narrowed.
Point components are percentages, as interpreted by the AEXCompat host.
"""
from pathlib import Path
import importlib.util
import sys
sys.dont_write_bytecode=True

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'rust/tools/oracle'))
spec=importlib.util.spec_from_file_location('radial_oracle',ROOT/'rust/tools/oracle/olm_oracle.py')
oracle=importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)
sys.path.insert(0, str(Path(__file__).parent.parent/'olm-directional-blur'))
from perf_storage import install
install(oracle)
original_generate=oracle.generate_cases
excluded=[]

def generate(parameters,count,seed,sizes,downsample):
    pool=original_generate(parameters,max(100,count*8),seed,sizes,downsample)
    result=[]
    for case in pool:
        noise=next((a['value'] for a in case['assignments'] if a['slot']==25), 1)
        if noise==3:
            excluded.append({'reason':'Original uninitialised Type-3 destination / dirty lifecycle; C++ documented refusal', 'plan':case})
            continue
        result.append(case)
        if len(result)==count: break
    assert len(result)==count
    return result

if __name__=='__main__':
    oracle.generate_cases=generate
    try:
        code=oracle.main(sys.argv[1:])
    finally:
        if '--out' in sys.argv:
            out=Path(sys.argv[sys.argv.index('--out')+1])
            if out.exists(): oracle.write_json(out/'exclusions.json',{'wrapper':oracle.identity(__file__),'point_units':'percent of layer extent','excluded':excluded})
    raise SystemExit(code)
