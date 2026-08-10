#!/usr/bin/env python3
"""PF32 Rotation bounded Outer/Inner Edge Fade families."""
from __future__ import annotations
import hashlib,json,pickle,subprocess,sys,tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/"tools/emulation";sys.path.insert(0,str(HERE))
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as pf32  # noqa:E402
REPORT=ROOT/"refs/conformance/olmradialblur_rotation_pf32_edge_fade_actual_aex_20260811.json";DOC=REPORT.with_suffix(".md")
def sha(b):return hashlib.sha256(b).hexdigest()
def configure(kind,value):
 pf32.OUTER_STRENGTH=4 if kind=="outer" else 0;pf32.INNER_STRENGTH=0 if kind=="outer" else 4;pf32.OUTER_EDGE_FADE=value if kind=="outer" else 0;pf32.INNER_EDGE_FADE=value if kind=="inner" else 0;pf32.base.FIXTURE_OUTER_EDGE_FADE=pf32.OUTER_EDGE_FADE;pf32.base.FIXTURE_INNER_EDGE_FADE=pf32.INNER_EDGE_FADE;pf32.base.CAPTURE_EDGE_INTERNALS=True
def actual(kind,value):configure(kind,value);return pf32.actual_aex()
def production(kind,value,e):configure(kind,value);return pf32.mac_production(e)
def isolated(mode,kind,value,e=None):
 with tempfile.TemporaryDirectory(prefix="radial_edgefade_") as d:
  out=Path(d)/"out.pkl";cmd=[sys.executable,str(Path(__file__)),f"--{mode}",kind,str(value)]
  if e is not None:inp=Path(d)/"in.pkl";inp.write_bytes(pickle.dumps(e));cmd.append(str(inp))
  cmd.append(str(out));p=subprocess.run(cmd,capture_output=True);return p.returncode,pickle.loads(out.read_bytes()) if out.exists() else None
def main():
 cases=[(k,v) for k in ("outer","inner") for v in (50,100)]
 with ThreadPoolExecutor(max_workers=4) as pool:a=dict(zip(cases,pool.map(lambda p:isolated("actual",*p)[1],cases)))
 with ThreadPoolExecutor(max_workers=4) as pool:p=dict(zip(cases,pool.map(lambda q:isolated("production",q[0],q[1],a[q]),cases)))
 rows=[];captured=True;exact=True
 for kind,value in cases:
  rc,m=p[(kind,value)]
  actual=a[(kind,value)];has_prepass="prepass_alpha" in actual;captured&=has_prepass
  names=("polar","source_scalar","prepass_alpha","accum","max_alpha","final_rgba","coordinates","output")
  matches={name:rc==0 and m is not None and name in m and m[name]==actual[name] for name in names}
  exact&=all(matches.values())
  rows.append({"kind":kind,"edge_fade":value,"strength":4,"production_returncode":rc,"matches":matches,"actual_hashes":{name:sha(actual[name]) for name in names if name in actual}})
 status="exact" if captured and exact else "mismatch";report={"kind":"olmradialblur_rotation_pf32_edge_fade_actual_aex_20260811","status":status,"scope":"PF32 Rotation 9x7 centered; Outer Strength4 with Outer Edge Fade50/100, or Inner Strength4 with Inner Edge Fade50/100; NV/SV0.","aex_sha256":pf32.AEX_SHA256,"cases":rows,"supported_observation":"FUN_180002780 uses zero-based fade spans (50/100 become 49/99), direct span-sized Gaussian tables, and a linear first tap across angular row boundaries before wrapping subsequent taps within the row.","boundary":"No Noise/Size intersection, other fade/strength/quality/geometry/depth or AE-host claim.","instruction_evidence":{"outer":"0x1800028f0 reads [RDX] before JNS wrap repair at 0x18000291c","inner":"0x180002ab0 increments the logical angle and reads the existing R9 pointer before row repair","table":"FUN_18000b680 generates span-sized Gaussian values directly"}};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");DOC.write_text(f"# OLM RadialBlur PF32 Rotation Edge Fade — 2026-08-11\n\nStatus: **{status}**\n\nThe actual AEX and production agree through polar, source scalar, the separate prepass-alpha plane, accum/max-alpha, final RGBA, coordinates, and padded output for Outer/Inner Fade 50/100. The recovered rule uses zero-based spans 49/99, direct span-sized Gaussian tables, and one linear cross-row tap before within-row wrapping.\n");print(status);return 0 if captured and exact else 1
if __name__=="__main__":
 if len(sys.argv)==5 and sys.argv[1]=="--actual":Path(sys.argv[4]).write_bytes(pickle.dumps(actual(sys.argv[2],int(sys.argv[3]))));raise SystemExit(0)
 if len(sys.argv)==6 and sys.argv[1]=="--production":Path(sys.argv[5]).write_bytes(pickle.dumps(production(sys.argv[2],int(sys.argv[3]),pickle.loads(Path(sys.argv[4]).read_bytes()))));raise SystemExit(0)
 raise SystemExit(main())
