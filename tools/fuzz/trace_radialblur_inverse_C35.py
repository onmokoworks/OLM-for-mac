#!/usr/bin/env python3
"""Lossless FLOAT32 inverse-sampler replay from a public Smart matrix input.

This isolates the operation at AEX RVA 1000 using the port's captured four
normalized taps. It does NOT assert that upstream native planes match.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import time
import capstone
import pefile
from types import SimpleNamespace
sys.dont_write_bytecode = True
from adapters.radialblur import Adapter, public
from core import sha, raw_diff
from verify_radialblur_smart_C06 import ROOT, MAIN
import verify_radialblur_smart_C11 as matrix
from aex_loader import AexLoader


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--source', type=Path, default=public.SOURCE)
    ap.add_argument('--index', type=int, default=44)
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C35-radial-smart-r6')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out),
                      OLM_RADIAL_CANDIDATE_SANITIZE='1', C35_INVERSE_TRACE=str(out/'taps.bin'))
    source = args.source.read_text()
    source = source.replace('GenericRadialInputIsSDR<PF_PixelFloat>(input));',
                            'GenericRadialInputIsFinite<PF_PixelFloat>(input));')
    marker = '\t\t\tPixelT output_pixel{};'
    pos = source.index(marker, source.index('static PF_Err RenderRotationTyped'))
    capture = r'''
            if (const char *path = std::getenv("C35_INVERSE_TRACE")) {
                FILE *file = std::fopen(path, "ab");
                const float values[] = {fx, fy,
                    sample(x0,y0,0),sample(x0,y0,1),sample(x0,y0,2),sample(x0,y0,3),
                    sample(x1,y0,0),sample(x1,y0,1),sample(x1,y0,2),sample(x1,y0,3),
                    sample(x0,y1,0),sample(x0,y1,1),sample(x0,y1,2),sample(x0,y1,3),
                    sample(x1,y1,0),sample(x1,y1,1),sample(x1,y1,2),sample(x1,y1,3),
                    outer_state.normalized_rgb[0],outer_state.normalized_rgb[1],
                    outer_state.normalized_rgb[2],outer_state.alpha};
                if (file) { std::fwrite(values, sizeof(values), 1, file); std::fclose(file); }
            }
'''
    source = source[:pos]+capture+source[pos:]
    source = re.sub(r'^#include "([^" ]+)"',lambda m:'#include "'+str((public.SOURCE.parent/m.group(1)).resolve())+'"',source,flags=re.MULTILINE)
    snapshot=out/'experiment.cpp';snapshot.write_text(source)
    for name in ('OLMRadialBlur.h','OLMRadialBlur_Strings.h','OLMRadialBlur_Strings.cpp'):
        (out/name).symlink_to(public.SOURCE.parent/name)
    snapshot.with_suffix('.h').write_bytes(public.SOURCE.with_suffix('.h').read_bytes())
    public.SOURCE=snapshot
    worker=Path.home()/'.cache/olm-emu/worker-F32-deep/aex-guest-worker'
    adapter=Adapter(SimpleNamespace(main=MAIN,worker=worker,max_size=256,case_timeout=60))
    deadline=time.monotonic()+1800
    report=dict(provenance=adapter.prepare(out,deadline),matrix_index=args.index)
    matrix.ALL_DEPTHS=True
    case=list(matrix.finite_cases(adapter))[args.index]
    report['input_sha256']=sha(case['pixels'])
    report['case']={k:v for k,v in case.items() if k!='pixels'}
    report['input_hex']=case['pixels'].hex()
    oracle,reference=adapter.oracle(case,out,deadline,'smart')
    actual,raw,guards=adapter.candidate(case,out,'smart',deadline)
    assert oracle['status']==actual['status']=='ok' and not actual.get('sanitizer')
    report['public']=dict(oracle=oracle,actual=actual,diff=raw_diff(reference,raw,32),
                          original_sha256=sha(reference),candidate_sha256=sha(raw))
    records=(out/'taps.bin').read_bytes()
    assert len(records)==case['geometry'][0]*case['geometry'][1]*88
    loader=AexLoader(str(adapter.aex),verbose=False,fast=False)
    src=loader.bump_alloc(64);dst=loader.bump_alloc(16)
    # Import-free ABI control: constant RGBA with unit alpha at fractional coords.
    control=struct.pack('<4f',.25,.5,.75,1.)*4
    loader.write_bytes(src,control)
    args1000=lambda x,y:[src,dst,2,8,x,y]
    loader.call_function(0x180001000,int_args=args1000(0x3e800000,0x3f000000),max_instructions=1000)
    assert loader.read_bytes(dst,16)==control[:16] and not loader.import_log
    report['abi_control']='exact; no imports'
    pe=pefile.PE(str(adapter.aex));base=pe.OPTIONAL_HEADER.ImageBase
    decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
    report['inverse_static']=[dict(rva=hex(i.address-base),bytes=i.bytes.hex(),instruction=i.mnemonic+' '+i.op_str) for i in decoder.disasm(pe.get_data(0x1000,0x270),base+0x1000)]
    rows=[]
    for i in range(len(records)//88):
        record=records[i*88:(i+1)*88]
        x,y=struct.unpack('<2I',record[:8]); taps=record[8:72]; mac=record[72:88]
        loader.write_bytes(src,taps)
        loader.call_function(0x180001000,int_args=args1000(x,y),max_instructions=1000)
        native=loader.read_bytes(dst,16)
        assert not loader.import_log and loader.read_bytes(src,64)==taps
        if native!=mac:
            rows.append(dict(pixel=i,coordinates_hex=record[:8].hex(),taps_hex=taps.hex(),
                             original_hex=native.hex(),mac_hex=mac.hex(),diff=raw_diff(native,mac,32)))
    report['inverse_replay']=dict(cases=len(records)//88,differences=rows,
        claim='Same captured port taps and fractions; upstream native equivalence unproven')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.rmtree(out/'build')
    print('INVERSE',len(records)//88,'different',len(rows),'public',report['public']['diff'],flush=True)


if __name__=='__main__':main()
