#!/usr/bin/env python3
"""Independent negative-phase index boundaries and original-AEX noise plane.

NumPy's MT19937 integer stream predicts table-index validity independently of
the C++ port. Each signed-fixed boundary is found by binary search, then both
adjacent values are exercised. Undefined original table reads never justify
admission; those cases must refuse cleanly without publishing output.
"""

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")
import argparse
import json
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
import numpy as np
import capstone
import pefile
from PIL import Image
from adapters.radialblur import Adapter, public
from core import sha, raw_diff
import probe_radialblur_zoom_fade_20261002 as zoom
from verify_radialblur_smart_C06 import ROOT, MAIN, WORKER

f32 = lambda v: struct.unpack('<f', struct.pack('<f', v))[0]
bits = lambda v: struct.pack('<f', v).hex()


def index_boundary(w, h, thickness, seed):
    inverse = f32(1/f32(thickness))
    dims = [int(f32(f32(v*inverse)+3)) for v in (w,h)]
    draws = np.random.RandomState(seed).randint(0, 2**32, 101+2*dims[0]*dims[1], dtype=np.uint32)
    positions = [f32(f32(f32(int(v))/4294967296.)*100.) for v in draws[102::2]]

    def inspect(raw):
        phase = f32(raw*2.663161090079238e-7)
        indices = [int(f32(v+phase)) for v in positions]
        return dict(raw=raw, phase_le_hex=bits(phase), min_index=min(indices),
                    first_invalid=next((i for i,v in enumerate(indices) if v<0 or v>=100), None),
                    defined=all(0<=v<100 for v in indices), dimensions=dims)

    low, high = -2147483648, 0
    assert not inspect(low)['defined'] and inspect(high)['defined']
    while high-low > 1:
        middle = (low+high)//2
        if inspect(middle)['defined']: high=middle
        else: low=middle
    return high, inspect


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--skip-plane-trace', action='store_true', help='Only run the public typed matrix; old F32 trace CLI cannot set AD angles')
    ap.add_argument('--worker', type=Path, default=WORKER)
    ap.add_argument('--source', type=Path, default=public.SOURCE)
    ap.add_argument('--core', type=Path, default=ROOT/'core/dblur_noise.h')
    ap.add_argument('--all-depths', action='store_true', help='Also measure the unpromoted PF32 experiment')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out), OLM_RADIAL_CANDIDATE_SANITIZE='1')
    public.SOURCE = args.source.resolve()
    adapter = Adapter(SimpleNamespace(main=MAIN, worker=args.worker, max_size=256, case_timeout=60))
    deadline = time.monotonic()+3600
    report = dict(provenance=adapter.prepare(out,deadline), core_sha256=sha(args.core.read_bytes()),
                  rows=[], failures=[])
    work = out/'case'; work.mkdir()
    trace_case = None
    for w,h in ((3,5),(11,7)):
        for seed in (1,17):
            thickness = 3 if seed==1 else 10
            boundary, inspect = index_boundary(w,h,thickness,seed)
            for variant, raw_phase in enumerate((-1, -30*65536, boundary-1, boundary, boundary+1, -2147483648)):
                domain = inspect(raw_phase)
                for depth in ((8,16,32) if args.all_depths else (8,16)):
                    rng = random.Random(11300+w*100+h+depth)
                    packed = b''.join(bytes([rng.choice([0,128,255]),*[rng.randrange(256) for _ in range(3)]]) for _ in range(w*h))
                    pixels = (packed if depth==8 else b''.join(struct.pack('<H',int(v/255*32768)) for v in packed)
                              if depth==16 else b''.join(struct.pack('<f',v/255) for v in packed))
                    for family in (1,2):
                        changes = {1:family, 4:4, 10:3 if variant%2 else 0, 7:25 if variant%2 else 0,
                                   15:variant%2, 20:1, 22:25 if variant%2 else 0,
                                   24:50, 25:1 if variant%2 else 2, 27:seed, 28:raw_phase/65536, 29:thickness}
                        params = adapter.defaults(w,h)
                        for p in params:
                            if p['slot'] in changes:p['value']=changes[p['slot']]
                        case = dict(geometry=[w,h], depth=depth, profile='sdr', parameters=params,
                                    pixels=pixels, input_padding=0, output_padding=0)
                        oracle, reference = adapter.oracle(case,work,deadline,'smart')
                        oracle = dict(oracle, raw_sha256=sha(reference))
                        row = dict(index=len(report['rows']),case={k:v for k,v in case.items() if k!='pixels'},
                                   input_sha256=sha(pixels),domain=domain,oracle=oracle,layouts=[])
                        for ip,op in ((0,0),(1,5),(3,11)):
                            actual, rendered, guards = adapter.candidate(dict(case,input_padding=ip,output_padding=op),work,'smart',deadline)
                            exact = oracle['status']==actual['status']=='ok' and rendered==reference
                            clean = not actual.get('sanitizer')
                            passed = clean and (exact if domain['defined'] else actual['status']=='refusal' and not rendered)
                            layout = dict(input_padding=ip,output_padding=op,actual=actual,raw_sha256=sha(rendered),
                                          guards=guards,exact=exact,clean=clean,passed=passed)
                            if actual['status']==oracle['status']=='ok' and not exact:layout['diff']=raw_diff(reference,rendered,depth)
                            row['layouts'].append(layout)
                            if not passed:report['failures'].append(dict(index=row['index'],layout=ip))
                        report['rows'].append(row)
                        if trace_case is None and w==11 and seed==17 and variant==3 and depth==8 and family==1:
                            trace_case = (case,domain,oracle)
                        print('ROW',row['index'],'defined',domain['defined'],[x['passed'] for x in row['layouts']],flush=True)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.skip_plane_trace:
        report['plane_trace'] = 'not requested; public raw typed matrix only'
        report['status'] = 'pass' if not report['failures'] else 'fail'
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        shutil.rmtree(out/'build')
        print('RESULT',report['status'],'rows',len(report['rows']),'failures',len(report['failures']),flush=True)
        return bool(report['failures'])
    # One boundary-adjacent defined negative phase, bound to the full Smart output.
    case, domain, oracle = trace_case
    image = Image.new('RGBA',tuple(case['geometry']))
    image.putdata([(r,g,b,a) for a,r,g,b in struct.iter_unpack('4B',case['pixels'])])
    image.save(out/'input.png')
    count = domain['dimensions'][0]*domain['dimensions'][1]
    command = [str(args.worker),'render-trace-png',str(adapter.aex),str(out/'input.png'),str(out/'trace.png'),
               '--pixel-format','argb8','--watch','function=0x9680,arg=rcx,size=72,occurrence=1',
               '--watch',f'function=0x9680,arg=rcx,deref=8,size={count*4},occurrence=1',*zoom.assignments(case)]
    run = subprocess.run(command,capture_output=True,check=True,timeout=120)
    trace = json.loads(run.stdout)
    (out/'trace.json').write_bytes(run.stdout)
    assert trace['raw_pixel_sha256']==oracle['raw_sha256'] and trace['guards_intact'] and not trace['render_error']
    assert not trace['unsupported_suite_calls'] and not trace['dropped_unsupported_suite_calls']
    stage = next(t for t in trace['execution_traces'] if t['selector']=='SMART_RENDER')
    assert not stage['truncated'] and not stage['dropped_memory_witnesses']
    watches = {w['watch_id']:w for w in stage['memory_witnesses']}
    native = bytes.fromhex(watches['watch-2']['before']['hex'])
    header = args.core.resolve()
    harness = (ROOT/'tools/emulation/radialblur_noise_plane_harness_20261001.cpp').read_text()
    harness = harness.replace('../../core/dblur_noise.h',str(header))
    (out/'plane.cpp').write_text(harness)
    subprocess.run([_UCRT_CXX,'-std=c++17','-O2','-fno-fast-math','-ffp-contract=off',str(out/'plane.cpp'),'-o',str(out/'plane')],capture_output=True,check=True)
    fields = {p['slot']:p['value'] for p in case['parameters']}
    mac = subprocess.run([str(out/'plane'),*map(str,case['geometry']),f'{struct.unpack("<I",struct.pack("<f",fields[29]))[0]:08x}',
                          f'{int.from_bytes(bytes.fromhex(domain["phase_le_hex"]),"little"):08x}',str(fields[27])],capture_output=True,check=True)
    report['plane'] = dict(domain=domain,input_sha256=sha(case['pixels']),case=case|{'pixels':case['pixels'].hex()},
                           original_raw_sha256=oracle['raw_sha256'],native_sha256=sha(native),mac_sha256=sha(mac.stdout),
                           exact=mac.stdout==native,words=count,native_hex=native.hex(),mac_hex=mac.stdout.hex())
    pe = pefile.PE(str(adapter.aex)); base=pe.OPTIONAL_HEADER.ImageBase
    decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
    report['noise_builder_static']=[dict(rva=hex(i.address-base),bytes=i.bytes.hex(),instruction=i.mnemonic+' '+i.op_str)
                                    for i in decoder.disasm(pe.get_data(0x9380,0x300),base+0x9380)]
    if mac.stdout!=native:report['failures'].append('paired_noise_plane')
    report['status']='pass' if not report['failures'] else 'fail'
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.rmtree(out/'build'); (out/'plane').unlink()
    print('RESULT',report['status'],'rows',len(report['rows']),'failures',len(report['failures']),flush=True)
    return bool(report['failures'])


if __name__=='__main__':raise SystemExit(main())
