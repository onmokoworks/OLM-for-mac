#!/usr/bin/env python3
"""Capture the bounded Mode4 gradient Highlight two-word PF32 seam."""
from __future__ import annotations
import importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"tools/emulation/probe_olmkirakira_mode4_fullcaller_scaffold_20260807.py"
SINGLE=ROOT/"refs/conformance/olmkirakira_mode4_natural_fullframe_exact_20260811.json"
OUT=ROOT/"refs/conformance/olmkirakira_mode4_highlight_gradient_pf32_seam_20260812.json"
DOC=OUT.with_suffix(".md")
def load():
 s=importlib.util.spec_from_file_location("k",BASE);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main()->int:
 m=load()
 try:
  m.main(natural=True,natural_slot=4,natural_length=3,highlight_gradient=True,allow_ray_mismatch=True)
  r=json.loads(SINGLE.read_text()); diffs=r["actual_aex"]["ray_differences"]
  typed=r["actual_aex"]["typed_outputs"]
  valid=(len(r["actual_aex"]["same_run_seed_f32"])==15 and
         [(x["word"],x["ulp"]) for x in diffs]==[(3,1),(11,1)] and
         len(r["actual_aex"]["aggregation_u32"])==60 and
         all(v["actual_hex"]==v["portable_hex"] for v in typed.values()))
  r.update(kind="olmkirakira_mode4_highlight_gradient_pf32_seam",date="2026-08-12",
           status="fail_closed_pf32_seam" if valid else "unexpected")
  r["first_difference"]={"stage":"highlight_isotropic_box_blur_ray","words":[3,11],"ulp":[1,1],
    "rejected":"Changing the general accumulator from double to float increases the mismatch from 2 to 8 words; no fixture correction is admitted."}
  r["controls"]={"constant_highlight":"15/15 ray words and PF8/PF16/PF32 exact",
    "gradient_downstream":"actual ray -> aggregate 15 pixels -> PF8/PF16/PF32 writer oracle exact"}
  OUT.write_text(json.dumps(r,indent=2)+"\n")
  DOC.write_text("# OLMKiraKira Mode4 Highlight gradient PF32 seam（2026-08-12）\n\nStatus: **"+r["status"]+"**\n\n5×3 gradientのsame-run seed 15 wordsからHighlight rayで初めてword 3/11が各1 ULPずれる。actual ray以後のaggregate 15 pixelsとPF8/PF16/PF32 writerはexact。constant Highlight controlも全段exact。一般boxFilter則を回収できていないためproductionは変更せずPF32 gradientをfail-closeする。\n")
  print(json.dumps({"status":r["status"],"ray_differences":diffs}))
  return 0 if valid else 1
 finally:
  m.main(natural=True,natural_slot=1,natural_length=5,natural_rotation=0)
if __name__=="__main__":raise SystemExit(main())
