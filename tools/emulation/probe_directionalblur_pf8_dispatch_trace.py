#!/usr/bin/env python3
"""F06: original PF8 builder/branch/worker/writer, paired with scratch core."""
import argparse
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import types

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from probe_directionalblur_pf8_dispatch import Probe, TICKET, BASE_REF, baseline, SOURCE
from core import load_corpus, sha
from aex_loader import AexLoader
from aex_witness import leaf_check
from PIL import Image
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    args.main, args.max_size, args.case_timeout = ROOT.parent.parent, 256, 10
    scratch = ROOT/'orchestra/state'/TICKET
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    tempfile.tempdir = str(scratch)
    fixture_path = ROOT/'tools/emulation/dblur_fullrender_host_fixture_20260711.py'
    # Only diagnostics change: the old fixture samples component records at
    # fixed large-image coordinates; keep its samples within these tiny worlds.
    body = fixture_path.read_text().replace(
        '(row_width // 2, 73), (row_width // 2, row_width - 72)',
        '(row_width // 2, 0), (row_width // 2, row_width - 1)')
    fixture = types.ModuleType('f06_fixture')
    fixture.__file__ = str(fixture_path)
    exec(compile(body, str(fixture_path), 'exec'), fixture.__dict__)
    triage = json.loads((ROOT/'reports/fuzz/olmdirectionalblur_triage_20261022.json').read_text())
    rows = []
    with tempfile.TemporaryDirectory(prefix='trace_', dir=scratch) as tmp:
        tmp = Path(tmp)
        adapter = Probe(args)
        provenance = adapter.prepare(tmp, time.monotonic()+120)
        for target in triage['clusters']:
            if target['cluster'] not in (4,5,6,7,16,17): continue
            case, _ = load_corpus(ROOT/target['corpus'], adapter)
            values = {p['slot']:p['value'] for p in case['parameters']}
            trace = {'branch':[], 'writer_rgba_f32':[]}
            class TracedLoader(AexLoader):
                def __init__(self, *a, **kw):
                    super().__init__(*a, **kw)
                    pointers = [self.host_alloc(16) for _ in range(4)]
                    self.write_bytes(pointers[0], bytes(16))
                    for p in pointers[1:]: self.write_bytes(p, b'\xa5'*16)
                    result = leaf_check(self, 0x180001000, [0,0,*pointers,0,0,0,0,1,0])
                    assert self.read_bytes(pointers[1],16) == bytes(16)
                    assert all(self.read_bytes(p,16) == bytes(4)+b'\xa5'*12 for p in pointers[2:])
                    trace['abi_leaf_instructions'] = result['instructions']
                    def branch(ld, address, size):
                        p = ld.uc.reg_read(UC_X86_REG_RBX)
                        trace['branch'].append({'rva':hex(address-0x180000000),
                            'strength_fade_counts':list(struct.unpack('<4i',ld.read_bytes(p+0x48,16)))})
                    def writer(ld, address, size):
                        if not trace['branch']: return
                        p = ld.uc.reg_read(UC_X86_REG_RCX)
                        x,y = ld.uc.reg_read(UC_X86_REG_RDX),ld.uc.reg_read(UC_X86_REG_R8)
                        stride = fixture.u32(ld,p+0x80a0)
                        row,col = fixture.u32(ld,p+0x8098),fixture.u32(ld,p+0x809c)
                        base = fixture.u64(ld,p+0x8090)
                        trace['writer_rgba_f32'].append(ld.read_bytes(base+((row+y)*stride+col+x)*16,16).hex())
                    self.add_code_hook(0x180004b50,branch)
                    self.add_code_hook(0x180004b69,branch)
                    self.add_code_hook(0x180006b30,writer)
            fixture.AexLoader = TracedLoader
            source, output, raw = tmp/'input.png', tmp/'fixture.json', tmp/'aex.raw'
            a,r,g,b = case['pixels']
            Image.frombytes('RGBA',(1,1),bytes((r,g,b,a))).save(source)
            names = {1:'angle',2:'brightness-gain',3:'size-variation',5:'front-strength',6:'front-alpha-fade',
                     7:'front-sharp-tail',10:'back-strength',11:'back-alpha-fade',12:'back-sharp-tail',
                     15:'noise-variation',16:'noise-type',18:'seed',19:'noise-offset',20:'thickness'}
            # Original builder's fixed getters truncate these controls to whole
            # values; all six angles are zero and noise is disabled.
            sys.argv = [str(fixture_path),'--aex',str(adapter.aex),'--source',str(source),'--output',str(output),
                '--host-output-raw',str(raw),'--actual-iterate-callbacks','--no-detour-rotate',
                '--downsample-num','1','--downsample-den','1','--world-area','0','0','1','1',
                '--max-instructions','20000000']
            for slot,name in names.items():
                value = values[slot] if slot in (1,2) else int(values[slot])
                sys.argv += ['--'+name,str(value)]
            fixture.main()
            observed = json.loads(output.read_text())
            assert observed['status']=='ok', observed.get('blocked')
            floats = tmp/'mac.f32'; floats.unlink(missing_ok=True)
            adapter.env['OLM_F06_FLOATS'] = str(floats)
            result, mac, _ = adapter.candidate(case,tmp,'classic',time.monotonic()+30)
            oracle, reference = adapter.oracle(case,tmp,time.monotonic()+30)
            native = raw.read_bytes()
            assert result['status']=='ok' and oracle['status']=='ok' and native==mac==reference
            paired = bytes.fromhex(''.join(trace['writer_rgba_f32'])) == floats.read_bytes()
            assert paired
            rows.append({'cluster':target['cluster'],'corpus':target['corpus'],'trace':trace,
                'mac_writer_rgba_f32':floats.read_bytes().hex(),'paired_writer_exact':paired,
                'final_argb8':native.hex(),'reference_sha256':sha(reference),
                'rowdriver_calls':observed['execution']['rowdriver_calls'],
                'component_map':observed['execution'].get('component_map_probe')})
    report = {'schema':'directionalblur.pf8-dispatch-trace/1','cases':rows,'provenance':provenance,
        'baseline_ref':BASE_REF,'baseline_source_sha256':sha(baseline(SOURCE).encode()),
        'baseline_core_sha256':sha(baseline(ROOT/'core/dblur_frontonly.cpp').encode()),
        'scratch_probe_sha256':sha((ROOT/'tools/fuzz/probe_directionalblur_pf8_dispatch.py').read_bytes()),
        'fixture_sha256':sha(fixture_path.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),
        'scope':'Original builder, rotate, rowdriver and typed callbacks; host allocation/iteration and libm substitutions. No native Windows AE/UCRT claim.'}
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PAIRED WRITER EXACT',len(rows),'SESSION/TRACE/PUBLIC RAW EXACT',len(rows))


if __name__ == '__main__': main()
