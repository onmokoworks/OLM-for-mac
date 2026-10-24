#!/usr/bin/env python3
"""Exercise full-plane and displaced-window configurations without rebuilding C53b."""
import hashlib, importlib.util, json, os, resource, time, zlib
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('trace_driver',Path(__file__).with_name('R06-radial-trace.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def main():
    d=m.S/'capability';d.mkdir(exist_ok=True)
    old=next(r for r in json.loads((ROOT/'orchestra/reports/F39-evidence.json').read_text()) if r['command_index']==152)
    p=next(p for p in (ROOT/'refs/fixtures/olmradialblur_F39_F32_final_20261023').glob('*/provenance.json') if json.loads(p.read_text())['command_index']==152)
    pixels=zlib.decompress(p.with_name('source.argb.zlib').read_bytes())
    assert m.sha(pixels)==old['source_sha256']
    case=dict(geometry=old['geometry'],depth=old['depth'],parameters=old['parameters'],pixels=pixels,input_padding=0,output_padding=0)
    worker=Path.home()/'.cache/olm-emu/worker-C53b-trace/aex-guest-worker'
    assert m.sha(worker.read_bytes())=='df51edc461ee13ae826c94e62b29c17b813181ef1c2719388e4d9faf180099a2'
    report=dict(worker_sha256=m.sha(worker.read_bytes()),required_full_plane_bytes=1800*1104*16,probes=[],scope='Configuration admission only on a retained 9x7 typed input; no full-size render or arithmetic claim')
    # Full array and a second window are two ways to preserve full-plane coverage.
    # The second requires a byte displacement after loading the pointer, not a
    # dereference_offset (which selects a pointer slot in the context).
    configs=[('whole-plane',dict(id='full',function_rva=0x2780,register='rcx',dereference_offset=0x38,size=1800*1104*16,occurrence=1)),('displaced-window',dict(id='tail',function_rva=0x2780,register='rcx',dereference_offset=0x38,byte_offset=16777216,size=1800*1104*16-16777216,occurrence=1))]
    for name,watch in configs:
        rd=d/name;rd.mkdir(exist_ok=True);wp=rd/'watches.json';wp.write_text(json.dumps([watch],indent=2)+'\n')
        adapter=m.Adapter(SimpleNamespace(main=m.main_assets(),worker=worker,max_size=1920,case_timeout=30))
        adapter.env.update(AEXCOMPAT_RESIDENT_TRACE=str(rd/'trace.json'),AEXCOMPAT_RESIDENT_WATCHES=str(wp))
        def observed(out,err):
            (rd/'stderr.log').write_bytes(err)
            (rd/'stdout.bin').write_bytes(out)
        adapter.session_observed=observed
        status,raw=adapter.oracle(case,rd,time.monotonic()+40)
        report['probes'].append(dict(name=name,watch=watch,status=status,output_bytes=len(raw),trace_present=(rd/'trace.json').exists()))
        (d/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(name,status['status'],status.get('diagnostic',''),flush=True)
    assert all(p['status']['status']=='reject' and p['output_bytes']==0 and not p['trace_present'] for p in report['probes'])
if __name__=='__main__':main()
