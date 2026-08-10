#!/usr/bin/env python3
"""Prepare and validate the bounded Windows AE Noise-Type-3 witness."""

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
# Noise Type 3 disables Thickness in the AEX UI. Keep the hidden value pinned
# for reproducibility, but do not present it as a public conformance axis.
FIXED_THICKNESS = 3
LAYERS = ("pattern", "inverse")
REPEATS = (1, 2)
WIDTH, HEIGHT = 9, 7
REQUEST_SCHEMA = "olmradialblur-type3-windows-witness-request/2"
RETURN_SCHEMA = "olmradialblur-type3-windows-witness-return/2"


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
            elif kind == "source":
                # Deliberately distinct from both Noise Layer fixtures so a
                # layer response cannot be confused with a changed primary.
                rgba = ((x * 19 + y * 53 + 17) & 255,
                        (x * 61 + y * 5 + 43) & 255,
                        (x * 3 + y * 37 + 101) & 255,
                        224 if (2 * x + y) % 5 else 64)
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
                for layer in LAYERS:
                    case_id = f"pf{depth}_{mode}_nv{nv}_{layer}"
                    result.append({
                        "case_id": case_id, "project_bpc": depth,
                        "blur_type": 1 if mode == "zoom" else 2,
                        "noise_variation": nv, "noise_type": 3,
                        "primary_source": "input/source.png",
                        "noise_layer": f"layers/{layer}.png",
                        "width": WIDTH, "height": HEIGHT, "renderer": "Software",
                        "parameters": {
                            "Center": [4.5, 3.5] if depth == 8 else [4, 3],
                            "Outer Strength": 4, "Outer Offset Mode": 1,
                            "Outer Offset": 0, "Inner Strength": 0,
                            "Repeat Border": True, "Ratio": 1, "Angle": 0,
                            "Quality": 5, "Brightness Gain": 1,
                            "Size Variation": 0, "Noise Variation": nv,
                            "Noise Type": 3, "Thickness": FIXED_THICKNESS,
                        },
                        "repeats": list(REPEATS),
                        "required_exports": [f"exports/{case_id}.r{{repeat}}.exr"],
                    })
    return result


def prepare(directory: Path) -> None:
    (directory / "input").mkdir(parents=True, exist_ok=True)
    (directory / "layers").mkdir(parents=True, exist_ok=True)
    source_raw = png_rgba("source")
    (directory / "input" / "source.png").write_bytes(source_raw)
    layer_meta = {}
    for name in LAYERS:
        raw = png_rgba(name)
        path = directory / "layers" / f"{name}.png"
        path.write_bytes(raw)
        layer_meta[name] = {"path": f"layers/{name}.png", "sha256": sha256(raw)}
    manifest = {
        "schema": REQUEST_SCHEMA,
        "aex_sha256": "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb",
        "fresh_process_required": True,
        "ae_renderer": "Software",
        "primary_source": {"path": "input/source.png", "sha256": sha256(source_raw)},
        "layers": layer_meta,
        "fixed_hidden_parameters": {
            "Thickness": FIXED_THICKNESS,
            "reason": "Noise Type 3 disables Thickness in the AEX UI",
        },
        "cases": cases(),
        "return_contract": {
            "schema": RETURN_SCHEMA,
            "one_fresh_ae_process_per_repeat": True,
            "required_fields": ["case_id", "repeat", "ae_pid", "ae_version", "ae_build",
                                "project_bpc", "renderer", "aex_sha256", "source_sha256",
                                "noise_layer_sha256", "output_path", "output_sha256"],
            "optional_internal_fields": ["source_factor_sha256", "source_scalar_sha256",
                                         "source_span_sha256"],
        },
    }
    (directory / "request.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (directory / "README.md").write_text(
        "# OLM RadialBlur Noise Type 3 Windows witness\n\n"
        "Use the pinned 2025 OLMRadialBlur AEX in a fresh Windows After Effects "
        "Software-render process for every repeat. Create a 9×7 comp from the fixed "
        "`input/source.png`, apply the parameters in `request.json`, bind the named PNG "
        "as Noise Layer, and export the complete frame to the requested EXR path. Do "
        "not reuse previews. Record one row per export in `return.json`; include internal "
        "plane hashes when a debugger/collector is available. Then run:\n\n"
        "```powershell\npy -3 prepare_olmradialblur_type3_windows_witness_20260811.py "
        "--validate return.json --request request.json\n"
        "# Or validate the strict PF32/NV25 eight-render pilot:\n"
        "py -3 prepare_olmradialblur_type3_windows_witness_20260811.py "
        "--validate return.json --request request.json --pilot\n```\n"
    )
    print(json.dumps({"directory": str(directory), "cases": len(manifest["cases"]),
                      "renders": len(manifest["cases"]) * len(REPEATS)}))


