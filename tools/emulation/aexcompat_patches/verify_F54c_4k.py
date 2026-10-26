#!/usr/bin/env python3
"""4K original-AEX no-op: F54b versus resident-traced F54c (selector context)."""
import argparse, json, struct, time
from pathlib import Path
from types import SimpleNamespace
import verify_F54c as v

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);args=ap.parse_args()
    # Original RadialBlur dispatch table: selector 24 -> 0x1096c;
    # direct call at 0x10974 invokes 0x17d60 with InData in RDX.
    d=v.S/'4k';d.mkdir(parents=True,exist_ok=True)
    wp=d/'watches.json';wp.write_text(json.dumps([dict(id='selector-context',instruction_rva=0x10974,register='rdx',size=128,occurrence=1)]))
    baseline=Path.home()/'.cache/olm-emu/worker-F54b/aex-guest-worker'
    rows=[]
    for depth in (8,16,32):
        pixel={8:bytes([255,71,29,103]),16:struct.pack('<4H',32768,9000,4000,12000),32:struct.pack('<4f',1.,.25,.125,.375)}[depth]
        a=v.Adapter(SimpleNamespace(main=v.MAIN,worker=baseline,max_size=4096,case_timeout=180))
        for key in list(a.env):
            if key.startswith('AEXCOMPAT_RESIDENT_') or key.startswith('AEXCOMPAT_SMART_TRACE'):del a.env[key]
        case=dict(geometry=[3840,2160],depth=depth,pixels=pixel*(3840*2160),parameters=a.defaults(3840,2160),input_padding=0,output_padding=0)
        status,raw=a.oracle(case,d,time.monotonic()+190)
        assert status['status']=='ok',status
        assert raw==case['pixels']
        expected=v.sha(raw);del raw
        a.worker=args.worker.resolve();tp=d/f'{depth}.json'
        a.env.update(AEXCOMPAT_RESIDENT_TRACE=str(tp),AEXCOMPAT_RESIDENT_WATCHES=str(wp))
        observed,raw=a.oracle(case,d,time.monotonic()+190)
        assert observed==status and v.sha(raw)==expected,(depth,observed)
        del raw
        trace=json.loads(tp.read_text());ws=trace['memory_witnesses']
        assert len(ws)==1 and ws[0]['watch_id']=='selector-context'
        assert not trace['dropped_memory_witnesses'] and not trace['trace_configuration']['unhookable_watches']
        for when in ('before','after'):
            snap=ws[0][when];assert snap['status']=='captured'
            assert bytes.fromhex(snap['hex'])==Path(str(tp)+f'.000.{when}.bin').read_bytes()
        rows.append(dict(depth=depth,geometry=case['geometry'],output_bytes=len(case['pixels']),output_sha256=expected,watch_id=ws[0]['watch_id'],capture_bytes=128,exact=True,status=observed))
        (v.S/'4k-summary.json').write_text(json.dumps(rows,indent=2)+'\n');print(depth,'4K exact with resident context capture',flush=True)
if __name__=='__main__':main()
