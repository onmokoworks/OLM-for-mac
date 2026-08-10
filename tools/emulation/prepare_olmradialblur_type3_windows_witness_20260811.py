#!/usr/bin/env python3
"""Prepare and validate the bounded Windows AE Noise-Type-3 witness.

This does not pretend that AEXCompat's zero-filled PF handles are Windows AE
evidence.  It creates the complete request matrix and validates a returned
manifest produced by a fresh Windows AE Software render run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path

DEPTHS = (8, 16, 32)
MODES = ("zoom", "rotation")
NOISE_VARIATIONS = (25, 100)
THICKNESSES = (3, 10)
LAYERS = ("pattern", "inverse")
REPEATS = (1, 2)
WIDTH, HEIGHT = 9, 7


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def png_rgba(kind: str) -> bytes:
    rows = bytearray()
    for y in range(HEIGHT):
        rows.append(0)
        for x in range(WIDTH):
            a = 255 if (x + y) % 4 else 96
            rgba = ((x * 31 + y * 7) & 255, (x * 11 + y * 29) & 255,
                    (x * 47 + y * 13) & 255, a)
            if kind == "inverse":
                rgba = (255 - rgba[0], 255 - rgba[1], 255 - rgba[2], rgba[3])
            rows.extend(rgba)

    def chunk(name: bytes, payload: bytes) -> bytes:
        body = name + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b""))


def cases() -> list[dict]:
    result = []
    for depth in DEPTHS:
        for mode in MODES:
            for nv in NOISE_VARIATIONS:
                for thickness in THICKNESSES:
                    for layer in LAYERS:
                        case_id = f"pf{depth}_{mode}_nv{nv}_t{thickness}_{layer}"
                        result.append({
                            "case_id": case_id, "project_bpc": depth,
                            "blur_type": 1 if mode == "zoom" else 2,
                            "noise_variation": nv, "noise_type": 3,
                            "thickness": thickness, "noise_layer": f"layers/{layer}.png",
                            "width": WIDTH, "height": HEIGHT, "renderer": "Software",
                            "parameters": {
                                "Center": [4.5, 3.5] if depth == 8 else [4, 3],
                                "Outer Strength": 4, "Outer Offset Mode": 1,
                                "Outer Offset": 0, "Inner Strength": 0,
                                "Repeat Border": True, "Ratio": 1, "Angle": 0,
                                "Quality": 5, "Brightness Gain": 1,
                                "Size Variation": 0, "Noise Variation": nv,
                                "Noise Type": 3, "Thickness": thickness,
                            },
                            "repeats": list(REPEATS),
                            "required_exports": [f"exports/{case_id}.r{{repeat}}.exr"],
                        })
    return result


def prepare(directory: Path) -> None:
    (directory / "layers").mkdir(parents=True, exist_ok=True)
    layer_meta = {}
    for name in LAYERS:
        raw = png_rgba(name)
        path = directory / "layers" / f"{name}.png"
        path.write_bytes(raw)
        layer_meta[name] = {"path": f"layers/{name}.png", "sha256": sha256(raw)}
    manifest = {
        "schema": "olmradialblur-type3-windows-witness-request/1",
        "aex_sha256": "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb",
        "fresh_process_required": True,
        "ae_renderer": "Software",
        "layers": layer_meta,
        "cases": cases(),
        "return_contract": {
            "schema": "olmradialblur-type3-windows-witness-return/1",
            "one_fresh_ae_process_per_repeat": True,
            "required_fields": ["case_id", "repeat", "ae_pid", "project_bpc",
                                "renderer", "aex_sha256", "output_path", "output_sha256"],
            "optional_internal_fields": ["source_factor_sha256", "source_scalar_sha256",
                                         "source_span_sha256"],
        },
    }
    (directory / "request.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (directory / "README.md").write_text(
        "# OLM RadialBlur Noise Type 3 Windows witness\n\n"
        "Use the pinned 2025 OLMRadialBlur AEX in a fresh Windows After Effects "
        "Software-render process for every repeat. Create a 9×7 comp, apply the "
        "parameters in `request.json`, bind the named PNG as Noise Layer, and export "
        "the complete frame to the requested EXR path. Do not reuse previews. Record "
        "one row per export in `return.json`; include internal plane hashes when a "
        "debugger/collector is available. Then run:\n\n"
        "```powershell\npy -3 prepare_olmradialblur_type3_windows_witness_20260811.py "
        "--validate return.json --request request.json\n```\n"
    )
    print(json.dumps({"directory": str(directory), "cases": len(manifest["cases"]),
                      "renders": len(manifest["cases"]) * len(REPEATS)}))


def validate(request_path: Path, return_path: Path) -> None:
    request = json.loads(request_path.read_text())
    returned = json.loads(return_path.read_text())
    expected = {(c["case_id"], repeat) for c in request["cases"] for repeat in c["repeats"]}
    rows = returned.get("renders", [])
    observed = {(r.get("case_id"), r.get("repeat")) for r in rows}
    if observed != expected or len(rows) != len(expected):
        raise SystemExit(f"incomplete/duplicate return: expected {len(expected)}, got {len(rows)}")
    by_case: dict[str, list[dict]] = {}
    for row in rows:
        if row.get("renderer") != "Software" or row.get("aex_sha256") != request["aex_sha256"]:
            raise SystemExit(f"identity mismatch: {row.get('case_id')} repeat {row.get('repeat')}")
        output = return_path.parent / row["output_path"]
        if not output.is_file() or sha256(output.read_bytes()) != row.get("output_sha256"):
            raise SystemExit(f"missing/hash-mismatched export: {output}")
        if row.get("ae_pid") is None:
            raise SystemExit("missing process binding")
        by_case.setdefault(row["case_id"], []).append(row)
    unstable = [key for key, group in by_case.items()
                if len({row["output_sha256"] for row in group}) != 1]
    reused = [key for key, group in by_case.items()
              if len({row["ae_pid"] for row in group}) != len(REPEATS)]
    if reused:
        raise SystemExit("repeat did not use fresh AE process: " + ", ".join(reused))
    if unstable:
        raise SystemExit("fresh-process nondeterminism: " + ", ".join(unstable))
    summary = {"status": "deterministic_windows_witness", "cases": len(by_case),
               "renders": len(rows), "unstable": unstable}
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate", type=Path)
    parser.add_argument("--request", type=Path)
    args = parser.parse_args()
    if args.validate:
        if not args.request:
            parser.error("--validate requires --request")
        validate(args.request, args.validate)
    elif args.output:
        prepare(args.output)
    else:
        parser.error("use --output or --validate")


if __name__ == "__main__":
    main()
