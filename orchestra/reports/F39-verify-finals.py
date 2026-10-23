#!/usr/bin/env python3
"""Verify provisional final fixtures against fresh F32 AEX and committed evidence.

This companion check deliberately retains the old, independent stage assertions.
It does not claim that whole multi-case legacy commands pass.
"""
import importlib.util,json,time,zlib,tempfile,shutil
from pathlib import Path
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('recheck',Path(__file__).with_name('F39-recheck.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def main():
 rows=json.loads((r.ROOT/'orchestra/reports/F39-evidence.json').read_text());count=0
 adapter=r.Adapter(SimpleNamespace(main=r.main_assets(),worker=r.WORKER,max_size=256,case_timeout=120))
 build=r.S/'final-verifier';build.mkdir(exist_ok=True)
 adapter.prepare(build,time.monotonic()+180)

 for path in sorted((r.ROOT/'refs/fixtures/olmradialblur_F39_F32_final_20261023').glob('*/provenance.json')):
  p=json.loads(path.read_text());expected=zlib.decompress(path.with_name('output.argb.zlib').read_bytes());pixels=zlib.decompress(path.with_name('source.argb.zlib').read_bytes())
  assert r.sha(expected)==p['output_sha256'] and r.sha(pixels)==p['source_sha256']
  adapter.aex=r.resolve_asset(Path(p['aex_path']))
  assert r.sha(adapter.aex.read_bytes())==p['aex_sha256'] and r.sha(r.WORKER.read_bytes())==p['worker_sha256']
  case=dict(geometry=p['geometry'],depth=p['depth'],parameters=p['parameters'],pixels=pixels,input_padding=0,output_padding=0)
  with tempfile.TemporaryDirectory(dir=r.S) as td:status,raw=adapter.oracle(case,Path(td),time.monotonic()+150)
  assert status['status']=='ok' and raw==expected,(p['command_index'],status,r.compare(expected,raw))
  with tempfile.TemporaryDirectory(dir=r.S) as td:
   candidate,mac,guards=adapter.candidate(case,Path(td),'smart',time.monotonic()+150)
  assert candidate['status']=='ok' and mac==expected,(p['command_index'],candidate,r.compare(expected,mac))
  evidence=next(v for v in rows if v['command_index']==p['command_index'])
  assert evidence['F32_vs_mac']['equal'] and evidence['F32_vs_mac']['left_sha256']==r.sha(raw)
  count+=1;print(p['command_index'],'F32 exact',flush=True)
 shutil.rmtree(build)
 print(f'{count} final fixtures verified against fresh F32 and Mac Smart; stage assertions are not re-adjudicated.')
if __name__=='__main__':main()
