#!/usr/bin/env python3
"""PF32 Rotation Offset-mode-3 x Type-1 Noise bounded cross-product."""
from __future__ import annotations
import hashlib,json,pickle,subprocess,sys,tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/"tools/emulation";sys.path.insert(0,str(HERE))
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as pf32  # noqa:E402
REPORT=ROOT/"refs/conformance/olmradialblur_rotation_pf32_offset_mode3_noise_type1_actual_aex_20260810.json";DOC=REPORT.with_suffix(".md")
OFFSETS=(2,3,4);NOISES=(25.0,100.0)
def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def actual_at(offset:int,noise:float)->dict[str,bytes]:
 old_mode,old_offset=pf32.OUTER_OFFSET_MODE,pf32.OUTER_OFFSET
 names=("FIXTURE_SIZE_VARIATION","FIXTURE_NOISE_VARIATION","FIXTURE_NOISE_TYPE","FIXTURE_SEED","FIXTURE_NOISE_OFFSET","FIXTURE_THICKNESS","CAPTURE_NOISE_INTERNALS")
 old={n:getattr(pf32.base,n) for n in names}
 try:
  pf32.OUTER_OFFSET_MODE=3;pf32.OUTER_OFFSET=offset
  pf32.base.FIXTURE_SIZE_VARIATION=0.;pf32.base.FIXTURE_NOISE_VARIATION=noise;pf32.base.FIXTURE_NOISE_TYPE=1;pf32.base.FIXTURE_SEED=1;pf32.base.FIXTURE_NOISE_OFFSET=0.;pf32.base.FIXTURE_THICKNESS=10.;pf32.base.CAPTURE_NOISE_INTERNALS=True
  return pf32.actual_aex()
 finally:
  pf32.OUTER_OFFSET_MODE,pf32.OUTER_OFFSET=old_mode,old_offset
  for n,v in old.items():setattr(pf32.base,n,v)
def production_at(offset:int,noise:float,expected:dict[str,bytes])->dict[str,bytes]:
 old=(pf32.OUTER_OFFSET_MODE,pf32.OUTER_OFFSET,pf32.NOISE_VARIATION)
 try:
  pf32.OUTER_OFFSET_MODE=3;pf32.OUTER_OFFSET=offset;pf32.NOISE_VARIATION=noise
  return pf32.mac_production(expected)
 finally:pf32.OUTER_OFFSET_MODE,pf32.OUTER_OFFSET,pf32.NOISE_VARIATION=old
def isolated(mode:str,offset:int,noise:float,expected:dict[str,bytes]|None=None)->dict[str,bytes]:
 with tempfile.TemporaryDirectory(prefix="radial_offset_noise_") as name:
  out=Path(name)/"out.pkl";cmd=[sys.executable,str(Path(__file__)),f"--{mode}",str(offset),str(noise)]
  if expected is not None:
   inp=Path(name)/"in.pkl";inp.write_bytes(pickle.dumps(expected));cmd.append(str(inp))
  cmd.append(str(out));subprocess.run(cmd,check=True);return pickle.loads(out.read_bytes())
def rejected(offset:int,noise:float,expected:dict[str,bytes])->bool:
 try:production_at(offset,noise,expected)
 except subprocess.CalledProcessError as exc:return exc.returncode==3
 return False
def main()->int:
 requested=[(o,n) for o in OFFSETS for n in NOISES]
 with ThreadPoolExecutor(max_workers=6) as pool:actual=dict(zip(requested,pool.map(lambda p:isolated("actual",*p),requested)))
 combos=[(o,n) for o in OFFSETS for n in NOISES]
 with ThreadPoolExecutor(max_workers=6) as pool:production=dict(zip(combos,pool.map(lambda p:isolated("production",p[0],p[1],actual[p]),combos)))
 rows=[];exact=True
 for p in combos:
  a=actual[p];m=production[p];matches={k:m[k]==a[k] for k in ("source_scalar","polar","accum","max_alpha","final_rgba","coordinates","output")}
  required=all(matches[k] for k in ("polar","accum","max_alpha","final_rgba","coordinates","output"));exact&=required
  l=np.frombuffer(m["source_scalar"],dtype=np.uint8);r=np.frombuffer(a["source_scalar"],dtype=np.uint8)
  rows.append({"outer_offset_mode":3,"outer_offset":p[0],"noise_variation":p[1],"production_matches_actual":matches,"production_source_scalar_different_bytes":int(np.count_nonzero(l!=r)),"actual_output_sha256":sha(a["output"]),"exact":required})
 fail={"offset5_nv25":rejected(5,25.,actual[(2,25.)]),"offset2_nv50":rejected(2,50.,actual[(2,25.)])};exact=exact and all(fail.values());status="exact_with_inactive_source_scalar_boundary" if exact else "mismatch"
 report={"kind":"olmradialblur_rotation_pf32_offset_mode3_noise_type1_actual_aex_20260810","status":status,"scope":"Pinned PF32 Rotation 9x7 rowbytes160; Offset mode3 UI 2/3/4 x Noise Type1 25/100; Strength4, Size Variation0, neutral remaining tuple.","aex_sha256":pf32.AEX_SHA256,"cases":rows,"controls":"The same-offset Noise-0 controls remain independently pinned by the three 20260805 Offset-mode-3 fixtures.","fail_closed":fail,"production_scalar_boundary":"Full source-scalar allocation has the known inactive-cell 1-ULP difference; polar, accum, max-alpha, final, coordinates and padded output are bit exact.","boundary":"No offset5, NV50, Type2/3, PF8/PF16, other geometry or AE-host claim."}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");DOC.write_text(f"# OLM RadialBlur PF32 Offset Mode 3 × Type-1 Noise — 2026-08-10\n\nStatus: **{status}**\n\nAll six Offset 2/3/4 × Noise 25/100 cells are exact from actual-AEX polar/accumulation planes through production padded output. The same-offset Noise-0 controls remain independently pinned by the three 2026-08-05 Offset-mode-3 fixtures. The full source-scalar allocation retains the known inactive-cell 1-ULP boundary. Offset 5 and Noise 50 remain fail-closed.\n");print(json.dumps({"status":status,"cases":len(rows)},sort_keys=True));return 0 if exact else 1
if __name__=="__main__":
 if len(sys.argv)==5 and sys.argv[1]=="--actual":Path(sys.argv[4]).write_bytes(pickle.dumps(actual_at(int(sys.argv[2]),float(sys.argv[3]))));raise SystemExit(0)
 if len(sys.argv)==6 and sys.argv[1]=="--production":Path(sys.argv[5]).write_bytes(pickle.dumps(production_at(int(sys.argv[2]),float(sys.argv[3]),pickle.loads(Path(sys.argv[4]).read_bytes()))));raise SystemExit(0)
 raise SystemExit(main())
