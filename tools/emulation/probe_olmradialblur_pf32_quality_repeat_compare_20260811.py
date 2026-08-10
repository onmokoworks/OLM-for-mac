#!/usr/bin/env python3
"""Probe-only PF32 Quality x Repeat owner/typed comparison."""
from __future__ import annotations

import hashlib, inspect, json, pickle, struct, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as support

REPORT = ROOT / "refs/conformance/olmradialblur_pf32_quality_repeat_compare_20260811.json"
CELLS = [(mode, 32, w, h, quality, repeat)
         for mode in ("zoom", "rotation")
         for w, h in ((9, 7), (32, 18))
         for quality in (1.0, 3.0, 5.0)
         for repeat in (0, 1)]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configure(cell):
    mode, depth, w, h, quality, repeat = cell
    target, frame, rb, cx, cy = support.configure((mode, depth, w, h, 0.0, 0.0, 1.0))
    m = target.fixture.m4 if mode == "zoom" else target.base.m4
    if mode == "rotation":
        target.base.FIXTURE_QUALITY = quality
    previous = m.install_reader_detours

    def install(loader, params):
        params = dict(params)
        params["Quality"] = quality
        params["Repeat Border"] = repeat
        return previous(loader, params)

    m.install_reader_detours = install
    return target, frame, rb, cx, cy


def capture(cell):
    target, *_ = configure(cell)
    return target.actual_aex()


def isolated(cell):
    key = "_".join(str(value).replace(".", "p") for value in cell)
    cache = Path("/tmp") / f"olmradial_pf32_qr_v3_{key}.pkl"
    if cache.exists():
        return 0, pickle.loads(cache.read_bytes())
    with tempfile.TemporaryDirectory(prefix="radial_pf32_qr_") as raw:
        out = Path(raw) / "capture.pkl"
        p = subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(out)])
        result = pickle.loads(out.read_bytes()) if out.exists() else None
        if p.returncode == 0 and result is not None:
            cache.write_bytes(pickle.dumps(result))
        return p.returncode, result


def patched_source(path: Path):
    path.write_text((ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp").read_text())


# Reuse the established production harness while substituting this matrix's
# tuple shape and values. The generated C++ still includes only a temporary copy.
_production_source = inspect.getsource(support.production)
_production_source = _production_source.replace(
    "mode,depth,w,h,ox,oy,gain=cell", "mode,depth,w,h,quality,repeat=cell;gain=1.0")
_production_source = _production_source.replace(
    "angular,radius=struct.unpack(\"<II\",expected[\"geometry\"]); cells=angular*radius",
    "angular,radius=struct.unpack(\"<II\",expected[\"geometry\"]); angular=int(quality*360) if mode=='rotation' else angular; cells=angular*radius")
_production_source = _production_source.replace("i.repeat_border=TRUE", "i.repeat_border={bool(repeat) and 'TRUE' or 'FALSE'}")
_production_source = _production_source.replace("i.quality=5", "i.quality={quality}")
exec(_production_source, globals())


def first_diff(actual: bytes, produced: bytes):
    offsets = [i for i, (a, b) in enumerate(zip(actual, produced)) if a != b]
    if len(actual) != len(produced):
        offsets.extend(range(min(len(actual), len(produced)), max(len(actual), len(produced))))
    return {"different_bytes": len(offsets), "first_byte": offsets[0] if offsets else None,
            "first_indices": offsets[:16]}


def visible_output(raw: bytes, width: int, height: int) -> bytes:
    rowbytes = width * 16 + 16
    return b"".join(raw[y * rowbytes:y * rowbytes + width * 16] for y in range(height))


def main() -> int:
    with ThreadPoolExecutor(max_workers=6) as pool:
        captured = list(pool.map(isolated, CELLS))
    actuals = {cell: result for cell, (rc, result) in zip(CELLS, captured) if rc == 0 and result}
    rows = []
    for cell in CELLS:
        mode, depth, w, h, quality, repeat = cell
        actual = actuals.get(cell)
        if actual is None:
            rows.append({"mode": mode, "geometry": [w, h], "quality": quality,
                         "repeat_border": bool(repeat), "captured": False, "exact": False})
            continue
        produced = production(cell, actual)
        planes = (("pre_blur", "post_blur", "output") if mode == "zoom" else
                  ("polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates", "output"))
        differences = {
            name: first_diff(
                visible_output(actual[name], w, h) if name == "output" else actual[name],
                visible_output(produced[name], w, h) if name == "output" else produced[name])
            for name in planes}
        exact = all(value["different_bytes"] == 0 for value in differences.values())
        rows.append({"mode": mode, "depth": depth, "geometry": [w, h], "quality": quality,
                     "repeat_border": bool(repeat), "captured": True, "exact": exact,
                     "matches": {name: differences[name]["different_bytes"] == 0 for name in planes},
                     "differences": differences,
                     "actual_sha256": {name: sha(actual[name]) for name in planes},
                     "production_sha256": {name: sha(produced[name]) for name in planes}})
        print(cell, exact, {k: v for k, v in differences.items() if v["different_bytes"]}, flush=True)
    exact_count = sum(row["exact"] for row in rows)
    report = {"kind": "olmradialblur_pf32_quality_repeat_compare_20260811",
              "status": "exact" if exact_count == len(CELLS) else "mismatch",
              "scope": "PF32 Zoom/Rotation owner vs temporary typed admission; 9x7/32x18, Quality{1,3,5}, Repeat Border{off,on}, centered neutral tuple.",
              "exact_cases": exact_count, "total_cases": len(CELLS), "cases": rows,
              "admitted_rules": {
                  "angular_count": "Quality * 360",
                  "quality3_forward_step": "f32(1 / f32(f32(Q * 180) / float(pi)))",
                  "rotation_quality3_inverse_scale": "f32(f32(Q * 180) / float(pi))",
                  "rotation_fixed_outer_span": "ceil(effective_length * Quality / 5)",
                  "zoom_repeat_off_span": "1.0f",
                  "rotation_repeat_off_source_scalar": "eligible ? 1.0f : 0.0f",
                  "output_comparison": "visible PF32 pixels only; host row padding is not effect output"},
              "boundary": "Bounded shared-production admission only; other depths, geometries, controls and AE-host behavior remain unproved."}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "exact": exact_count, "total": len(CELLS)}))
    return 0 if exact_count == len(CELLS) else 1


if __name__ == "__main__":
    if len(sys.argv) == 9 and sys.argv[1] == "--capture":
        values = sys.argv[2:-1]
        cell = (values[0], int(values[1]), int(values[2]), int(values[3]), float(values[4]), int(values[5]))
        Path(sys.argv[-1]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
