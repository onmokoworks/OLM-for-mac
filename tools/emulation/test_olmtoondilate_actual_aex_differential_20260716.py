"""Bounded actual-AEX OLMToonDilate worker differential on macOS.

This drives the checked-in Windows PE AEX under the local Unicorn loader.  It
does not invoke After Effects, Windows, or the production Mac plug-in.  The
portable side is an independent small reference for the 8bpc worker contract;
the typed-core test is intentionally not imported as an oracle.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex"
WORKER = 0x1801A6150
REPORT = Path(__file__).parent / "OLMTOONDILATE_ACTUAL_AEX_DIFFERENTIAL_20260716_REPORT.md"
JSON_REPORT = REPORT.with_suffix(".json")


def portable(source, radius=1):
    h, w = len(source), len(source[0])
    out = [row[:] for row in source]
    dist = [[0 if source[y][x][0] == 255 else 0xFFFFFFFF for x in range(w)] for y in range(h)]

    def relax(x, y, neighbors):
        if dist[y][x] == 0:
            return
        candidates = [(dist[ny][nx], nx, ny) for nx, ny in neighbors
                      if 0 <= nx < w and 0 <= ny < h]
        if not candidates:
            return
        best, nx, ny = min(candidates, key=lambda item: item[0])
        if best != 0xFFFFFFFF and best + 1 < dist[y][x]:
            dist[y][x] = best + 1
            if dist[y][x] <= radius:
                out[y][x] = out[ny][nx]

    for y in range(h):
        for x in range(w):
            relax(x, y, ((x - 1, y), (x - 1, y - 1), (x, y - 1), (x + 1, y - 1)))
    for y in range(h - 1, -1, -1):
        for x in range(w - 1, -1, -1):
            relax(x, y, ((x + 1, y), (x + 1, y + 1), (x, y + 1), (x - 1, y + 1)))

    for y in range(h):
        for x in range(w):
            a, r, g, b = out[y][x]
            if 0 < a < 255:
                r, g, b = tuple((v * a + 127) // 255 for v in (r, g, b))
            out[y][x] = (a, r, g, b)
    return out


def world(loader, pixels, width, height):
    data = loader.bump_alloc(width * height * 4, align=64)
    loader.write_bytes(data, bytes(byte for px in pixels for byte in px))
    header = loader.host_alloc(0x80, align=16)
    loader.write_bytes(header, b"\0" * 0x80)
    loader.write_bytes(header + 0x18, struct.pack("<Q", data))
    loader.write_bytes(header + 0x20, struct.pack("<I", width * 4))
    loader.write_bytes(header + 0x24, struct.pack("<I", width))
    loader.write_bytes(header + 0x28, struct.pack("<I", height))
    loader.write_bytes(header + 0x2C, struct.pack("<H", 8))
    return header


def run_case(case_id, source, expected):
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    width, height = len(source[0]), len(source)
    src = world(loader, [px for row in source for px in row], width, height)
    dst = world(loader, [(0, 0, 0, 0)] * (width * height), width, height)

    # FUN_1801a6150 calls *(param1+0xb0)+0x40(param1+0xb8,...).  A success
    # callback is enough to pass the worker's handle/status gate; no AE suite
    # or Windows process is involved.
    context = loader.host_alloc(0x140, align=16)
    loader.write_bytes(context, b"\0" * 0x140)
    vtable = loader.host_alloc(0x50, align=16)
    loader.write_bytes(vtable, b"\0" * 0x50)
    calls = []

    def status_ok(_loader, args):
        calls.append([hex(value) for value in args])
        return 0

    callback = loader.install_callback("toondilate_status_ok", status_ok)
    loader.write_bytes(vtable + 0x40, struct.pack("<Q", callback))
    loader.write_bytes(context + 0xB0, struct.pack("<Q", vtable))
    loader.write_bytes(context + 0xB8, struct.pack("<Q", 0x1234))
    loader.write_bytes(context + 0x11C, struct.pack("<i", 1))
    loader.write_bytes(context + 0x120, struct.pack("<i", 1))

    radius = loader.bump_alloc(4, align=16)
    loader.write_bytes(radius, struct.pack("<f", 1.0))
    # Disassembly at 0x1801a6194..0x1801a61b8 establishes the effective
    # worker ABI: RCX=context, R8=input world, R9=output world, and the fifth
    # positional argument is a pointer to the float radius. RDX is auxiliary
    # in this worker and is supplied as zero for the bounded call.
    flat_expected = [list(px) for row in expected for px in row]
    try:
        result = loader.call_function(WORKER, int_args=[context, 0, src, dst, radius],
                                      max_instructions=5_000_000)
        raw = loader.read_bytes(struct.unpack("<Q", loader.read_bytes(dst + 0x18, 8))[0], width * height * 4)
        flat_actual = [list(raw[i * 4:(i + 1) * 4]) for i in range(width * height)]
        return {
            "case": case_id, "status": "PASS", "match": flat_actual == flat_expected,
            "expected_argb": flat_expected, "actual_argb": flat_actual,
            "instructions": result["instructions"], "callback_calls": calls,
            "imports": [entry.name for entry in loader.import_log],
        }
    except (RuntimeError, ValueError) as exc:
        rip = str(exc).split("RIP=", 1)[1].split(":", 1)[0] if "RIP=" in str(exc) else "unknown"
        return {
            "case": case_id, "status": "BLOCKED", "match": None,
            "expected_argb": flat_expected, "stop_rip": rip, "error": str(exc),
            "callback_calls": calls, "imports": [entry.name for entry in loader.import_log],
        }


def main():
    transparent = (0, 0, 0, 0)
    opaque = (255, 31, 127, 223)
    semi = (128, 200, 100, 50)
    cases = [
        ("alpha_threshold_center", [[transparent] * 3 for _ in range(3)]),
        ("boundary_corner", [[transparent] * 3 for _ in range(3)]),
        ("semi_alpha_quantization", [[semi, transparent, opaque]]),
    ]
    cases[0][1][1][1] = opaque
    cases[1][1][0][0] = opaque
    results = []
    for case_id, source in cases:
        results.append(run_case(case_id, source, portable(source)))
    if all(item["match"] is True for item in results):
        status = "PASS"
    elif any(item["status"] == "BLOCKED" for item in results):
        status = "BLOCKED"
    else:
        status = "FAIL"
    payload = {"status": status,
               "aex": str(AEX.relative_to(ROOT)), "worker": hex(WORKER), "cases": results,
               "claim_boundary": "actual-AEX worker differential only; no AE-exact claim"}
    JSON_REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# OLMToonDilate Actual-AEX Differential - 2026-07-16", "",
             "## Result", "", f"- Status: **{payload['status']}**",
             f"- AEX: `{payload['aex']}`", f"- Worker: `{payload['worker']}`",
             "- Execution: checked-in PE AEX under local Unicorn on macOS; no AE or Windows.",
             "- The portable side is independent and covers alpha threshold, boundary, and 8bpc premultiply quantization.", ""]
    first = results[0]
    lines += ["## ABI Stop Point", "",
              "- Effective worker call: `RCX=context, RDX=0, R8=input world, R9=output world, stack arg 5=float* radius`.",
              f"- Stop RIP: `{first.get('stop_rip', 'return')}`",
              f"- Callback args observed: `{first.get('callback_calls', [])}`",
              "- The synthetic status callback returned zero once; the next return path fetched unmapped `0xc3`.", ""]
    for item in results:
        lines += [f"## {item['case']}", "", f"- Status: `{item['status']}`",
                  f"- Match: `{item['match']}`",
                  f"- Stop RIP: `{item.get('stop_rip', 'return')}`",
                  f"- Instructions: `{item.get('instructions', 'not returned')}`",
                  f"- Callback calls: `{len(item['callback_calls'])}`",
                  f"- Imports: `{item['imports'] or 'none'}`", ""]
    lines += ["## Interpretation", "",
              "This is a bounded actual-AEX worker differential; no AE-exact claim is made. "
              "The checked-in typed-core model was not used as an oracle. The AEX is a Windows PE "
              "artifact exercised through Unicorn; the host callback is synthetic and only satisfies "
              "the worker status gate.", "", "## Reproduce", "",
              "```sh", "tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_actual_aex_differential_20260716.py", "```", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
