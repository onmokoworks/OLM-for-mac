#!/usr/bin/env python3
"""Deterministically relabel the preserved OLMBlur smoke observation."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OBS=ROOT/'refs/conformance/olmblur_classic_current_install_smoke_observed_raw_20260812.json'
OUT=ROOT/'refs/conformance/olmblur_classic_current_install_smoke_raw_20260812.json'
RUNNER=ROOT/'scripts/run_olmblur_classic_current_install_smoke_observed_20260812.py'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=json.loads(OBS.read_text())
 r['claim_boundary']='Fresh AE installed-path load, effect add, and default-parameter PF32 Software render only; no live classic PF8/PF16 pixel-exact or owner-route claim.'
 r['gates']['classic_pf8_pf16_live_pixel_exact_claim']=r['gates'].pop('lab76_live_pixel_exact_claim')
 r['provenance']={'observed_raw_sha256_before_semantic_label_sanitization':sha(OBS),'temporary_runner_sha256':sha(RUNNER),'sanitization':'Observation values are unchanged. Only ColorKey-template Lab76 claim labels were replaced with OLMBlur classic fail-closed labels before repository persistence.'}
 OUT.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()
