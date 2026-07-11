"""Validation for the case-bound OLM AEX CPU fixture contract.

The manifest is JSON and all payloads are slices of manifest-relative binary
blobs.  Verification does not import or depend on the After Effects SDK.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA = "olm.aex.cpu-fixture/1"
_REQUIRED_DESCRIPTOR_KEYS = frozenset(("blob", "offset", "size", "sha256"))
_ORACLES = frozenset(("windows-aex-cdb", "unicorn-aex", "portable-core"))
_PARAM_ORIGINS = frozenset(("runtime-captured", "binary-built", "harness-constructed"))


class FixtureContractError(ValueError):
    """Raised when a fixture does not satisfy the contract."""


@dataclass(frozen=True)
class BinaryDescriptor:
    blob: str
    offset: int
    size: int
    sha256: str


@dataclass(frozen=True)
class Fixture:
    case_id: str
    scope: str
    manifest_path: Path
    provenance: Mapping[str, Any]
    world: Mapping[str, Any]
    raw_param_block: BinaryDescriptor
    intermediates: tuple[Mapping[str, Any], ...]
    output: Mapping[str, Any]


def verify_manifest(manifest_path: str | Path) -> Fixture:
    """Load and verify a JSON manifest and its sibling binary blobs."""
    path = Path(manifest_path).resolve()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FixtureContractError(f"missing manifest: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureContractError(f"invalid manifest {path}: {exc}") from exc
    return _verify(raw, path.parent, path)


def verify_fixture(root: str | Path, manifest_name: str = "manifest.json") -> Fixture:
    """Verify ``manifest_name`` in a fixture directory."""
    return verify_manifest(Path(root) / manifest_name)


def _verify(raw: Any, root: Path, manifest_path: Path) -> Fixture:
    if not isinstance(raw, dict):
        _fail("manifest must be a JSON object")
    if raw.get("schema") != _SCHEMA:
        _fail(f"schema must be {_SCHEMA!r}")
    case_id = raw.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        _fail("case_id must be a non-empty string")

    scope = raw.get("scope")
    if scope not in ("effect", "function"):
        _fail("scope must be 'effect' or 'function'")
    provenance = _provenance(raw.get("provenance"))
    world = _image_record(raw.get("world"), "world", require_argb=scope == "effect")
    raw_param_block = _raw_param_block(raw.get("raw_param_block"), provenance)

    intermediate_raw = raw.get("intermediates")
    if not isinstance(intermediate_raw, list):
        _fail("intermediates must be an array")
    intermediates = tuple(_image_record(item, "intermediate") for item in intermediate_raw)
    output = _image_record(raw.get("output"), "output", require_argb=scope == "effect")

    descriptors = [world["descriptor"], raw_param_block, *(item["descriptor"] for item in intermediates), output["descriptor"]]
    _verify_payloads(descriptors, root)
    _reject_overlaps(descriptors)
    return Fixture(case_id, scope, manifest_path, provenance, world, raw_param_block, intermediates, output)


def _provenance(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("provenance must be an object")
    for key in ("oracle", "binary_sha256", "function", "parameter_block_origin"):
        if key not in value:
            _fail(f"provenance missing {key}")
    if value["oracle"] not in _ORACLES:
        _fail(f"provenance.oracle must be one of {sorted(_ORACLES)}")
    digest = value["binary_sha256"]
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        _fail("provenance.binary_sha256 must be a lowercase SHA-256 hex digest")
    if not isinstance(value["function"], str) or not value["function"]:
        _fail("provenance.function must be a non-empty string")
    if value["parameter_block_origin"] not in _PARAM_ORIGINS:
        _fail(f"provenance.parameter_block_origin must be one of {sorted(_PARAM_ORIGINS)}")
    return dict(value)


def _raw_param_block(value: Any, provenance: Mapping[str, Any]) -> BinaryDescriptor:
    if not isinstance(value, dict) or value.get("format") != "raw":
        _fail("raw_param_block must be an object with format 'raw'")
    descriptor = _descriptor(value.get("descriptor"), "raw_param_block.descriptor")
    relocations = value.get("relocations", [])
    if not isinstance(relocations, list):
        _fail("raw_param_block.relocations must be an array")
    seen: set[tuple[int, int]] = set()
    for index, relocation in enumerate(relocations):
        label = f"raw_param_block.relocations[{index}]"
        if not isinstance(relocation, dict):
            _fail(f"{label} must be an object")
        offset = relocation.get("offset")
        width = relocation.get("width")
        target = relocation.get("target")
        if not _nonnegative_int(offset) or width not in (4, 8):
            _fail(f"{label} requires non-negative offset and width 4 or 8")
        if offset + width > descriptor.size:
            _fail(f"{label} exceeds raw parameter block")
        if not isinstance(target, str) or not target:
            _fail(f"{label}.target must be a non-empty string")
        if (offset, width) in seen:
            _fail(f"duplicate relocation at {offset}:{offset + width}")
        seen.add((offset, width))
    if provenance["parameter_block_origin"] == "binary-built" and not relocations:
        _fail("binary-built raw parameter block must declare relocations")
    return descriptor


def _image_record(value: Any, label: str, *, require_argb: bool = False) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(f"{label} must be an object")
    for key in ("format", "width", "height", "rowbytes", "bpc", "descriptor"):
        if key not in value:
            _fail(f"{label} missing {key}")
    if value["format"] not in ("ARGB", "SCALAR", "INTERLEAVED"):
        _fail(f"{label}.format must be 'ARGB', 'SCALAR', or 'INTERLEAVED'")
    if require_argb and value["format"] != "ARGB":
        _fail(f"{label}.format must be 'ARGB'")
    for key in ("width", "height", "rowbytes"):
        if not _positive_int(value[key]):
            _fail(f"{label}.{key} must be a positive integer")
    if value["bpc"] not in (8, 16, 32):
        _fail(f"{label}.bpc must be 8, 16, or 32")
    if value["format"] == "INTERLEAVED":
        channels = value.get("channels")
        if (not isinstance(channels, list) or not channels or
                any(not isinstance(channel, str) or not channel for channel in channels) or
                len(set(channels)) != len(channels)):
            _fail(f"{label}.channels must be a non-empty array of unique names")
        channel_count = len(channels)
    else:
        channel_count = 4 if value["format"] == "ARGB" else 1
    bytes_per_pixel = channel_count * (value["bpc"] // 8)
    if value["rowbytes"] < value["width"] * bytes_per_pixel:
        _fail(f"{label}.rowbytes is smaller than one ARGB row")
    record = dict(value)
    record["descriptor"] = _descriptor(value["descriptor"], f"{label}.descriptor")
    expected = value["rowbytes"] * value["height"]
    if record["descriptor"].size != expected:
        _fail(f"{label}.descriptor.size must equal rowbytes * height ({expected})")
    return record


def _descriptor(value: Any, label: str) -> BinaryDescriptor:
    if not isinstance(value, dict):
        _fail(f"{label} must be an object")
    missing = _REQUIRED_DESCRIPTOR_KEYS - value.keys()
    if missing:
        _fail(f"{label} missing {sorted(missing)[0]}")
    blob = value["blob"]
    if not isinstance(blob, str) or not blob or Path(blob).is_absolute() or "\\" in blob:
        _fail(f"{label}.blob must be a relative POSIX path")
    blob_path = Path(blob)
    if ".." in blob_path.parts:
        _fail(f"{label}.blob may not escape the fixture directory")
    if not _nonnegative_int(value["offset"]):
        _fail(f"{label}.offset must be a non-negative integer")
    if not _positive_int(value["size"]):
        _fail(f"{label}.size must be a positive integer")
    digest = value["sha256"]
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        _fail(f"{label}.sha256 must be a lowercase SHA-256 hex digest")
    return BinaryDescriptor(blob, value["offset"], value["size"], digest)


def _verify_payloads(descriptors: list[BinaryDescriptor], root: Path) -> None:
    for descriptor in descriptors:
        blob_path = root / Path(descriptor.blob)
        try:
            blob = blob_path.read_bytes()
        except (FileNotFoundError, OSError) as exc:
            _fail(f"missing blob: {descriptor.blob}", exc)
        end = descriptor.offset + descriptor.size
        if end > len(blob):
            _fail(f"size mismatch: {descriptor.blob} has no range {descriptor.offset}:{end}")
        actual = hashlib.sha256(blob[descriptor.offset:end]).hexdigest()
        if actual != descriptor.sha256:
            _fail(f"hash mismatch: {descriptor.blob} range {descriptor.offset}:{end}")


def _reject_overlaps(descriptors: list[BinaryDescriptor]) -> None:
    by_blob: dict[str, list[tuple[int, int]]] = {}
    for descriptor in descriptors:
        by_blob.setdefault(descriptor.blob, []).append((descriptor.offset, descriptor.offset + descriptor.size))
    for blob, ranges in by_blob.items():
        ranges.sort()
        for previous, current in zip(ranges, ranges[1:]):
            if current[0] < previous[1]:
                _fail(f"overlapping descriptors in {blob}: {previous} and {current}")


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _fail(message: str, cause: BaseException | None = None) -> None:
    error = FixtureContractError(message)
    if cause is not None:
        raise error from cause
    raise error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path, help="Fixture directory or manifest JSON.")
    args = parser.parse_args()
    target = args.fixture.resolve()
    fixture = verify_manifest(target) if target.is_file() else verify_fixture(target)
    print(f"[OK] fixture verified: case_id={fixture.case_id} scope={fixture.scope} oracle={fixture.provenance['oracle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
