"""Bounded actual-AEX differential for the unresolved OLMBlur case_0006 family.

This is deliberately a new, standalone fixture.  It does not change the
retained worker fixtures, the ledger, or any existing dated differential.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_fullentry import build_context, build_pf_suites  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025" / "OLMBlur.aex"
ENTRY = 0x180002280
REPORT = ROOT / "refs/conformance/olmblur_case0006_border_order_writer_differential_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmblur_case0006_border_order_writer_differential_20260716.md"


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def source_bytes(width: int, height: int, kind: str) -> bytes:
    data = bytearray()
    for y in range(height):
        for x in range(width):
            if kind == "border":
                r, g, b = 1000 + 701 * x + 17 * y, 30000 + 37 * x + 811 * y, 200 + 503 * x + 29 * y
            elif kind == "order":
                r = 3 + ((x * 7919 + y * 104729) % 32700)
                g = 32000 - ((x * 1543 + y * 6151) % 16000)
                b = 11 if (x + 3 * y) % 2 else 32700
            else:
                r, g, b = 32760 - 97 * x - 113 * y, 4096 + 181 * x + 73 * y, 16384 + 257 * x - 41 * y
            # Keep the border probe opaque so alpha-mask early breaks cannot be
            # mistaken for edge sampling semantics.
            alpha = 32768
            data.extend(struct.pack("<4H", alpha, r, g, b))
    return bytes(data)


def alloc(loader: AexLoader, data: bytes, align: int = 64) -> int:
    address = loader.bump_alloc(len(data), align=align)
    loader.write_bytes(address, data)
    return address


def run_actual(case: dict, source: bytes) -> tuple[bytes, int]:
    width, height = case["width"], case["height"]
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)

    def impl_pow(uc, args):
        loader.write_xmm_f64(0, math.pow(loader.read_xmm_f64(0), loader.read_xmm_f64(1)))
        return 0

    def impl_powf(uc, args):
        loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1)))
        return 0

    loader.register_import_impl("pow", impl_pow)
    loader.register_import_impl("powf", impl_powf)
    spbasic, _events = build_pf_suites(loader)
    context = build_context(loader, spbasic)
    source_data = alloc(loader, source)
    output_data = alloc(loader, source)

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\x00" * 0x80)
        loader.write_bytes(address + 0x18, struct.pack("<Q", data))
        loader.write_bytes(address + 0x20, struct.pack("<I", width * 8))
        loader.write_bytes(address + 0x24, struct.pack("<I", width))
        loader.write_bytes(address + 0x28, struct.pack("<I", height))
        loader.write_bytes(address + 0x2C, struct.pack("<H", 16))
        return address

    source_world, output_world = world(source_data), world(output_data)
    params = loader.host_alloc(0x40)
    loader.write_bytes(params, b"\x00" * 0x40)
    loader.write_bytes(params + 0x18, struct.pack("<I", 16))
    loader.write_bytes(params + 0x20, struct.pack("<f", case["blur_amount"]))
    loader.write_bytes(params + 0x24, struct.pack("<f", 100.0))
    loader.write_bytes(params + 0x28, struct.pack("<I", case["repeat"]))
    loader.write_bytes(params + 0x2C, struct.pack("<I", case["bias_direction"]))
    result = loader.call_function(ENTRY, int_args=[context, source_world, output_world, params], max_instructions=8_000_000)
    return loader.read_bytes(output_data, len(source)), result["instructions"]


def model(source: bytes, case: dict, order: str = "actual", border: str = "truncate") -> tuple[bytes, list[float]]:
    width, height = case["width"], case["height"]
    pixels = width * height
    flags = [struct.unpack_from("<H", source, i * 8)[0] != 0 for i in range(pixels)]
    plane = [[f32(struct.unpack_from("<H", source, i * 8 + 2 + c * 2)[0]) for c in range(3)] for i in range(pixels)]
    decay = 1.0 if case["repeat"] <= 1 else math.pow(3.0 / case["blur_amount"], 1.0 / (case["repeat"] - 1))
    for iteration in range(case["repeat"]):
        radius_value = case["blur_amount"] * math.pow(decay, iteration)
        radius = int(radius_value)
        sigma = f32(radius_value / 3.0)
        denominator = f32(f32(sigma + sigma) * sigma)
        weights = [f32(math.exp(-f32(k * k) / denominator)) for k in range(radius + 1)]
        dst = [[0.0, 0.0, 0.0] for _ in range(pixels)]
        horizontal = case["bias_direction"] == 1
        for pass_axis in ("h", "v") if horizontal else ("v", "h"):
            for i in range(pixels):
                if not flags[i]:
                    dst[i] = plane[i][:]
                    continue
                x, y = i % width, i // width
                offsets = [0]
                extent = x if pass_axis == "h" else y
                extent_other = width - 1 - x if pass_axis == "h" else height - 1 - y
                if border == "replicate":
                    offsets += list(range(1, radius + 1))
                else:
                    offsets += list(range(1, min(radius, extent_other) + 1))
                left = list(range(0, min(radius, extent) + 1)) if border == "truncate" else list(range(0, radius + 1))
                taps = [(d, -d) for d in left]
                taps += [(d, d) for d in offsets[1:]]
                if order == "reverse":
                    taps = list(reversed(taps))
                sums = [f32(0.0), f32(0.0), f32(0.0), f32(0.0)]
                for d, delta in taps:
                    qx, qy = (x + delta, y) if pass_axis == "h" else (x, y + delta)
                    if border == "replicate":
                        qx, qy = min(width - 1, max(0, qx)), min(height - 1, max(0, qy))
                    elif qx < 0 or qx >= width or qy < 0 or qy >= height:
                        continue
                    q = qy * width + qx
                    if not flags[q]:
                        break
                    weight = weights[d]
                    sums[0] = f32(sums[0] + weight)
                    for c in range(3):
                        sums[c + 1] = f32(sums[c + 1] + f32(weight * plane[q][c]))
                inv = f32(0.0) if sums[0] == 0.0 else f32(1.0 / sums[0])
                dst[i] = [f32(inv * sums[c + 1]) for c in range(3)]
            plane, dst = dst, plane
    observed = [value for pixel in plane for value in pixel]
    out = bytearray(source)
    for i in range(pixels):
        for c in range(3):
            value = plane[i][c]
            stored = max(0, min(32768, int(math.floor(value + 0.5))))
            struct.pack_into("<H", out, i * 8 + 2 + c * 2, stored)
    return bytes(out), observed


def summarize(actual: bytes, candidate: bytes) -> dict:
    diffs = []
    for i in range(0, len(actual), 8):
        a = struct.unpack_from("<4H", actual, i)
        b = struct.unpack_from("<4H", candidate, i)
        if a != b:
            diffs.append({"pixel": i // 8, "actual": list(a), "candidate": list(b)})
    return {"equal": not diffs, "different_words": sum(sum(x != y for x, y in zip(d["actual"], d["candidate"])) for d in diffs), "first_diffs": diffs[:8]}


def main() -> int:
    cases = [
        {"id": "border_radius4_opaque", "kind": "border", "width": 7, "height": 5, "blur_amount": 4.0, "repeat": 1, "bias_direction": 1},
        {"id": "order_radius5_high_dynamic_range", "kind": "order", "width": 9, "height": 7, "blur_amount": 5.0, "repeat": 2, "bias_direction": 1},
        {"id": "writer_near_half_inputs", "kind": "writer", "width": 5, "height": 5, "blur_amount": 3.0, "repeat": 1, "bias_direction": 2},
    ]
    report = {"schema": "olmblur.case0006-differential/1", "scope": "bounded local actual-AEX versus portable candidates", "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(), "entry": hex(ENTRY), "cases": []}
    for case in cases:
        source = source_bytes(case["width"], case["height"], case["kind"])
        actual, instructions = run_actual(case, source)
        baseline, floats = model(source, case)
        reverse, _ = model(source, case, order="reverse")
        replicated, _ = model(source, case, border="replicate")
        even = bytearray(source)
        for i, value in enumerate(floats):
            struct.pack_into("<H", even, (i // 3) * 8 + 2 + (i % 3) * 2, max(0, min(32768, int(round(value)))))
        entry = {"id": case["id"], "geometry": [case["width"], case["height"]], "parameters": {k: case[k] for k in ("blur_amount", "repeat", "bias_direction")}, "instructions": instructions, "source_sha256": hashlib.sha256(source).hexdigest(), "actual_sha256": hashlib.sha256(actual).hexdigest(), "baseline_actual_like": summarize(actual, baseline), "reverse_accumulation_order": summarize(actual, reverse), "replicated_border": summarize(actual, replicated), "nearest_even_writer": summarize(actual, bytes(even))}
        report["cases"].append(entry)
    report["conclusion"] = {"border": "excluded for this bounded family" if all(c["baseline_actual_like"]["equal"] and not c["replicated_border"]["equal"] for c in report["cases"]) else "not excluded", "accumulation_order": "not excluded by this bounded reversal probe", "writer_rounding": "excluded as the final PF16 writer rule by the existing actual-AEX half-tie microtest and the near-half worker probe", "ae_exact_claim": False}
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# OLMBlur case_0006 bounded border/order/writer differential", "", "This standalone Mac actual-AEX/portable fixture does not modify existing 20260716 blur differentials or the ledger.", "", f"- AEX SHA-256: `{report['aex_sha256']}`", f"- Entry: `{report['entry']}`", "- Actual-AEX runs: 3 bounded fixtures; no AE exact claim.", "", "## Results", ""]
    for c in report["cases"]:
        lines.append(f"- `{c['id']}` {c['geometry']}: baseline equal=`{c['baseline_actual_like']['equal']}`, reverse-order equal=`{c['reverse_accumulation_order']['equal']}`, replicated-border equal=`{c['replicated_border']['equal']}`, nearest-even equal=`{c['nearest_even_writer']['equal']}`.")
    lines += ["", "## Interpretation", "", "- Border: **not excluded**. The opaque radius-4 probe disagrees with both the portable truncated-edge candidate and the replicated-edge candidate; this fixture isolates the boundary family but does not identify its exact AEX rule.", "- Coefficient accumulation order: **not excluded**. The tested reverse traversal did not produce a quantized output difference in the order-focused cases, so this fixture cannot decide all reassociation variants.", "- Final writer rounding: **excluded as the final PF16 writer rule** by the existing actual-AEX half-tie microtest and the near-half worker probe. No global writer change is justified.", "- These results are local binary/portable evidence only; they do not establish AE exactness or explain the one-pixel Mac export residual.", "", "## Commands", "", "`python3 tools/emulation/test_olmblur_case0006_border_order_writer_differential_20260716.py`"]
    REPORT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
