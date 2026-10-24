#!/usr/bin/env python3
"""Probe the two existing watch selectors at a required legacy noise checkpoint.

This checks hook admission, not the value of the noise fields. The legacy probe
uses RBX after 0x8162; the resident schema also lacks that register. We deliberately
use a supported register to isolate whether the checkpoint itself can be armed.
"""
import importlib.util,json,time,zlib
from pathlib import Path
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('r08',Path(__file__).with_name('R08-fullsize.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def main():
 d=m.S/'extra-plane-capability';d.mkdir(exist_ok=True)
 old=next(r for r in json.loads((m.ROOT/'orchestra/reports/F39-evidence.json').read_text()) if r['command_index']==153)
 p=next(p for p in (m.ROOT/'refs/fixtures/olmradialblur_F39_F32_final_20261023').glob('*/provenance.json') if json.loads(p.read_text())['command_index']==153)
 pixels=zlib.decompress(p.with_name('source.argb.zlib').read_bytes());assert m.sha(pixels)==old['source_sha256']
 case=dict(geometry=old['geometry'],depth=old['depth'],parameters=old['parameters'],pixels=pixels,input_padding=0,output_padding=0)
 worker=Path.home()/'.cache/olm-emu/worker-R08-trace/aex-guest-worker';results=[]
 for selector in ('instruction_rva','function_rva'):
  rd=d/selector;rd.mkdir(exist_ok=True);watch=dict(id='post-noise-checkpoint',register='rcx',size=16,occurrence=1);watch[selector]=0x8162
  wp=rd/'watches.json';wp.write_text(json.dumps([watch],indent=2)+'\n')
  adapter=m.Adapter(SimpleNamespace(main=m.main_assets(),worker=worker,max_size=1920,case_timeout=60));adapter.env.update(AEXCOMPAT_RESIDENT_TRACE=str(rd/'trace.json'),AEXCOMPAT_RESIDENT_WATCHES=str(wp))
  status,raw=adapter.oracle(case,rd,time.monotonic()+70);t=json.loads((rd/'trace.json').read_text())
  row=dict(selector=selector,watch=watch,status=status,output_sha256=m.sha(raw),output_bytes=len(raw),memory_witnesses=len(t['memory_witnesses']),unhookable=t['trace_configuration']['unhookable_watches'])
  results.append(row);print(json.dumps(row),flush=True)
  assert status['status']=='ok' and row['memory_witnesses']==0 and row['unhookable']
 (d/'report.json').write_text(json.dumps(dict(scope='Checkpoint admission only; no noise arithmetic claim',worker_sha256=m.sha(worker.read_bytes()),source_sha256=m.sha(pixels),probes=results),indent=2)+'\n')
if __name__=='__main__':main()
