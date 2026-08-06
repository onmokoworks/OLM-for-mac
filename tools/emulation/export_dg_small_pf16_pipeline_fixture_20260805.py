#!/usr/bin/env python3
"""Capture a same-shape 17x11 fieldgen->PF16 compose pipeline from the AEX."""

from __future__ import annotations

import hashlib, json, struct
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
from export_dg_fieldgen_fixture import run_aex_fieldgen, sha256_file
from test_dg_fieldgen_p1b import make_mask
from test_dg_compose import (
    make_loader, build_world, call_compose, alloc_refcon,
    OFF_SRC_WORLD_PTR, OFF_FIELD_WORLD_PTR, OFF_DEGENERATE, OFF_USE_BG,
    OFF_INVERT, OFF_INOUT_MODE, OFF_RENDER_MODE, OFF_INTERP_MODE, OFF_POWER,
    OFF_GRAD_G, OFF_GRAD_R, OFF_GRAD_B, OFF_BG_G, OFF_BG_R, OFF_BG_B,
)

OUT = HERE / "fixtures/distancegradation_pipeline_pf16_17x11_threshold4_linear_inside"
AEX = ROOT / "plugins_2025/DistanceGradation.aex"

def desc(name: str, data: bytes) -> dict:
    return {"blob": name, "offset": 0, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def main() -> int:
    if OUT.exists():
        raise SystemExit(f"fixture exists: {OUT}")
    OUT.mkdir(parents=True)
    w, h = 17, 11
    mask = make_mask(w, h)
    field, trace = run_aex_fieldgen(mask, 4, 0)
    # The PF16 typed callback reads the staged field green word at 1/32768.
    words = np.rint(np.clip(field, 0, 1) * 32768.0).astype("<u2")
    loader = make_loader()
    src_pixels, field_pixels = {}, {}
    for y in range(h):
        for x in range(w):
            if mask[y, x] != 0: src_pixels[(x, y)] = (32768, 0, 0, 0)
            field_pixels[(x, y)] = (0, int(words[y, x]), 0, 0)
    src_world = build_world(loader, w, h, src_pixels)
    field_world = build_world(loader, w, h, field_pixels)
    ref = alloc_refcon(loader)
    def put(off, fmt, value): loader.write_bytes(ref + off, struct.pack(fmt, value))
    put(OFF_SRC_WORLD_PTR, "<Q", src_world); put(OFF_FIELD_WORLD_PTR, "<Q", field_world)
    put(OFF_DEGENERATE, "<B", 0); put(OFF_USE_BG, "<B", 1); put(OFF_INVERT, "<B", 1)
    put(OFF_INOUT_MODE, "<i", 1); put(OFF_RENDER_MODE, "<i", 1); put(OFF_INTERP_MODE, "<i", 1); put(OFF_POWER, "<f", 1.0)
    put(OFF_GRAD_G, "<f", 0.0); put(OFF_GRAD_R, "<f", 28/255); put(OFF_GRAD_B, "<f", 238/255)
    put(OFF_BG_G, "<f", 0.0); put(OFF_BG_R, "<f", 1.0); put(OFF_BG_B, "<f", 0.0)
    output = bytearray()
    for y in range(h):
        for x in range(w): output += struct.pack("<4H", *call_compose(loader, ref, x, y))
    source = bytearray()
    for y in range(h):
        for x in range(w): source += struct.pack("<4H", *(src_pixels.get((x,y), (0,0,0,0))))
    blobs = {"source_agrb16.bin": bytes(source), "field_f32.bin": field.astype("<f4").tobytes(), "field_pf16.bin": words.tobytes(), "output_agrb16.bin": bytes(output)}
    for n,b in blobs.items(): (OUT/n).write_bytes(b)
    manifest = {
      "schema":"olm.aex.cpu-pipeline-fixture/1", "case_id":"distancegradation.pipeline.pf16.17x11.threshold4.linear.inside",
      "scope":"same-shape fieldgen -> nearest-even PF16 staging -> compose/store", "width":w,"height":h,"threshold":4,"param8":0,
      "params":{"invert":1,"in_out":1,"render_mode":1,"use_bg":1,"interp_mode":1,"power":1.0,"grad_rgb_u8":[28,0,238],"bg_rgb_u8":[255,0,0]},
      "provenance":{"oracle":"unicorn-aex","binary_sha256":sha256_file(AEX),"field_function":"0x181174760","compose_function":"0x181170480","execution":trace},
      "blobs":{n:desc(n,b) for n,b in blobs.items()},
      "exclusions":["host resize","blur","After Effects checkout/export"]}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(OUT)
    return 0
if __name__ == "__main__": raise SystemExit(main())
