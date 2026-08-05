#!/usr/bin/env python3
"""Migrate only stale Python callback code hashes in the pinned case0010 checkpoint."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import aex_loader as al  # noqa: E402
import test_m4_case0010 as m4  # noqa: E402

SOURCE = ROOT / "refs/fixtures/olmradialblur_case0010_rotation_full_planes_20260805/post_worker_pre_pf8.aexcp"
OUTPUT = ROOT / "refs/fixtures/olmradialblur_case0010_rotation_full_planes_20260805/post_worker_pre_pf8_current_callbacks.aexcp"
SOURCE_SHA256 = "47b7911d1ba4628b5c318d220ad53d06ec0819c4e8fd805d6c6d28ebf871d67a"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_checkpoint(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    prefix_size = len(al.CHECKPOINT_MAGIC) + 4 + 8 + 32
    prefix = raw[:prefix_size]
    if not prefix.startswith(al.CHECKPOINT_MAGIC):
        raise RuntimeError("checkpoint magic mismatch")
    version, header_size = struct.unpack(
        "<IQ", prefix[len(al.CHECKPOINT_MAGIC):len(al.CHECKPOINT_MAGIC) + 12])
    if version != al.CHECKPOINT_VERSION:
        raise RuntimeError("checkpoint version mismatch")
    header_bytes = raw[prefix_size:prefix_size + header_size]
    if hashlib.sha256(header_bytes).digest() != prefix[-32:]:
        raise RuntimeError("checkpoint header checksum mismatch")
    return json.loads(header_bytes.decode("ascii")), raw[prefix_size + header_size:]


def fresh_loader() -> al.AexLoader:
    params = m4.load_case0010_params()
    image = Image.open(m4.INPUT_PNG).convert("RGBA")
    width, height = image.size
    red, green, blue, alpha = image.split()
    input_bytes = Image.merge("RGBA", (alpha, red, green, blue)).tobytes()
    loader = al.AexLoader(str(m4.AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    spbasic = m4.build_host_suites(loader)
    render_ctx = m4.build_render_context(loader, spbasic)
    m4.build_world(loader, width, height, input_bytes)
    m4.build_world(loader, width, height, bytes(width * height * 4))
    param_ctx = m4.build_param_block(loader)
    m4.install_reader_detours(loader, params)
    metadata_expected = {
        "render_ctx": f"0x{render_ctx:x}",
        "param_ctx": f"0x{param_ctx:x}",
    }
    loader._case0010_metadata_expected = metadata_expected  # type: ignore[attr-defined]
    return loader


def main() -> int:
    if sha256(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("source checkpoint SHA256 mismatch")
    header, payload = read_checkpoint(SOURCE)
    loader = fresh_loader()
    expected_callbacks = [
        {"address": address, "label": label, "handler": al._callable_fingerprint(handler)}
        for address, (label, handler) in sorted(loader.callbacks.items())
    ]
    old_callbacks = header.get("callbacks", [])
    if len(old_callbacks) != len(expected_callbacks) or len(old_callbacks) != 14:
        raise RuntimeError("unexpected callback count")
    migrations = []
    for old, current in zip(old_callbacks, expected_callbacks):
        if old["address"] != current["address"] or old["label"] != current["label"]:
            raise RuntimeError("callback address/label changed")
        old_module = old["handler"].get("module")
        current_module = current["handler"].get("module")
        if (old_module, current_module) not in {
            (current_module, current_module), ("__main__", "test_m4_case0010")
        }:
            raise RuntimeError("callback module changed outside the pinned script/import transition")
        if old["handler"].get("qualname") != current["handler"].get("qualname"):
            raise RuntimeError("callback qualname changed")
        migrations.append({
            "address": old["address"],
            "label": old["label"],
            "old_code_sha256": old["handler"].get("code_sha256"),
            "new_code_sha256": current["handler"].get("code_sha256"),
        })
    expected_imports = {
        name: al._callable_fingerprint(handler)
        for name, handler in sorted(loader.import_impls.items())
    }
    if header.get("import_impls") != expected_imports:
        raise RuntimeError("import implementation topology changed")
    metadata = header.get("metadata", {})
    expected_meta = loader._case0010_metadata_expected  # type: ignore[attr-defined]
    if any(metadata.get(key) != value for key, value in expected_meta.items()):
        raise RuntimeError("deterministic pointer metadata changed")
    if header["registers"]["gp"]["rip"] != m4.FUN_180007B4A:
        raise RuntimeError("checkpoint is not at post-worker RIP")

    header["callbacks"] = expected_callbacks
    header.setdefault("metadata", {})["callback_fingerprint_migration"] = {
        "schema": "olmradialblur.case0010-callback-fingerprint-migration/1",
        "source_checkpoint_sha256": SOURCE_SHA256,
        "reason": "marshal code hashes changed after line-only harness layout edits; callback identities and import topology are unchanged",
        "migrations": migrations,
    }
    header_bytes = json.dumps(
        header, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    prefix = al.CHECKPOINT_MAGIC + struct.pack("<IQ", al.CHECKPOINT_VERSION, len(header_bytes))
    prefix += hashlib.sha256(header_bytes).digest()
    OUTPUT.write_bytes(prefix + header_bytes + payload)

    verify = fresh_loader()
    loaded = verify.load_checkpoint(OUTPUT)
    if loaded["registers"]["gp"]["rip"] != m4.FUN_180007B4A:
        raise RuntimeError("migrated checkpoint restored wrong RIP")
    print(json.dumps({
        "status": "loadable",
        "output": str(OUTPUT.relative_to(ROOT)),
        "sha256": sha256(OUTPUT),
        "callback_migrations": len(migrations),
        "rip": f"0x{loaded['registers']['gp']['rip']:x}",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
