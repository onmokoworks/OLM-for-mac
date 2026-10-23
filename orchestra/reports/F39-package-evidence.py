#!/usr/bin/env python3
"""Package only measured F32 bytes; never derive expectations from Mac output.

These final-only fixtures are provisional companions. They do not replace the
legacy plane assertions until raw typed F32 stage capture is available.
"""
import importlib.util,json,zlib,struct,subprocess
from pathlib import Path
spec=importlib.util.spec_from_file_location('recheck',Path(__file__).with_name('F39-recheck.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def main():
 rows=[]
 destination=r.ROOT/'refs/fixtures/olmradialblur_F39_F32_final_20261023'
 destination.mkdir(exist_ok=True)
 stored={}
 for p in (r.ROOT/'refs/fixtures').glob('olmradialblur*/*output*.zlib'):
  raw=zlib.decompress(p.read_bytes());stored.setdefault(r.sha(raw),[]).append(str(p.relative_to(r.ROOT)))
 for index in sorted([*r.PROFILES,165]):
  d=r.S/str(index);row=json.loads((d/'result.json').read_text())
  assert row['oracle_status']['status']=='ok' and row['F32_vs_mac']['equal']
  row['classification']='C' if row['F32_vs_legacy']['equal'] else 'A'
  row['candidate_revision']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.ROOT,text=True).strip()
  row['candidate_source_sha256']=r.sha((r.ROOT/'mac/OLMRadialBlur/OLMRadialBlur.cpp').read_bytes())
  if index!=165:
   oldsha=row['legacy_vs_mac']['output']['left_sha256']
   row['stored_outputs_matching_legacy_padded_sha256']=stored.get(oldsha,[])
   matches=subprocess.run(['rg','-l',oldsha,'refs/conformance','orchestra/reports/F36-fixture-runner-worktree-and-triage.md'],cwd=r.ROOT,text=True,capture_output=True)
   row['stored_reports_containing_legacy_padded_sha256']=matches.stdout.splitlines()
   assert row['stored_outputs_matching_legacy_padded_sha256'] or row['stored_reports_containing_legacy_padded_sha256']
   inp=(d/'input.raw').read_bytes()
   # Prove whether the PNG-only trace transport could preserve these inputs.
   fmt='H' if row['depth']==16 else 'f';top=32768 if fmt=='H' else 1
   values=[v[0] for v in struct.iter_unpack('<'+fmt,inp)]
   promoted=[((v*32768+127)//255 if fmt=='H' else struct.unpack('<f',struct.pack('<f',v/255))[0]) for v in range(256)]
   row['samples_not_representable_by_trace_png']=sum(v not in promoted for v in values)
   if row['classification']=='A':
    target=destination/str(index);target.mkdir(exist_ok=True)
    raw=(d/'F32.raw').read_bytes();assert r.sha(raw)==row['F32_vs_mac']['left_sha256']
    (target/'output.argb.zlib').write_bytes(zlib.compress(raw,9))
    (target/'source.argb.zlib').write_bytes(zlib.compress(inp,9))
    provenance=dict(schema='olm.radial.F32-final-fixture/1',command_index=index,geometry=row['geometry'],depth=row['depth'],controls=row['controls'],parameters=row['parameters'],source_sha256=r.sha(inp),output_sha256=r.sha(raw),aex_path=row['aex_path'],aex_sha256=row['aex_sha256'],worker_path=row['worker_path'],worker_sha256=row['worker_sha256'],route='original AEX public Smart',rowbytes=row['geometry'][0]*row['depth']//8*4,legacy_padded_output_sha256=oldsha,superseded_final_outputs=row['stored_outputs_matching_legacy_padded_sha256'],superseded_reports=row['stored_reports_containing_legacy_padded_sha256'],candidate_revision=row['candidate_revision'],candidate_source_sha256=row['candidate_source_sha256'],scope='F36 first failing witness only; packed visible final pixels. Legacy full-plane assertions remain active. Provisional until raw typed F32 intermediate capture.',regenerate=f'python3 -B orchestra/reports/F39-recheck.py {index}; python3 -B orchestra/reports/F39-package-evidence.py')
    (target/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
  else:
   row['legacy_plane_report']=json.loads((d/'mac-report.json').read_text())['differences']
  rows.append(row)
 (r.ROOT/'orchestra/reports/F39-evidence.json').write_text(json.dumps(rows,indent=2)+'\n')
 for row in rows:print(row['command_index'],row['classification'],row['F32_vs_legacy']['different_bytes'],row['F32_vs_mac']['different_bytes'],flush=True)
if __name__=='__main__':main()
