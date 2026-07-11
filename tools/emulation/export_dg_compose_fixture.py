#!/usr/bin/env python3
"""Export a three-point case_0023 fixture from the real DG compose callback."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from fixture_contract import verify_fixture  # noqa: E402
from test_dg_compose import (  # noqa: E402
    FIELD_X_BY_PIXEL,
    FUN_181170480,
    REFCON_SIZE,
    WINDOWS_FINAL_RGBA16,
    build_case0023_refcon,
    build_world,
    call_compose,
    make_loader,
)
from export_dg_fieldgen_fixture import sha256_file  # noqa: E402

AEX = ROOT / "plugins_2025" / "DistanceGradation.aex"
DEFAULT_OUTPUT = HERE / "fixtures" / "distancegradation_compose_case0023_triplet"
WIDTH = 420
HEIGHT = 400


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def descriptor(name: str, data: bytes) -> dict[str, object]:
    return {"blob": name, "offset": 0, "size": len(data), "sha256": digest(data)}


def world_bytes(loader, world: int) -> tuple[bytes, int]:
    data = struct.unpack("<Q", loader.read_bytes(world + 0x18, 8))[0]
    rowbytes = struct.unpack("<I", loader.read_bytes(world + 0x20, 4))[0]
    return loader.read_bytes(data, rowbytes * HEIGHT), rowbytes


def export_fixture(output: Path, *, replace: bool) -> Path:
    if output.exists():
        if not replace:
            raise FileExistsError(f"fixture exists: {output}; pass --replace")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    loader = make_loader()
    field_pixels = {
        xy: (0, int(round(field_x * 32768.0)), 0, 0)
        for xy, field_x in FIELD_X_BY_PIXEL.items()
    }
    field_world = build_world(loader, WIDTH, HEIGHT, field_pixels)
    source_world = build_world(loader, WIDTH, HEIGHT, {})
    refcon = build_case0023_refcon(loader, field_world, source_world)
    points = sorted(WINDOWS_FINAL_RGBA16)
    output_words = [call_compose(loader, refcon, x, y) for x, y in points]

    source_bytes, source_rowbytes = world_bytes(loader, source_world)
    field_bytes, field_rowbytes = world_bytes(loader, field_world)
    runtime_refcon_bytes = loader.read_bytes(refcon, REFCON_SIZE)
    # Persist a relocatable block, not emulator heap addresses. The scalar
    # layout is reconstructed from the AEX callback's binary reads; replay
    # binds the two world pointers at runtime.
    refcon = bytearray(runtime_refcon_bytes)
    refcon[0x00:0x10] = b"\x00" * 0x10
    refcon_bytes = bytes(refcon)
    output_bytes = b"".join(struct.pack("<4H", *words) for words in output_words)
    blobs = {
        "source_agrb16.bin": source_bytes,
        "field_agrb16.bin": field_bytes,
        "refcon.bin": refcon_bytes,
        "output_triplet_agrb16.bin": output_bytes,
    }
    for name, data in blobs.items():
        (output / name).write_bytes(data)

    manifest = {
        "schema": "olm.aex.cpu-fixture/1",
        "case_id": "distancegradation.case0023.compose.triplet",
        "scope": "function",
        "provenance": {
            "oracle": "unicorn-aex",
            "binary_sha256": sha256_file(AEX),
            "binary_path": "plugins_2025/DistanceGradation.aex",
            "function": hex(FUN_181170480),
            "parameter_block_origin": "binary-built",
            "parameter_block_basis": "AEX callback layout plus case manifest; not runtime-captured",
        },
        "world": {
            "name": "source_world",
            "format": "INTERLEAVED",
            "channels": ["A", "G", "R", "B"],
            "sample_type": "uint16",
            "byte_order": "little",
            "width": WIDTH, "height": HEIGHT, "rowbytes": source_rowbytes, "bpc": 16,
            "descriptor": descriptor("source_agrb16.bin", source_bytes),
        },
        "raw_param_block": {
            "format": "raw",
            "descriptor": descriptor("refcon.bin", refcon_bytes),
            "relocations": [
                {"offset": 0, "width": 8, "target": "source_world"},
                {"offset": 8, "width": 8, "target": "field_world"},
            ],
            "scalar_range": {"offset": 144, "size": 68},
        },
        "intermediates": [{
            "name": "field_world",
            "format": "INTERLEAVED",
            "channels": ["A", "G", "R", "B"],
            "sample_type": "uint16",
            "byte_order": "little",
            "width": WIDTH, "height": HEIGHT, "rowbytes": field_rowbytes, "bpc": 16,
            "descriptor": descriptor("field_agrb16.bin", field_bytes),
        }],
        "output": {
            "name": "compose_triplet",
            "format": "INTERLEAVED",
            "channels": ["A", "G", "R", "B"],
            "sample_type": "uint16",
            "byte_order": "little",
            "width": len(points), "height": 1, "rowbytes": len(points) * 8, "bpc": 16,
            "descriptor": descriptor("output_triplet_agrb16.bin", output_bytes),
        },
        "points": [list(point) for point in points],
        "field_values": [FIELD_X_BY_PIXEL[point] for point in points],
        "claim": "Actual AEX compose output with relocatable binary-built parameters; field values are tied to the case_0023 AEX fieldgen fixture.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    verify_fixture(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    fixture = export_fixture(args.output.resolve(), replace=args.replace)
    print(f"[OK] exported and verified DG AEX compose fixture: {fixture}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
