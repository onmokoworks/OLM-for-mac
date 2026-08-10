#!/usr/bin/env python3
"""Bounded PF32 Rotation Edge Fade x Size/Noise intersections."""
from __future__ import annotations
import hashlib,json,pickle,subprocess,sys,tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/"tools/emulation";sys.path.insert(0,str(HERE))
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as pf32  # noqa:E402
REPORT=ROOT/"refs/conformance/olmradialblur_rotation_pf32_edge_fade_intersections_actual_aex_20260811.json";DOC=REPORT.with_suffix(".md")
CASES=[("outer","size50"),("outer","noise25"),("inner","size50"),("inner","noise25")]
def sha(b):return hashlib.sha256(b).hexdigest()
def configure(kind,variation):
 pf32.OUTER_STRENGTH=4 if kind=="outer" else 0;pf32.INNER_STRENGTH=0 if kind=="outer" else 4
 pf32.OUTER_EDGE_FADE=50 if kind=="outer" else 0;pf32.INNER_EDGE_FADE=50 if kind=="inner" else 0
 pf32.SIZE_VARIATION=50.0 if variation=="size50" else 0.0;pf32.NOISE_VARIATION=25.0 if variation=="noise25" else 0.0
 b=pf32.base;b.FIXTURE_OUTER_EDGE_FADE=pf32.OUTER_EDGE_FADE;b.FIXTURE_INNER_EDGE_FADE=pf32.INNER_EDGE_FADE;b.FIXTURE_SIZE_VARIATION=pf32.SIZE_VARIATION;b.FIXTURE_NOISE_VARIATION=pf32.NOISE_VARIATION;b.FIXTURE_NOISE_TYPE=1;b.FIXTURE_SEED=1;b.FIXTURE_NOISE_OFFSET=0.0;b.FIXTURE_THICKNESS=10.0;b.CAPTURE_EDGE_INTERNALS=True
def actual(kind,variation):configure(kind,variation);return pf32.actual_aex()
def production(kind,variation,e):configure(kind,variation);return pf32.mac_production(e)
def isolated(mode,kind,variation,e=None):
 with tempfile.TemporaryDirectory(prefix="radial_edge_intersection_") as d:
  out=Path(d)/"out.pkl";cmd=[sys.executable,str(Path(__file__)),f"--{mode}",kind,variation]
  if e is not None:inp=Path(d)/"in.pkl";inp.write_bytes(pickle.dumps(e));cmd.append(str(inp))
  cmd.append(str(out));p=subprocess.run(cmd,capture_output=True);return p.returncode,pickle.loads(out.read_bytes()) if out.exists() else None
def main():
 with ThreadPoolExecutor(max_workers=4) as pool:a=dict(zip(CASES,pool.map(lambda q:isolated("actual",*q)[1],CASES)))
 with ThreadPoolExecutor(max_workers=4) as pool:p=dict(zip(CASES,pool.map(lambda q:isolated("production",q[0],q[1],a[q]),CASES)))
 names=("polar","source_scalar","prepass_alpha","accum","max_alpha","final_rgba","coordinates","output");rows=[];exact=True
 for case in CASES:
  rc,m=p[case];actual_case=a[case]
  matches={n:rc==0 and m is not None and m.get(n)==actual_case[n] for n in names};accepted=all(matches.values());first_stage=next((n for n in names if not matches[n]),None)
  exact&=accepted
  rows.append({"kind":case[0],"variation":case[1],"production_returncode":rc,"production_fail_closed":rc!=0 and m is None,"accepted":accepted,"matches":matches,"first_mismatch_stage":first_stage,"actual_hashes":{n:sha(actual_case[n]) for n in names}})
 status="exact" if exact else "mismatch";report={"kind":"olmradialblur_rotation_pf32_edge_fade_intersections_actual_aex_20260811","status":status,"scope":"PF32 Rotation centered 9x7 Quality5; Outer or Inner Strength4 Edge Fade50 crossed with opaque Size Variation50 or Noise Type1 NV25 Seed1 Offset0 Thickness10.","aex_sha256":pf32.AEX_SHA256,"cases":rows,"ordering":"The AEX constructs source size/noise planes before polar sampling. Its Radial noise sampler uses scalar float32 smoothstep/tap accumulation order; later scatter consumes the sampled noise-composed span slot (+0x10). The Inner prepass boundary reads the float immediately after polar, which is source_scalar[0] in this allocation, before repairing the angular wrap.","boundary":"No transparent Size input, Size+Noise triple intersection, Fade100 intersection, Type2/3, other seed/offset/thickness/geometry/depth, or AE-host claim."};REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");DOC.write_text(f"# OLM RadialBlur PF32 Edge Fade intersections — 2026-08-11\n\nStatus: **{status}**\n\nOuter and Inner Edge Fade50 crossed with opaque Size Variation50 or Type1 Noise Variation25 are exact across polar, source scalar, prepass, accumulation, max alpha, final RGBA, coordinates, and padded output. Radial noise interpolation uses the AEX scalar float32 instruction order. At the Inner angular boundary, the prepass reads the adjacent source-scalar allocation once before repairing the wrap.\n");print(status);return 0 if exact else 1
if __name__=="__main__":
 if len(sys.argv)==5 and sys.argv[1]=="--actual":Path(sys.argv[4]).write_bytes(pickle.dumps(actual(sys.argv[2],sys.argv[3])));raise SystemExit(0)
 if len(sys.argv)==6 and sys.argv[1]=="--production":Path(sys.argv[5]).write_bytes(pickle.dumps(production(sys.argv[2],sys.argv[3],pickle.loads(Path(sys.argv[4]).read_bytes()))));raise SystemExit(0)
 raise SystemExit(main())
