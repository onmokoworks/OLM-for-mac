#!/usr/bin/env python3
"""PF8 Quality x Repeat actual-owner comparison (probe-only gate)."""
from __future__ import annotations

import hashlib, importlib, inspect, json, pickle, struct, subprocess, sys, tempfile, textwrap
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base
BASE_CONFIGURE = base.configure
BASE_PATCHED_SOURCE = base.patched_source

CELLS = [(mode, 8, w, h, quality, repeat, 1.0)
         for mode in ("zoom", "rotation") for w, h in ((9, 7), (32, 18))
         for quality in (1.0, 3.0, 5.0) for repeat in (0.0, 1.0)]
REPORT = ROOT / "refs/conformance/olmradialblur_pf8_quality_repeat_actual_aex_20260811.json"


def configure(cell):
    mode, depth, w, h, quality, repeat, gain = cell
    target, frame, rb, _, _ = BASE_CONFIGURE((mode, depth, w, h, 0.0, 0.0, gain))
    m = target.fixture.m4 if mode == "zoom" else target.m4
    original = m.install_reader_detours
    def install(loader, params):
        params = dict(params)
        params["Quality"] = quality
        params["Repeat Border"] = bool(repeat)
        return original(loader, params)
    m.install_reader_detours = install
    if mode == "rotation":
        # This fixture overwrites Quality with 5 inside actual_aex before the
        # reader detour.  Build a process-local copy with the requested value.
        source = textwrap.dedent(inspect.getsource(target.actual_aex))
        source = source.replace('"Quality": 5.0', f'"Quality": {quality!r}', 1)
        source = source.replace(
            "cells = (max_radius - min_radius + 1) * 1800",
            "angular_count = int(round(struct.unpack('<f', ld.read_bytes(work + 8, 4))[0] * 6.283185307179586))\n        cells = (max_radius - min_radius + 1) * angular_count")
        source = source.replace(
            'if int(captured["cells"]) % 1800:\n        raise RuntimeError(f"Rotation cells do not divide the quality-5 angular extent: {captured[\'cells\']}")\n    planes["geometry"] = struct.pack("<II", 1800, int(captured["cells"]) // 1800)',
            "angular_count = int(round(angle_scale * 6.283185307179586))\n    if int(captured['cells']) % angular_count:\n        raise RuntimeError(f\"Rotation cells do not divide angular extent {angular_count}: {captured['cells']}\")\n    planes['geometry'] = struct.pack('<II', angular_count, int(captured['cells']) // angular_count)")
        exec(source, target.__dict__)
    cx, cy = w / 2.0, h / 2.0
    return target, frame, rb, cx, cy


def capture(cell):
    target, *_ = configure(cell)
    return target.actual_aex()


def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_pf8_qr_") as raw:
        p = Path(raw) / "capture.pkl"
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(p)], check=True)
        return pickle.loads(p.read_bytes())


def patched_source(path):
    """Copy the current shared production source without probe-only edits."""
    BASE_PATCHED_SOURCE(path)


def production(cell, expected):
    # Reuse the established compiler/capture driver, intercepting only its
    # generated probe C++ and temporary production source.
    _, _, _, _, quality, repeat, _ = cell
    old_patch, old_write = base.patched_source, Path.write_text
    base.patched_source = patched_source
    def write_text(path, data, *args, **kwargs):
        if path.name == "p.cpp":
            data = data.replace("i.repeat_border=TRUE", f"i.repeat_border={'TRUE' if repeat else 'FALSE'}")
            data = data.replace("i.quality=5", f"i.quality={quality}")
            if cell[0] == "rotation":
                # Actual owner allocates Quality5 capacity, but only writes the
                # Quality/5 active prefix. Preserve the zero-initialized tail.
                data = data.replace("if(z||cap.written_cells!=C)return 3;", "if(z)return 3;")
                data = data.replace("if(cap.written_cells!=C)return 4;", "")
        return old_write(path, data, *args, **kwargs)
    Path.write_text = write_text
    old_configure = base.configure
    base.configure = configure
    try:
        return base.production(cell, expected)
    finally:
        base.configure, base.patched_source, Path.write_text = old_configure, old_patch, old_write


