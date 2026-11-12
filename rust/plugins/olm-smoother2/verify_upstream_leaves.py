"""Reproducible binary-grounded witness maps; no shared-tool source edits."""
from pathlib import Path
import copy, hashlib, json, random, struct, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = HERE / 'upstream-work'
ORIGINAL = ROOT.parent / 'upstream_20261112/extracted/OLMSmoother2AE/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex'
CANDIDATE = Path('D:/olm-rs-target/Up-smoother2/release/examples/upstream_witness.dll')
sys.path.insert(0, str(ROOT / 'rust/tools/diverge'))
import olm_diverge as d

def ptr(name, offset=0): return dict(type='ptr', buffer=name, offset=offset)
def scalar(kind, value): return dict(type=kind, value=value)
def save(path, obj): path.write_text(json.dumps(obj, indent=2), encoding='utf-8')

def main():
    rng = random.Random(20261112)
    values = [(0.,0.,0.,0.), (1.,1.,1.,1.), (1.,0.,0.,1.), (0.,1.,0.,.5), (0.,0.,1.,1.)]
    values += [tuple(rng.uniform(-2,4) for _ in range(4)) for _ in range(123)]
    raw = b''.join(struct.pack('<4f', *v) for v in values)
    buffers = {'input':dict(size=len(raw),hex=raw.hex()),'output':dict(size=16)}
    ref = dict(schema_version=1,module=str(ORIGINAL),fma='fma',buffers=copy.deepcopy(buffers),calls=[])
    cand = dict(schema_version=1,module=str(CANDIDATE),fma='fma',buffers=copy.deepcopy(buffers),calls=[])
    stages=[]
    for name,rva in [('to_oklab','0x5520'),('from_oklab','0x5840')]:
        for i in range(len(values)):
            idx=len(ref['calls']);args=[ptr('output'),ptr('input',16*i)]
            ref['calls'].append(dict(rva=rva,args=args,return_type='void'))
            ref['calls'][-1]['return']=ref['calls'][-1].pop('return_type')
            cand['calls'].append(dict(export=name,args=copy.deepcopy(args),**{'return':'void'}))
            stages.append(dict(id=f'{name}-{i}',dtype='f32',shape=[4],grounding=f'new AEX {rva}, two RGBA float pointers; alpha copied',reference=dict(call=idx,buffer='output'),candidate=dict(call=idx,buffer='output')))
    case=dict(schema_version=1,stateless_calls=True,scope='Isolated new Oklab transforms on 128 signed/HDR RGBA vectors each; no whole-frame claim',reference=dict(sha256=d.witness.sha256(ORIGINAL),expected_fma=1,witness=ref),candidate=dict(sha256=d.witness.sha256(CANDIDATE),expected_fma=1,witness=cand),stages=stages)
    save(WORK/'leaves-map.json',case)
    # Recorded real-render import provider and 4 calls of each matrix routine.
    profile=dict(schema_version=1,module_sha256=d.witness.sha256(ORIGINAL),functions=[],imports=[dict(name='cbrtf',args=['f32'],**{'return':'f32'},max_calls=12)])
    for name,rva in [('to_oklab','0x5520'),('from_oklab','0x5840')]:
        profile['functions'].append(dict(name=name,rva=rva,args=['ptr','ptr'],**{'return':'void'},max_calls=4,buffers=[dict(arg=0,size=16,stride=4,role='output'),dict(arg=1,size=16,stride=4,role='input')]))
    save(WORK/'record-profile.json',profile)
    save(WORK/'record-request.json',dict(schema_version=1,assignments=[dict(slot=7,value=3)]))
    print('Prepared 256 native transform comparisons and real-render recorder profile.')

if __name__=='__main__': main()
