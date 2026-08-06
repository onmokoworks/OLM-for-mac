#!/usr/bin/env python3
"""Invalid count safety and full-surface checkout failure contracts."""

from __future__ import annotations

import hashlib, json, struct
from pathlib import Path
import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle
from test_colorkeep_max100_effectmain_actual_aex_20260805 import COLORS100, depth_pixels

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/"refs/conformance/colorkeep_invalid_counts_checkout_effectmain_20260805.json"

def materialize(colors,pixels):
    oracle.COLORS=tuple(colors); inputs={}; expected={}
    specs={"PF8":(0x180001580,"<4B",pixels["PF8"]),"PF16":(0x180001280,"<4H",pixels["PF16"]),"PF32":(0x180001850,"<4f",pixels["PF32"])}
    for d,(e,f,p) in specs.items():
        inputs[d]=b"".join(b"".join(struct.pack(f,*p[(y*4+x)%len(p)]) for x in range(4))+b"\xcc"*8 for y in range(3))
        expected[d]=oracle.actual_frame(e,f,p)
    return inputs,expected

def target(e): return e["PF8"]+e["PF16"]+e["PF8"]+e["PF16"]+e["PF32"]

def main():
    base=tuple(COLORS100[:5]); pix=depth_pixels(base,(0,3,4)); inputs,_=materialize(base,pix)
    # Missing Color index 57: legacy paths are unaffected; all Smart paths
    # return 77 before iterate, leaving their 0xEE output worlds immutable.
    normal_colors=oracle.COLORS
    _,legacy_expected=materialize(base,pix)
    oracle.COLORS=normal_colors
    failed=adapter.compile_and_run(inputs,fail_index=57)
    sizes={"PF8":72,"PF16":120,"PF32":216}
    fail_target=legacy_expected["PF8"]+legacy_expected["PF16"]+b"\xee"*sizes["PF8"]+b"\xee"*sizes["PF16"]+b"\xee"*sizes["PF32"]
    assert failed==fail_target
    # Negative is safely normalized to zero by production. Compare against
    # fresh actual-worker count=0 oracles, never against an unsafe OOB state.
    oracle.COLORS=(); zero_expected={}
    for d,(e,f,p) in {"PF8":(0x180001580,"<4B",pix["PF8"]),"PF16":(0x180001280,"<4H",pix["PF16"]),"PF32":(0x180001850,"<4f",pix["PF32"])}.items(): zero_expected[d]=oracle.actual_frame(e,f,p)
    oracle.COLORS=base
    negative=adapter.compile_and_run(inputs,enabled_count=-1)
    assert negative==target(zero_expected)
    # >100 is safely normalized to the public maximum and compared with a
    # fresh count=100 actual-worker oracle.
    p100=depth_pixels(COLORS100,(0,99)); i100,e100=materialize(COLORS100,p100)
    over=adapter.compile_and_run(i100,enabled_count=101)
    assert over==target(e100)
    report={"status":"exact","production_change":"SmartRender always checks out Color[0..99], matching actual FUN_180001a90 dependency preparation","checkout_failure":{"failing_parameter_index":57,"return_code":77,"ordered_checkout_indices":list(range(1,58)),"smart_output":"fully unchanged including padding","legacy_output":"normal"},"invalid_counts":{"negative":{"production":"clamp to 0","oracle":"fresh actual worker count=0"},"above_100":{"production":"clamp to 100","oracle":"fresh actual worker count=100"},"actual_aex_effectmain_fact":"FUN_180001a90 stores the raw count; >100 would make the worker read beyond its 100-color local buffer and is therefore not adopted as a compatibility behavior"},"depths":["PF8","PF16","PF32"],"normal_100_regression":"covered separately by colorkeep_max100_effectmain_actual_aex_20260805","combined_sha256":hashlib.sha256(failed+negative+over).hexdigest(),"not_proven":["After Effects host execution/export","unsafe out-of-bounds behavior for forged count >100"]}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps(report,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