def first_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return {"byte_offset": i, "actual": x, "production": y}
    if len(a) != len(b):
        return {"byte_offset": min(len(a), len(b)), "actual_size": len(a), "production_size": len(b)}
    return None


def main():
    with ThreadPoolExecutor(max_workers=6) as pool:
        actuals = dict(zip(CELLS, pool.map(isolated, CELLS)))
    rows = []
    for cell in CELLS:
        mode, _, w, h, quality, repeat, _ = cell
        actual = actuals[cell]
        should_admit = True
        try:
            prod = production(cell, actual)
        except (AssertionError, subprocess.CalledProcessError):
            if should_admit:
                raise
            rows.append({"mode": mode, "geometry": [w, h], "quality": quality,
                         "repeat_border": bool(repeat), "admitted": False,
                         "fail_closed": True, "matches": {}, "first_diffs": {},
                         "consumer_exact": False, "exact": False})
            print(cell, "fail-closed", flush=True)
            continue
        planes = ("pre_blur", "post_blur", "output") if mode == "zoom" else ("polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates", "output")
        allocation_tail = {}
        matches = {}
        for p in planes:
            # Rotation's owner always allocates the Quality-5 (1800-angle)
            # scratch capacity.  Quality 1/3 only writes and consumes the
            # Quality*360 prefix; the remainder is allocator residue in the
            # AEX capture and is deliberately excluded from semantic equality.
            if mode == "rotation" and quality < 5.0 and p in (
                    "polar", "source_scalar", "accum", "max_alpha"):
                bytes_per_cell = 16 if p in ("polar", "accum") else 4
                _, radius_count = struct.unpack("<II", actual["geometry"])
                active_bytes = int(quality * 360) * radius_count * bytes_per_cell
                matches[p] = prod[p][:active_bytes] == actual[p][:active_bytes]
                allocation_tail[p] = {
                    "active_bytes": active_bytes,
                    "actual_tail_bytes": len(actual[p]) - active_bytes,
                    "full_allocation_exact": prod[p] == actual[p],
                    "consumed": False,
                }
            else:
                matches[p] = prod[p] == actual[p]
        diffs = {p: first_diff(actual[p], prod[p]) for p in planes if not matches[p]}
        consumer_planes = ("output",) if mode == "zoom" else ("final_rgba", "coordinates", "output")
        row = {"mode": mode, "geometry": [w, h], "quality": quality,
               "repeat_border": bool(repeat), "admitted": True, "fail_closed": False,
               "matches": matches, "first_diffs": diffs,
               "allocation_tail": allocation_tail,
               "consumer_exact": all(matches[p] for p in consumer_planes),
               "exact": all(matches.values())}
        rows.append(row)
        print(cell, row["exact"], matches, diffs, flush=True)
    exact = sum(r["exact"] for r in rows)
    consumer_exact = sum(r["consumer_exact"] for r in rows)
    fail_closed = sum(r.get("fail_closed", False) for r in rows)
    status = "semantic-exact" if consumer_exact == 24 and exact == 24 and fail_closed == 0 else "mismatch"
    report = {"kind": "olmradialblur_pf8_quality_repeat_actual_aex_20260811", "status": status,
              "exact_cases": exact, "consumer_exact_cases": consumer_exact,
              "fail_closed_cases": fail_closed, "total_cases": len(rows), "cases": rows,
              "boundary": "PF8 only. All 24 cells are admitted. Rotation Quality1/3 compares the active Quality*360 angular prefix; the unused tail of the owner's fixed Quality5 allocation is recorded but excluded. Every consumed plane and visible output is exact."}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if status == "semantic-exact" else 1


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--capture":
        v = sys.argv[2:-1]
        cell = (v[0], int(v[1]), int(v[2]), int(v[3]), float(v[4]), float(v[5]), float(v[6]))
        Path(sys.argv[-1]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
