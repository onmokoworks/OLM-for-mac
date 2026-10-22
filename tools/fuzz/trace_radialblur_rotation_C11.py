#!/usr/bin/env python3
"""Reduce and trace C11 Rotation against the pinned original Smart worker."""
import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
from adapters.radialblur import Adapter, public
from core import evaluate, shrink, sha
import probe_radialblur_rotation_fields_20261001 as fields
import probe_radialblur_zoom_fade_20261002 as zoom
from PIL import Image
import capstone
import pefile

ROOT = Path(__file__).resolve().parents[2]
WORKER = Path('/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, default=public.SOURCE)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--index', type=int, default=67)
    ap.add_argument('--fixture', type=Path)
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C11-radial-smart-r2')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    public.SOURCE = args.source.resolve()
    main = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT
    adapter = Adapter(SimpleNamespace(main=main, worker=WORKER, max_size=256, case_timeout=60))
    adapter.routes = ('smart',)
    adapter.oracle_routes = {'smart': 'smart'}
    deadline = time.monotonic()+2400
    provenance = adapter.prepare(out, deadline)
    if args.fixture:
        saved = json.loads(args.fixture.read_text())
        case = dict(saved['case'], pixels=bytes.fromhex(saved['input_hex']))
        reduction = {'fixture': str(args.fixture)}
        result = evaluate(adapter, case, out, deadline)
    else:
        case = adapter.generate(args.seed, args.index)
        result = evaluate(adapter, case, out, deadline)
        case, result, reduction = shrink(adapter, case, result, out, deadline, 96)
    report = dict(provenance=provenance, case={k:v for k,v in case.items() if k!='pixels'},
                  input_hex=case['pixels'].hex(), result=result, reduction=reduction)
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    assert case['depth'] == 8 and next(p['value'] for p in case['parameters'] if p['slot']==1) == 2
    public.initial.ROOT = main
    public.initial.AEX = adapter.aex
    hp = out/'planes.cpp'; hp.write_text(fields.plane_harness())
    old = public.initial.HARNESS; public.initial.HARNESS = hp
    binary = public.build(out/'planes_build', public.SOURCE.read_text())
    public.initial.HARNESS = old
    planes = out/'mac'; planes.mkdir()
    config = out/'parameters.txt'; config.write_text(public.initial.config_text(case))
    run = subprocess.run([str(binary), *map(str,case['geometry']), '8', 'smart', str(config)],
                         input=case['pixels'], capture_output=True, check=True, timeout=120,
                         env=dict(os.environ, ROTATION_PLANES_DIRECTORY=str(planes)))
    assert b'ERROR 0\n' in run.stderr and sha(run.stdout)==result['routes']['smart']['raw_sha256']
    w,h = case['geometry']; im = Image.new('RGBA',(w,h))
    im.putdata([(r,g,b,a) for a,r,g,b in struct.iter_unpack('4B',case['pixels'])]); im.save(out/'input.png')
    command = [str(WORKER),'render-trace-png',str(adapter.aex),str(out/'input.png'),str(out/'trace.png'),'--pixel-format','argb8']
    def trace(options, name):
        run = subprocess.run(command+options+zoom.assignments(case), capture_output=True, check=True, timeout=120)
        (out/(name+'.json')).write_bytes(run.stdout)
        data = json.loads(run.stdout)
        assert data['raw_pixel_sha256'] == result['oracle']['raw_sha256']
        assert not data['render_error'] and data['guards_intact']
        assert not data['unsupported_suite_calls'] and not data['dropped_unsupported_suite_calls']
        stage = next(t for t in data['execution_traces'] if t['selector']=='SMART_RENDER')
        assert not stage['truncated'] and not stage['dropped_memory_witnesses']
        return {q['watch_id']:q for q in stage['memory_witnesses']}
    watches = trace(['--watch','function=0x4640,arg=rcx,size=64,occurrence=1'],'config_trace')
    config = bytes.fromhex(watches['watch-1']['after']['hex'])
    minimum,maximum = struct.unpack_from('<2i',config,12)
    step, = struct.unpack_from('<f',config)
    # 4867 SUB / 486A INC: both endpoint rows are allocated and consumed.
    angular = int(fields.f32(360/step)); radial = maximum-minimum+1; cells=angular*radial
    report.update(native_dimensions=[angular,radial], native_min_radius=minimum,
                  mac_dimensions=list(struct.unpack('<2i',(planes/'dimensions.i32').read_bytes())), planes={})
    specs = [('polar',0x2780,'rdx',None,cells*16),('scalar',0x2780,'rcx',0x40,cells*4),
             ('span',0x4640,'rdx',0x90,w*h*4),('accum',0x1b10,'rcx',0x3c940,cells*16),
             ('max',0x1b10,'rcx',0x3c948,cells*4),('normalized',0x1000,'rcx',None,cells*16)]
    for name,rva,arg,deref,size in specs:
        options=[]
        for offset in range(0,size,4096):
            spec=f'function={hex(rva)},arg={arg},size={min(4096,size-offset)},offset={offset},occurrence=1'
            if deref is not None: spec+=f',deref={hex(deref)}'
            options+=['--watch',spec]
        watches=trace(options,name+'_trace')
        native=b''.join(bytes.fromhex(watches[f'watch-{i+1}']['before']['hex']) for i in range(len(options)//2))
        (out/('native_'+name+'.f32')).write_bytes(native)
        mac=(planes/(name+'.f32')).read_bytes()
        report['planes'][name]=(fields.compare_words(native,mac) if len(native)==len(mac) else
                               dict(status='dimensions_differ',native_bytes=len(native),mac_bytes=len(mac)))
    pe=pefile.PE(str(adapter.aex)); decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
    report['static']={}
    for name,start,end in [('rotation_geometry',0x4640,0x49cc),('rotation_radius',0x1bb0,0x1c85),('zoom_radius',0xa8f0,0xa9c5)]:
        report['static'][name]=[dict(rva=hex(i.address-pe.OPTIONAL_HEADER.ImageBase),bytes=i.bytes.hex(),
                                    instruction=i.mnemonic+' '+i.op_str)
                                for i in decoder.disasm(pe.get_data(start,end-start),pe.OPTIONAL_HEADER.ImageBase+start)]
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',case['geometry'],report['native_dimensions'],report['mac_dimensions'],
          {k:v.get('different_words',v.get('status')) for k,v in report['planes'].items()},flush=True)
    shutil.rmtree(out/'build'); shutil.rmtree(out/'planes_build')


if __name__=='__main__': main()
