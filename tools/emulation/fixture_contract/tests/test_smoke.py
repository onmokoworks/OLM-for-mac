"""Self-contained smoke test for the fixture contract."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fixture_contract import FixtureContractError, verify_fixture


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def descriptor(blob: str, data: bytes, offset: int = 0) -> dict[str, object]:
    return {"blob": blob, "offset": offset, "size": len(data), "sha256": digest(data)}


def make_manifest(root: Path, *, overlap: bool = False, bad_hash: bool = False) -> None:
    pixels = bytes(range(32))
    params = b"raw-params"
    blob = pixels + params + b"padding" * 4
    (root / "payload.bin").write_bytes(blob)
    world_descriptor = descriptor("payload.bin", pixels)
    if overlap:
        # This range has the correct digest but intersects the param range.
        world_descriptor = descriptor("payload.bin", blob[16:48], offset=16)
    if bad_hash:
        world_descriptor["sha256"] = "0" * 64
    manifest = {
        "schema": "olm.aex.cpu-fixture/1",
        "case_id": "smoke-0001",
        "scope": "effect",
        "provenance": {
            "oracle": "unicorn-aex",
            "binary_sha256": "1" * 64,
            "function": "0x180001000",
            "parameter_block_origin": "harness-constructed",
        },
        "world": {"format": "ARGB", "width": 2, "height": 2, "rowbytes": 16, "bpc": 8, "descriptor": world_descriptor},
        "raw_param_block": {"format": "raw", "descriptor": descriptor("payload.bin", params, offset=len(pixels))},
        "intermediates": [
            {
                "name": "field",
                "format": "SCALAR",
                "width": 2,
                "height": 2,
                "rowbytes": 8,
                "bpc": 32,
                "descriptor": descriptor("field.bin", b"\x00" * 16),
            }
        ],
        "output": {"format": "ARGB", "width": 2, "height": 2, "rowbytes": 16, "bpc": 8, "descriptor": descriptor("output.bin", pixels)},
    }
    (root / "output.bin").write_bytes(pixels)
    (root / "field.bin").write_bytes(b"\x00" * 16)
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")


def rejects(root: Path, expected: str) -> None:
    try:
        verify_fixture(root)
    except FixtureContractError as exc:
        assert expected in str(exc), str(exc)
    else:
        raise AssertionError(f"expected rejection containing {expected!r}")


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        make_manifest(root)
        fixture = verify_fixture(root)
        assert fixture.case_id == "smoke-0001"
        assert fixture.scope == "effect"
        assert fixture.world["format"] == "ARGB"
        assert fixture.intermediates[0]["format"] == "SCALAR"
        assert fixture.provenance["oracle"] == "unicorn-aex"

        missing = root / "missing"
        missing.mkdir()
        make_manifest(missing)
        (missing / "output.bin").unlink()
        rejects(missing, "missing blob")

        bad_hash = root / "bad-hash"
        bad_hash.mkdir()
        make_manifest(bad_hash, bad_hash=True)
        rejects(bad_hash, "hash mismatch")

        overlap = root / "overlap"
        overlap.mkdir()
        make_manifest(overlap, overlap=True)
        rejects(overlap, "overlapping descriptors")

        too_short = root / "too-short"
        too_short.mkdir()
        make_manifest(too_short)
        (too_short / "output.bin").write_bytes(b"short")
        rejects(too_short, "no range")

        binary_without_relocation = root / "binary-without-relocation"
        binary_without_relocation.mkdir()
        make_manifest(binary_without_relocation)
        manifest_path = binary_without_relocation / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["provenance"]["parameter_block_origin"] = "binary-built"
        manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        rejects(binary_without_relocation, "must declare relocations")

    print("fixture contract smoke: PASS (1 valid, 5 invalid cases)")


if __name__ == "__main__":
    main()
