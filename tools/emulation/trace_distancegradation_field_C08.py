#!/usr/bin/env python3
"""Pair original public PF8 normalization with before/current Mac intermediates."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter, SOURCE
from core import load_corpus, sha, raw_diff
from run import main_checkout, default_worker
from verify_distancegradation_smart_C08 import variant
from PIL import Image


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--before-ref', default='d3fe5c3e')
    args = p.parse_args()
    args.scratch = args.scratch.resolve()
    assert args.scratch.is_relative_to(ROOT/'orchestra/state/C08-dg-smart-r2')
    args.scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(args.scratch), TMP=str(args.scratch), TEMP=str(args.scratch))
    tempfile.tempdir = str(args.scratch)
    a = Adapter(argparse.Namespace(max_size=256, case_timeout=30, main=main_checkout(), worker=default_worker()))
    report = dict(schema='olm.dg-smart-field-C08/1', before_ref=args.before_ref, rows=[])
    asm = (main_checkout()/'disasm/DistanceGradation.aex.asm.txt').read_bytes()
    anchors = ['18117490b  MOVSD XMM3,qword ptr [0x181504ab0]',
               '181174942  CALL 0x18117ca50', '181172932  CALL 0x18117c580']
    assert all(anchor.encode() in asm for anchor in anchors)
    report.update(disassembly_sha256=sha(asm), static_anchors=anchors)
    old = subprocess.check_output(['git','show',args.before_ref+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'], cwd=ROOT).decode()
    # Diagnostic copies only: record the scaled float plane before byte packing.
    dump = 'if (const char *dp = getenv("OLM_DG_C08_FIELD")) { FILE *f = fopen(dp,"ab"); if (f) { for (long j=0;j<w*h;++j) { float v=out[j] * SCALE; fwrite(&v,4,1,f); } fclose(f); } }'
    anchor = 'out, (size_t)w * sizeof(float), (float)threshold, constant_interp);'
    assert old.count(anchor) == 1
    old = old.replace(anchor, anchor+'\n'+dump.replace('SCALE','255.0f'))
    current = SOURCE.read_text()
    anchor = 'if (smart_pf8_staging) {'
    assert current.count(anchor) == 1
    current = current.replace(anchor, anchor+'\n'+dump.replace('SCALE','1.0f'))
    deadline = time.monotonic()+300
    with tempfile.TemporaryDirectory(dir=args.scratch) as td:
        td = Path(td); prod = td/'prod'; prod.mkdir()
        report['provenance'] = a.prepare(prod, deadline)
        before = variant(a, td/'before', deadline, old)
        after = variant(a, td/'after', deadline, current)
        for index in (58,236):
            path = next((ROOT/'tests/fuzz_corpus/olmdistancegradation').glob(f'seed1_case{index:06d}_*.json'))
            c,saved = load_corpus(path,a); w,h = c['geometry']; assert c['depth'] == 8
            im = Image.new('RGBA',(w,h))
            im.putdata([(r,g,b,al) for al,r,g,b in struct.iter_unpack('<4B',c['pixels'])]); im.save(td/'in.png')
            params=[]
            for q in c['parameters']:
                name=next(d['name'] for d in a.binding['parameters'] if d['slot']==q['slot'])
                params.append(name+'='+(','.join(map(str,q['value'])) if isinstance(q['value'],list) else str(q['value'])))
            watches=[f'function=0x117ca50,arg=rcx,deref=88,size={w*h*4}',
                     f'function=0x117ca50,arg=rdx,deref=88,size={w*h*4}',
                     f'function=0x1170380,arg=r9,deref=24,size={w*h*4}']
            cmd=[str(a.worker),'render-trace-png',str(a.aex),str(td/'in.png'),str(td/'out.png'),'--pixel-format','argb8']
            for watch in watches: cmd += ['--watch',watch]
            proc=subprocess.run(cmd+params,capture_output=True,timeout=30,check=True,env=a.env)
            trace=json.loads(proc.stdout)
            assert trace['render_error']==0 and trace['guards_intact']
            assert trace['raw_pixel_sha256']==saved['result']['oracle']['raw_sha256']
            t=next(t for t in trace['execution_traces'] if t['selector']=='SMART_RENDER')
            assert not t['trace_configuration']['unhookable_watches']
            ws={v['watch_id']:v for v in t['memory_witnesses']}
            expected=bytes.fromhex(ws['watch-2']['after']['hex'])
            row=dict(index=index,geometry=[w,h],input_sha256=sha(c['pixels']),oracle_sha256=trace['raw_pixel_sha256'],
                     watches=watches,thresholded_hex=ws['watch-1']['before']['hex'],aex_scaled_float_hex=expected.hex(),
                     aex_staged_hex=ws['watch-3']['before']['hex'])
            for name,adapter in (('before',before),('after',after)):
                dumpfile=td/'field.bin';dumpfile.unlink(missing_ok=True)
                adapter.env['OLM_DG_C08_FIELD']=str(dumpfile)
                status,raw,_=adapter.candidate(c,td,'smart',deadline)
                assert status['status']=='ok'
                plane=dumpfile.read_bytes(); assert len(plane)==len(expected)
                row[name]=dict(scaled_float_hex=plane.hex(),scaled_diff=raw_diff(expected,plane,32),raw_sha256=sha(raw),exact=sha(raw)==trace['raw_pixel_sha256'])
                if name=='after':assert plane==expected and row[name]['exact']
            report['rows'].append(row)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PASS',len(report['rows']),'scaled planes and final public outputs exact')

if __name__=='__main__':main()
