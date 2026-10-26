#!/usr/bin/env python3
"""Replay Q02's case and force a neighbouring Smart workspace allocation."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import time
import subprocess
import sys
sys.dont_write_bytecode = True
import native_diff as nd

ROOT = Path(__file__).resolve().parents[2]
FORCED = r'''
static unsigned char adjacent_arena[256];
static bool force_next = false;
void* operator new(std::size_t n) {
    if (force_next) { force_next=false; return adjacent_arena+16; }
    if (void* p=std::malloc(n)) return p;
    throw std::bad_alloc();
}
void operator delete(void* p) noexcept { if (p!=adjacent_arena+16) std::free(p); }
void operator delete(void* p, std::size_t) noexcept { ::operator delete(p); }
int main() {
    unsigned refused=0, admitted=0; PF_Err first_error=0;
    for (int run=0;run<1000;++run) {
        std::memset(adjacent_arena,0,sizeof(adjacent_arena));
        PF_EffectWorld input{},output{};
        input.data=reinterpret_cast<PF_PixelPtr>(adjacent_arena+4);
        output.data=reinterpret_cast<PF_PixelPtr>(adjacent_arena+128);
        input.width=output.width=2;input.height=output.height=1;
        input.rowbytes=output.rowbytes=13;
        input.extent_hint=output.extent_hint={0,0,2,1};
        OLMColorKeyInfo info{};
        ColorKeyPreparedRender prepared{};
        force_next=true;
        PF_Err err=PrepareSmartRenderWorld(&input,&output,info,8,&prepared);
        force_next=false;
        if(err) { ++refused; if(!first_error) first_error=err; } else ++admitted;
    }
    std::printf("{\"refused\":%u,\"admitted\":%u,\"first_error\":%d}\n",refused,admitted,int(first_error));
}
'''


def check_differences(args, out):
    """Bind every native difference to its regenerated input and default AEX."""
    records = []
    for path in sorted(args.differences.glob('*.jsonl')):
        with path.open() as stream:
            records.extend(json.loads(line) for line in stream
                           if json.loads(line)['status'] == 'difference')
    if not records:
        print('{"differences": 0, "oracle_matches": 0}')
        return
    a = nd.adapter_at(ROOT, args.plugin, ROOT.parent.parent, 180)
    a.env.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    from run import default_worker
    pending = {}
    for r in records:
        if r['base']['status'] != 'refusal' or r['head']['status'] != 'ok':
            raise ValueError('Difference is not base refused / head rendered')
        pending.setdefault(r['case']['sequence_index'], []).append(r)
    checked = 0
    with (out/'oracle-differences.jsonl').open('w') as log:
        for case in nd.cases(a, 3000, 909):
            rows = pending.get(case['sequence_index'])
            if not rows:
                continue
            assert all({k: v for k, v in case.items() if k != 'pixels'} == r['case'] for r in rows)
            assert all(hashlib.sha256(case['pixels']).hexdigest() == r['input_sha256'] for r in rows)
            geometry = case.get('geometry_sampler', 'default')
            a.worker = (Path.home()/'.cache/olm-emu'/
                        ('worker-F53-geom' if geometry == 'realistic-v2' else 'worker-F52c-geom')/
                        'aex-guest-worker') if geometry != 'default' else default_worker()
            oracle, raw = a.oracle(case, out, time.monotonic()+180)
            sha = hashlib.sha256(raw).hexdigest()
            rect = oracle.get('output_rect', [0, 0, *case['geometry']])
            matches = oracle['status'] == 'ok' and all(
                r['head']['sha256'] == sha and r['head']['rect'] == rect for r in rows)
            log.write(json.dumps(dict(sequence=case['sequence_index'], oracle=oracle,
                sha256=sha, worker=str(a.worker), worker_sha256=nd.digest(a.worker),
                aex_sha256=nd.digest(a.aex), comparisons=len(rows), matches=matches))+'\n')
            log.flush()
            if not matches:
                raise ValueError('Newly admitted output differs from oracle')
            checked += len(rows)
    assert checked == len(records)
    print(json.dumps(dict(differences=len(records), oracle_matches=checked)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--revision')
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--forced',action='store_true')
    p.add_argument('--differences',type=Path)
    p.add_argument('--plugin',choices=nd.PLUGINS,default='olmcolorkey')
    args=p.parse_args();out=args.scratch.resolve()
    if not out.is_relative_to(ROOT/'orchestra/state'):p.error('scratch must be in orchestra/state')
    out.mkdir(parents=True,exist_ok=True)
    if args.differences:
        return check_differences(args, out)
    root=out/'source' if args.revision else ROOT
    if args.revision:nd.snapshot(args.revision,root)
    a=nd.adapter_at(root,'olmcolorkey',ROOT.parent.parent,180);a.reference_build=True
    a.env.update(TMPDIR=str(out),TMP=str(out),TEMP=str(out),MallocScribble='1',OLM_REFUSAL_TRACE=str(out/'refusal.trace'))
    original=a.compile
    if args.forced:
        def compile(argv,deadline):
            if str(argv[0])=='clang++' and '-o' in argv:
                host=out/'host.cpp'
                body=host.read_text().replace('int main(int argc, char **argv)','int unused_main(int argc, char **argv)')
                host.write_text(body+FORCED)
            return original(argv,deadline)
        a.compile=compile
    a.binary,_=a.build(out,time.monotonic()+300)
    if args.forced:
        result=json.loads(subprocess.check_output([a.binary],env=a.env,text=True))
        print(json.dumps(result,indent=2))
        if not args.revision and result['refused']:raise SystemExit(1)
        return
    case=next(c for c in nd.cases(a,3000,909) if c['sequence_index']==1932)
    pixels=case.pop('pixels')
    (out/'case.json').write_text(json.dumps(case,sort_keys=True,indent=2))
    input_hash=hashlib.sha256(pixels).hexdigest()
    if input_hash!='352bee204602201794b673362fc72b034b5ca3683aa58624425b78908a817866':
        raise ValueError('Q02 input binding changed')
    print('input_sha256',input_hash,flush=True)
    case['pixels']=pixels
    counts=Counter(); failures=0
    for i in range(1000):
        r=nd.render(a,case,out,'arm64',180)
        counts[json.dumps(r,sort_keys=True)]+=1
        failures += r['status']!='ok'
    print(json.dumps(dict(counts),indent=2))
    # Same default worker selection as tools/fuzz/run.py for realistic-v2.
    a.worker=Path.home()/'.cache/olm-emu/worker-F53-geom/aex-guest-worker'
    oracle,raw=a.oracle(case,out,time.monotonic()+180)
    result=dict(oracle=oracle,worker=str(a.worker),worker_sha256=nd.digest(a.worker),
                aex_sha256=nd.digest(a.aex),oracle_sha256=hashlib.sha256(raw).hexdigest(),
                matches_native=oracle['status']=='ok' and raw==(out/'output.raw').read_bytes()
                    and oracle.get('output_rect')==r['rect'])
    (out/'oracle.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not result['matches_native'] or failures:raise SystemExit(1)


if __name__=='__main__':main()
