#!/usr/bin/env python3
"""Validate and retain the case_0010 actual-AEX Rotation plane dump."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = Path("/tmp/olmradialblur_case0010_full_planes_20260805")
DESTINATION = ROOT / "refs/fixtures/olmradialblur_case0010_rotation_full_planes_20260805"
EXPECTED_MANIFEST_SHA256 = "a52ff1a6f3a554ee4613120aa275e6a4ac40b875a0d2194299ec3d03ffef2b6b"
EXPECTED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
EXPECTED_INPUT_SHA256 = "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4"
EXPECTED_STAGES = ["pre_scatter", "post_scatter_pre_gather", "post_normalize"]
EXPECTED_PLANES = {
    "pre_scatter": {
        "accum_rgba", "max_alpha", "normalized_or_polar_rgba",
        "slot_0x10", "slot_0x12", "slot_0x14",
    },
    "post_scatter_pre_gather": {
        "accum_rgba", "eligibility_mask", "max_alpha", "normalized_or_polar_rgba",
        "slot_0x10", "slot_0x12", "slot_0x14",
    },
    "post_normalize": {
        "accum_rgba", "max_alpha", "normalized_or_polar_rgba",
        "slot_0x10", "slot_0x12", "slot_0x14",
    },
}


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate(source: Path) -> tuple[dict, list[Path]]:
    manifest_path = source / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    if sha256(manifest_bytes) != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("source manifest identity mismatch")
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema") != "olmradialblur.rotation-full-plane-dump/1":
        raise RuntimeError("unexpected fixture schema")
    if manifest.get("aex_sha256") != EXPECTED_AEX_SHA256:
        raise RuntimeError("AEX identity mismatch")
    if manifest.get("input_sha256") != EXPECTED_INPUT_SHA256:
        raise RuntimeError("input identity mismatch")
    stages = manifest.get("stages", [])
    if [stage.get("stage") for stage in stages] != EXPECTED_STAGES:
        raise RuntimeError("stage order mismatch")

    files = [manifest_path]
    for stage in stages:
        name = stage["stage"]
        if stage.get("geometry") != {
            "angular_count": 1800, "cells": 1987200, "radius_count": 1104,
        }:
            raise RuntimeError(f"geometry mismatch at {name}")
        planes = stage.get("planes", {})
        if set(planes) != EXPECTED_PLANES[name]:
            raise RuntimeError(f"plane set mismatch at {name}")
        for plane_name, metadata in planes.items():
            path = source / metadata["path"]
            encoded = path.read_bytes()
            if len(encoded) != metadata["zlib_bytes"] or sha256(encoded) != metadata["zlib_sha256"]:
                raise RuntimeError(f"compressed identity mismatch: {name}/{plane_name}")
            raw = zlib.decompress(encoded)
            if len(raw) != metadata["raw_bytes"] or sha256(raw) != metadata["raw_sha256"]:
                raise RuntimeError(f"raw identity mismatch: {name}/{plane_name}")
            files.append(path)
    return manifest, files


def main() -> int:
    source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_SOURCE
    _, files = validate(source)
    if DESTINATION.exists():
        raise RuntimeError(f"destination already exists: {DESTINATION}")
    DESTINATION.mkdir(parents=True)
    for path in files:
        shutil.copyfile(path, DESTINATION / path.name)
    # Verify the retained copy independently of the source directory.
    validate(DESTINATION)
    print(json.dumps({
        "status": "pass",
        "destination": str(DESTINATION),
        "file_count": len(files),
        "compressed_payload_bytes": sum(path.stat().st_size for path in DESTINATION.glob("*.zlib")),
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
