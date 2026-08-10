#!/usr/bin/env python3
"""Actual-AEX differential for centered Inner Offset pairwise cells."""
from __future__ import annotations

import hashlib, inspect, json, pickle, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base

CELLS = [(effect, depth, w, h, mode, offset)
         for effect in ("zoom", "rotation") for depth in (8, 16, 32)
         for w, h in ((9, 7), (32, 18))
         for mode in (2, 3) for offset in (2, 4)]
REPORT = base.ROOT / "refs/conformance/olmradialblur_inner_offset_pairwise_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")


def configure(cell):
    effect, depth, w, h, mode, offset = cell
    target, frame, rb, cx, cy = base.configure((effect, depth, w, h, 0., 0., 1.))
    # Also set fixture globals where they exist, then override at the final
    # parameter-reader boundary.  The latter is the authoritative owner input.
    owner = target.base if effect == "rotation" and depth == 32 else target
    owner.OUTER_STRENGTH = 0
    owner.INNER_STRENGTH = 4
    m = target.fixture.m4 if effect == "zoom" else (target.base.m4 if depth == 32 else target.m4)
    old = m.install_reader_detours
    def install(loader, params):
        params = dict(params)
        params.update({"Outer Strength": 0, "Inner Strength": 4,
                       "Inner Offset Mode": mode, "Inner Offset": offset})
        return old(loader, params)
    m.install_reader_detours = install
    return target, frame, rb, cx, cy


def capture(cell):
    target, *_ = configure(cell)
    return target.actual_aex()


def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_inner_offset_") as raw:
        p = Path(raw) / "capture.pkl"
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(p)], check=True)
        return pickle.loads(p.read_bytes())


def patched_source(path):
    path.write_text((base.ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp").read_text())


source = inspect.getsource(base.production)
source = source.replace("def production(cell, expected):", "def production_inner(cell, expected):")
source = source.replace("mode,depth,w,h,ox,oy,gain=cell;", "effect,depth,w,h,inner_mode,inner_offset=cell;mode=effect;ox=oy=0.;gain=1.;")
source = source.replace("mode,depth,w,h,ox,oy,gain=cell; _,frame,rb,cx,cy=configure(cell)",
                        "effect,depth,w,h,inner_mode,inner_offset=cell;mode=effect;ox=oy=0.;gain=1.; _,frame,rb,cx,cy=configure(cell)")
source = source.replace("i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;",
                        "i.outer_strength=0;i.inner_strength=4;i.outer_offset_mode=1;i.inner_offset_mode={inner_mode};i.inner_offset={inner_offset};")
namespace = dict(base.__dict__)
namespace["configure"] = configure
namespace["patched_source"] = patched_source
exec(source, namespace)
production_inner = namespace["production_inner"]


def first_difference(a, b):
    n = min(len(a), len(b))
    at = next((i for i in range(n) if a[i] != b[i]), n)
    return {"byte_offset": at, "actual": a[at:at+8].hex(), "production": b[at:at+8].hex(),
            "actual_size": len(a), "production_size": len(b)}


def main():
    exact = 0
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        actuals = dict(zip(CELLS, pool.map(isolated, CELLS)))
    for cell in CELLS:
        actual = actuals[cell]
        prod = production_inner(cell, actual)
        planes = (("pre_blur", "post_blur", "output") if cell[0] == "zoom" else
                  ("polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates", "output"))
        matches = {p: prod[p] == actual[p] for p in planes}
        exact += all(matches.values())
        residual = next((f"{p}:{first_difference(actual[p], prod[p])}" for p in planes if not matches[p]), "")
        rows.append({"effect": cell[0], "depth": cell[1], "geometry": list(cell[2:4]),
                     "inner_offset_mode": cell[4], "inner_offset_ui": cell[5],
                     "matches": matches, "exact": all(matches.values()),
                     "first_residual": residual or None,
                     "actual_sha256": {p: hashlib.sha256(actual[p]).hexdigest() for p in planes}})
        print(cell, all(matches.values()), matches, residual, flush=True)
    print(f"exact={exact}/{len(CELLS)}")
    status = "exact" if exact == len(CELLS) else "mismatch"
    report = {"kind": "olmradialblur_inner_offset_pairwise_actual_aex_20260811",
              "status": status, "exact_cases": exact, "total_cases": len(CELLS),
              "aex": {"path": str(base.rotation.m4.AEX_PATH),
                      "sha256": hashlib.sha256(Path(base.rotation.m4.AEX_PATH).read_bytes()).hexdigest()},
              "scope": "Zoom/Rotation PF8/PF16/PF32, centered 9x7/32x18, Inner Strength 4, Inner Offset Mode 2/3, UI Offset 2/4, Outer Strength 0, neutral fades/ratio/angle/quality/repeat/brightness/noise.",
              "rules": {"zoom": "For the enumerated cells the owner retains the Inner Strength 4 worker result; modes and offsets do not change captured post_blur/output.",
                        "rotation": "UI offset is decremented once and radius-scaled. Mode 2 takes max(fixed Inner Strength worker span, dynamic span); Mode 3 selects dynamic span directly."},
              "boundary": "Only the 48 enumerated actual-owner and typed cells are admitted; other strengths, offsets, modes, geometries and parameter intersections remain fail-closed.",
              "cases": rows}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(f"# OLM RadialBlur Inner Offset pairwise — 2026-08-11\n\nStatus: **{status}** ({exact}/{len(CELLS)})\n\nZoom/Rotation、PF8/PF16/PF32、9×7/32×18で、Inner Strength 4、Offset Mode 2/3、UI Offset 2/4をactual AEX内部planeとtyped outputで比較しました。Zoomは列挙範囲でStrength 4 worker結果を維持します。RotationはUI offsetを1減算後に半径依存でscaleし、Mode 2は固定spanとのmax、Mode 3は動的spanを直接使用します。列挙外はfail-closeです。\n")
    return exact != len(CELLS)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--capture":
        v = sys.argv[2:-1]
        cell = (v[0], int(v[1]), int(v[2]), int(v[3]), int(v[4]), int(v[5]))
        Path(sys.argv[-1]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
