#!/usr/bin/env python3
"""Independent PF8 Zoom small-frame actual-AEX/production fixture."""

from __future__ import annotations

import hashlib, json, struct, zlib
from pathlib import Path

import numpy as np
import test_olmradialblur_zoom_pf16_small_actual_aex_20260805 as zoom

ROOT = zoom.fixture.ROOT
FIXTURE = ROOT / "refs/fixtures/olmradialblur_zoom_pf8_small_20260805"
REPORT = ROOT / "refs/conformance/olmradialblur_zoom_pf8_small_actual_aex_20260805.json"
W, H, ROWBYTES, VISIBLE = 9, 7, 44, 36
EXPECTED = {
    "source_pf8": ("52e90891881bcacb8f3ac3e737ba5b9905d4a63fb5d7aefe55c43b21fe91c240", "ea5adddaede98f6f2a86139efb54df542ffc5a5ece4ad40f56c87dc94866c7f2"),
    "pre_blur": ("65d238f8d0afa5fe9291d8a1e434f3d60359147c3f70d0428c1366241bf55805", "767d31aeb62c7a153abce84c041ef1332408225bf5ae8d596a81b1c13e835b82"),
    "post_blur": ("3a4558578778fd15acbec55d6662e1f2e3760c6fbaa98eb378ffdfaa157c5123", "ecd78bf283604643bb3cd338be76b438e3f86a1db1dc79d9d8e241a583214f27"),
    "output": ("c970cdd100cd3df066e69d76da61b106c18834ba41353406e0c9f06bcf87e4a4", "ae3f1c8ff35ccc7c3397eb7149524352d99ae3e57eb471bd5417046591834815"),
}
SOURCE_KEY = "source_pf8"
BITDEPTH = 8
PIXEL_CPP = "PF_Pixel8"
PIXEL_BYTES = 4
OWNER = 0x180007520
ZOOM_RETURN = 0x180007B12
KIND = "olmradialblur_zoom_pf8_small_actual_aex_20260805"
SCOPE = "independent PF8 Zoom outer-only Strength4/mode1/offset0, padded 9x7; no PF16/PF32 source or quantization reuse and no AE-host claim"
TYPED_CONTRACT = {"source": "independent PF_Pixel8 ARGB bytes", "writer": "PF8 floor/clamp path", "radius_neighbor": "PF8 clamped", "deep_quantization_reused": False}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def source_frame(output_seed: bool = False) -> bytes:
    raw = bytearray(ROWBYTES * H)
    for y in range(H):
        for x in range(W):
            if output_seed:
                argb = (0x77, 0x66, 0x55, 0x44)
            else:
                argb = (
                    255 if (x + y) % 5 else 127,
                    (x * 31 + y * 7) % 256,
                    (x * 11 + y * 29) % 256,
                    (x * 47 + y * 13) % 256,
                )
            struct.pack_into("<4B", raw, y * ROWBYTES + x * 4, *argb)
        raw[y * ROWBYTES + VISIBLE:(y + 1) * ROWBYTES] = bytes([0xA0 + y]) * (ROWBYTES - VISIBLE)
    return bytes(raw)


def build_world(loader, payload: bytes):
    data = loader.bump_alloc(len(payload), align=64)
    loader.write_bytes(data, payload)
    world = loader.host_alloc(0x80)
    loader.write_bytes(world, b"\0" * 0x80)
    loader.write_bytes(world + 0x18, struct.pack("<Q", data))
    loader.write_bytes(world + 0x20, struct.pack("<I", ROWBYTES))
    loader.write_bytes(world + 0x24, struct.pack("<I", W))
    loader.write_bytes(world + 0x28, struct.pack("<I", H))
    loader.write_bytes(world + 0x2C, struct.pack("<H", BITDEPTH))
    return world, data


def configure():
    zoom.OUTER_STRENGTH = 4
    zoom.OUTER_OFFSET_MODE = 1
    zoom.OUTER_OFFSET = 0
    zoom.PIXEL_CPP = PIXEL_CPP
    zoom.PIXEL_BYTES = PIXEL_BYTES
    zoom.USE_RENDER_WORLD_FINAL = globals().get("USE_RENDER_WORLD_FINAL", False)
    zoom.RENDER_WORLD_BITDEPTH = BITDEPTH
    zoom.ZOOM_RETURN = ZOOM_RETURN
    zoom.fixture.OWNER = OWNER
    zoom.fixture.W, zoom.fixture.H = W, H
    zoom.fixture.ROWBYTES, zoom.fixture.VISIBLE = ROWBYTES, VISIBLE
    zoom.fixture.source_frame = source_frame
    zoom.fixture.build_world = build_world


def main():
    configure()
    actual = zoom.actual_aex()
    mac = zoom.mac_production(actual)
    FIXTURE.mkdir(parents=True, exist_ok=True)
    artifacts, matches, differences = {}, {}, {}
    source_raw = source_frame()
    source_encoded = zlib.compress(source_raw, 9)
    source_path = FIXTURE / f"{SOURCE_KEY}.bin.zlib"
    source_path.write_bytes(source_encoded)
    artifacts[SOURCE_KEY] = {"raw_sha256": sha(source_raw), "zlib_sha256": sha(source_encoded), "bytes": len(source_raw), "path": str(source_path.relative_to(ROOT))}
    geometry = actual.pop("geometry")
    for name, raw in actual.items():
        encoded = zlib.compress(raw, 9)
        path = FIXTURE / f"{name}.bin.zlib"
        path.write_bytes(encoded)
        artifacts[name] = {"raw_sha256": sha(raw), "zlib_sha256": sha(encoded), "bytes": len(raw), "path": str(path.relative_to(ROOT))}
        matches[name] = mac[name] == raw
        left, right = np.frombuffer(raw, dtype=np.uint8), np.frombuffer(mac[name], dtype=np.uint8)
        diff = np.flatnonzero(left != right)
        differences[name] = {"different_bytes": int(diff.size), "first_byte": int(diff[0]) if diff.size else None, "mac_raw_sha256": sha(mac[name])}
    fixture_hashes_exact = all((v["raw_sha256"], v["zlib_sha256"]) == EXPECTED[k] for k, v in artifacts.items())
    aex_hash = sha(zoom.fixture.m4.AEX_PATH.read_bytes())
    padding_exact = all(mac["output"][y*ROWBYTES+VISIBLE:(y+1)*ROWBYTES] == bytes([0xA0+y])*(ROWBYTES-VISIBLE) for y in range(H))
    angular_count, radius_count = struct.unpack("<II", geometry)
    exact = all(matches.values()) and fixture_hashes_exact and padding_exact and aex_hash == zoom.fixture.AEX_SHA256
    report = {
        "kind": KIND,
        "status": "exact" if exact else "mismatch",
        "scope": SCOPE,
        "aex": {"sha256": aex_hash, "identity_exact": aex_hash == zoom.fixture.AEX_SHA256, "owner": hex(OWNER), "zoom_core": "0x1800056f0"},
        "geometry": {"width": W, "height": H, "rowbytes": ROWBYTES, "visible_bytes": VISIBLE, "padding_bytes": ROWBYTES-VISIBLE, "angular_count": angular_count, "radius_count": radius_count},
        "typed_contract": TYPED_CONTRACT,
        "matches": matches, "differences": differences, "padding_exact": padding_exact,
        "fixture_hashes_exact": fixture_hashes_exact, "artifacts": artifacts,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