def pilot_case_ids(request: dict) -> set[str]:
    return {
        case["case_id"] for case in request["cases"]
        if case["project_bpc"] == 32 and case["noise_variation"] == 25
    }


def validate(request_path: Path, return_path: Path, *, pilot: bool = False) -> None:
    request = json.loads(request_path.read_text())
    returned = json.loads(return_path.read_text())
    if request.get("schema") != REQUEST_SCHEMA or returned.get("schema") != RETURN_SCHEMA:
        raise SystemExit("schema mismatch: this validator requires Type3 witness schema 2")
    assets = [request["primary_source"], *request["layers"].values()]
    for asset in assets:
        path = request_path.parent / asset["path"]
        if not path.is_file() or sha256(path.read_bytes()) != asset["sha256"]:
            raise SystemExit(f"missing/hash-mismatched request asset: {path}")
    selected = pilot_case_ids(request) if pilot else {case["case_id"] for case in request["cases"]}
    indexed = {case["case_id"]: case for case in request["cases"]}
    expected = {(case_id, repeat) for case_id in selected for repeat in indexed[case_id]["repeats"]}
    rows = returned.get("renders", [])
    observed = {(row.get("case_id"), row.get("repeat")) for row in rows}
    if observed != expected or len(rows) != len(expected):
        raise SystemExit(f"incomplete/duplicate return: expected {len(expected)}, got {len(rows)}")
    by_case: dict[str, list[dict]] = {}
    for row in rows:
        case = indexed.get(row.get("case_id"))
        layer_name = Path(case["noise_layer"]).stem if case else None
        expected_layer_hash = request["layers"].get(layer_name, {}).get("sha256")
        if (row.get("renderer") != "Software" or row.get("aex_sha256") != request["aex_sha256"]
                or row.get("project_bpc") != (case or {}).get("project_bpc")
                or row.get("source_sha256") != request["primary_source"]["sha256"]
                or row.get("noise_layer_sha256") != expected_layer_hash):
            raise SystemExit(f"identity mismatch: {row.get('case_id')} repeat {row.get('repeat')}")
        if not isinstance(row.get("ae_version"), str) or not row["ae_version"].strip():
            raise SystemExit("missing AE version")
        if not isinstance(row.get("ae_build"), str) or not row["ae_build"].strip():
            raise SystemExit("missing AE build")
        output = return_path.parent / row["output_path"]
        if not output.is_file() or sha256(output.read_bytes()) != row.get("output_sha256"):
            raise SystemExit(f"missing/hash-mismatched export: {output}")
        if not isinstance(row.get("ae_pid"), int) or row["ae_pid"] <= 0:
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
    summary = {"status": "deterministic_windows_witness", "scope": "pilot" if pilot else "full",
               "cases": len(by_case), "renders": len(rows), "unstable": unstable}
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate", type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--pilot", action="store_true",
                        help="strictly validate the 8-render PF32/NV25 pilot subset")
    args = parser.parse_args()
    if args.validate:
        if not args.request:
            parser.error("--validate requires --request")
        validate(args.request, args.validate, pilot=args.pilot)
    elif args.output:
        prepare(args.output)
    else:
        parser.error("use --output or --validate")


if __name__ == "__main__":
    main()
