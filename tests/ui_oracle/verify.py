#!/usr/bin/env python3
"""Verify original UI fixtures; retain and separately report raw serializer tail differences."""
import argparse, copy, gzip, hashlib, json, struct
from pathlib import Path
HERE=Path(__file__).resolve().parent

def rows(path):
    opener=gzip.open if path.suffix=='.gz' else open
    with opener(path,'rt',encoding='utf-8') as f: return [json.loads(line) for line in f]

def active_ramp(parameter):
    data=parameter['value']['flat_bytes']
    assert len(data)==325 and data[0]==1, 'unrecognized original ramp serialization'
    n=int.from_bytes(bytes(data[1:5]),'little',signed=True)
    assert 0<=n<=16
    return data[:5+n*20]

def semantic(records):
    result=copy.deepcopy(records)
    for row in result:
        for side in ['before','after']:
            for p in row['event'][side]:
                value=p['value']
                if value and 'flat_bytes' in value:
                    # KiraKira schema: serialized version, count and active 20-byte records.
                    # Raw fixtures remain untouched. Inactive capacity is compared separately.
                    value['flat_bytes']=active_ramp(p)
    return result

def scalar(params,slot):
    p=params[slot-1];b=bytes(p['value']['bytes'])
    return struct.unpack('<d',b)[0] if p['type']==10 else int.from_bytes(b[:4],'little',signed=True)

def invariants(name,records):
    for row in records:
        e=row['event'];assert e['selector_error']==0
        before=e['before'];after=e['after'];v=lambda s:scalar(before,s)
        disabled=lambda s:bool(after[s-1]['ui_flags']&32)
        hidden=lambda s:after[s-1]['hidden']
        assert [p['name_bytes'] for p in before]==[p['name_bytes'] for p in after]
        if name=='ColorKeep-update':
            assert [hidden(s) for s in range(2,102)]==[i>=v(1) for i in range(100)]
        elif name=='Blur-update': assert hidden(2)
        elif name=='DirectionalBlur-update':
            assert hidden(17)==(v(16)!=3)
            assert all(hidden(s)==(v(16)==3) for s in [18,19,20])
        elif name=='DistanceGradation-update':
            for slot,want in {10:v(9)!=4,4:v(2)==1,3:v(2)==2,7:v(5)!=1,8:v(6)==0,12:v(11)==1}.items():assert disabled(slot)==want
        elif name=='KiraKira-update':
            for use,solid,ramp in [(13,11,14),(19,17,20),(25,23,26),(31,29,32),(37,35,38)]:
                assert disabled(solid)==bool(v(use));assert disabled(ramp)==(not v(use))
        elif name=='Smoother2-update':
            assert disabled(2)==(not v(1)) and disabled(3)==(not v(1))
            assert disabled(9)==(v(8)==1) and disabled(10)==(v(8)!=2)
            assert [hidden(s) for s in range(11,16)]==[not(v(8)==2 and i<v(10)) for i in range(5)]
        elif name=='RadialBlur-update':
            for slot in [5,6,11,12]:assert disabled(slot)==(v(1)!=2)
            for mode,strength in [(5,4),(11,10)]:assert disabled(strength)==(v(1)==2 and v(mode)==3)
            assert hidden(26)==(v(25)!=3)
            assert all(hidden(s)==(v(25)==3) for s in [27,28,29])
        elif name=='ColorKey-update':
            p,c,r,n=map(v,[7,8,23,22]);assert disabled(2)==bool(p or c)
            assert all(hidden(s)==(not(c and not p)) for s in [9,10,11])
            for i in range(25):
                base=24+8*i;use=v(base);replace=v(base+1)
                assert hidden(base)==(i>=n) and hidden(base+2)==(i>=n)
                assert disabled(base+2)==(not use)
                assert hidden(base+4)==(not(i<n and p and not c))
                assert all(hidden(s)==(not(i<n and p and c)) for s in range(base+5,base+8))
                assert hidden(base+1)==(not(i<n and r))
                assert hidden(base+3)==(not(i<n and r and replace))
                assert disabled(base+1)==(not use) and disabled(base+3)==(not use)
    def ramp(i,side='after',slot=14):return active_ramp(records[i]['event'][side][slot-1])
    def count(i):return int.from_bytes(bytes(ramp(i)[1:5]),'little')
    if name=='KiraKira-draw-click':assert count(0)==3 and count(1)==4
    if name=='KiraKira-drag-delete-20':assert count(-1)==3
    if name=='KiraKira-drag-delete-21':assert count(-1)==2
    if name=='KiraKira-picker-cancel':assert ramp(1,'before')==ramp(1)
    if name=='KiraKira-picker-accept':assert ramp(1,'before')!=ramp(1)
    if name=='KiraKira-copy-paste':assert ramp(-1,slot=20)==ramp(-1)
    if name=='KiraKira-randomize-flip':
        assert ramp(2,'before')!=ramp(2) and ramp(4,'before')!=ramp(4) and ramp(6,'before')!=ramp(6)
        assert records[6]['state_before']==records[6]['state_after']
    if name=='KiraKira-presets':assert ramp(7,'before')!=ramp(7)
    if name=='KiraKira-context-negative':assert all(not row['event']['calls'] for row in records)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--replay',type=Path);args=ap.parse_args()
    manifest=json.loads((HERE/'manifest.json').read_text());total=0;raw_different=[]
    if args.replay:
        summary=json.loads((args.replay/'summary.json').read_text())
        assert sorted(r['name'] for r in summary)==sorted(r['name'] for r in manifest['sessions'])
        assert all(r['returncode']==0 for r in summary), 'replay process/teardown failure'
        capture=json.loads((args.replay/'capture.json').read_text())
        assert capture['worker_sha256']==manifest['worker_sha256'], 'replay worker identity differs'

    for entry in manifest['sessions']:
        name=entry['name'];path=HERE/'witnesses'/(name+'.jsonl.gz')
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['compressed_sha256']
        request=HERE/'witnesses'/(name+'.request.json')
        assert hashlib.sha256(request.read_bytes()).hexdigest()==entry['request_sha256']
        expected=rows(path);assert len(expected)==entry['events'];invariants(name,expected);total+=len(expected)
        if args.replay:
            assert hashlib.sha256((args.replay/request.name).read_bytes()).hexdigest()==entry['request_sha256'],f'{name}: request changed'
            actual=rows(args.replay/(name+'.jsonl'));invariants(name,actual)
            assert semantic(expected)==semantic(actual),f'{name}: active payload/UI/draw mismatch'
            if expected!=actual:raw_different.append(name)
    print(json.dumps({'sessions':len(manifest['sessions']),'events':total,'mode':'replay' if args.replay else 'fixture_invariants','semantic_mismatches':0 if args.replay else None,'raw_tail_different_sessions':raw_different},sort_keys=True))
if __name__=='__main__':main()
