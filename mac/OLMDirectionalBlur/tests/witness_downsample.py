#!/usr/bin/env python3
"""Typed downsample + partial request witnesses against the original F52 AEX."""
import argparse, json, os, struct, sys, time
from pathlib import Path
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from adapters.olmdirectionalblur import Adapter
from core import evaluate, sha
from run import main_checkout
p = argparse.ArgumentParser()
p.add_argument('--sanitize', action='store_true')
args = p.parse_args()
S = ROOT/'orchestra/state/P01b-directionalblur-downsample'/('witness-sanitized' if args.sanitize else 'witness')
S.mkdir(parents=True, exist_ok=True)
class WitnessAdapter(Adapter):
    def compile(self, argv, deadline):
        if args.sanitize and str(argv[0]) == 'clang++':
            argv = [*argv, '-fsanitize=address,undefined', '-fno-sanitize-recover=all']
        return super().compile(argv, deadline)
    routes = ('smart',)
    oracle_routes = {'smart': 'smart'}
    def geometry_host(self, body):
        body = super().geometry_host(body)
        marker = '#include "'+str(ROOT/'tools/fuzz/harnesses/geometry.hpp')+'"\n'
        return body.replace(marker, marker + r'''
#undef EffectMain
static PF_Err p01_entry(PF_Cmd cmd, PF_InData *in, PF_OutData *out,
    PF_ParamDef **params, PF_LayerDef *world, void *extra) {
    if (cmd == PF_Cmd_SMART_PRE_RENDER && std::getenv("P01_PARTIAL")) {
        auto *pre = static_cast<PF_PreRenderExtra *>(extra);
        pre->input->output_request.rect = PF_LRect{1, 1, 2, 2};
    }
    return f52_entry(cmd, in, out, params, world, extra);
}
#define EffectMain p01_entry
''')
    def session_arguments(self, case, directory):
        return ['--request-rect', '1,1,2,2'] if case['partial_request'] else []
a = WitnessAdapter(SimpleNamespace(max_size=64, case_timeout=10, main=main_checkout(),
    worker=Path.home()/'.cache/olm-emu/worker-F52-geom/aex-guest-worker'))
a.env.update(TMPDIR=str(S), TMP=str(S), TEMP=str(S),
    ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
deadline = time.monotonic()+600
a.binary, deps = a.build(S, deadline)
counts = {}; index = 0
with (S/'results.jsonl').open('w') as out:
    for depth in (8,16,32):
      for ds in (((1,2),(1,2)), ((1,3),(1,3)), ((1,8),(1,8)), ((1,2),(1,3))):
       for mode in ('fade', 'noise', 'truncate-to-zero'):
        for partial in (False,True):
            full = (39,27)
            w,h = [(n*r[0]+r[1]-1)//r[1] for n,r in zip(full,ds)]
            values = {1:37, 5:17, 6:9, 10:31, 11:7, 15:0}
            if mode == 'noise': values.update({3:23, 7:17, 12:31, 15:51, 16:2, 20:1})
            if mode == 'truncate-to-zero': values.update({5:1,6:0,10:1,11:0})
            params = a.defaults(w,h)
            for p in params:
                if p['slot'] in values:p['value'] = values[p['slot']]
            pixels = bytearray()
            for y in range(h):
                for x in range(w):
                    channels = [(x*31+y*47+17)%256, (x*13+y*7)%256,
                                (x*17+y*29)%256, (x*43+y*11)%256]
                    if depth==8: pixels.extend(channels)
                    elif depth==16: pixels.extend(struct.pack('<4H',*[v*128 for v in channels]))
                    else: pixels.extend(struct.pack('<4f',*[v/255 for v in channels]))
            case = dict(seed=20261024,index=index,depth=depth,full_geometry=full,
                        geometry=[w,h],downsample=ds,parameters=params,pixels=bytes(pixels),
                        input_padding=5,output_padding=11,partial_request=partial)
            if partial:a.env['P01_PARTIAL']='1'
            else:a.env.pop('P01_PARTIAL',None)
            result = evaluate(a,case,S,deadline)
            status=result['routes']['smart']['status'];counts[status]=counts.get(status,0)+1
            row={k:v for k,v in case.items() if k!='pixels'}
            row.update(mode=mode,input_sha256=sha(pixels),result=result)
            out.write(json.dumps(row)+'\n');out.flush();index+=1
summary=dict(counts=counts,n=index,worker_sha256=sha(a.worker.read_bytes()),
    aex_sha256=sha(a.aex.read_bytes()),candidate_sha256=sha(a.binary.read_bytes()),
    dependencies={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in
        [*deps,ROOT/'core/dblur_generic_budget.h',Path(__file__)]},
    scope='Partial request with full returned worlds; F52 does not negotiate cropped output worlds.')
(S/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(counts, flush=True)
assert counts=={'exact':72}, counts
