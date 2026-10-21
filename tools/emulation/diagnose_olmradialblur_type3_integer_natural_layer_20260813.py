#!/usr/bin/env python3
"""Read-only PF8/PF16 Type3 full-alpha natural-Layer diagnostic."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "tools/emulation/test_olmradialblur_type3_all_depth_public_closure_20260813.py"


def load_base():
    spec = importlib.util.spec_from_file_location("radial_type3_natural_base", BASE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def natural_layer(base, depth: int) -> bytes:
    cfg = base.CONFIG[depth]
    raw = bytearray(cfg["rb"] * base.H)
    for y in range(base.H):
        for x in range(base.W):
            if depth == 8:
                values = (255, (x * 255) // 8, (y * 255) // 6, ((x + y) * 255) // 14)
                struct.pack_into("<4B", raw, y * cfg["rb"] + x * 4, *values)
            else:
                values = (32768, (x * 32768) // 8, (y * 32768) // 6, ((x + y) * 32768) // 14)
                struct.pack_into("<4H", raw, y * cfg["rb"] + x * 8, *values)
        active = base.W * cfg["pixel"]
        raw[y * cfg["rb"] + active:(y + 1) * cfg["rb"]] = bytes([0xA0 + y]) * (cfg["rb"] - active)
    return bytes(raw)


def active_rows(base, depth: int, payload: bytes) -> bytes:
    cfg = base.CONFIG[depth]
    active = base.W * cfg["pixel"]
    return b"".join(payload[y * cfg["rb"]:y * cfg["rb"] + active] for y in range(base.H))


def patched_source(base, layer_hashes: dict[int, str]) -> str:
    text = base.SOURCE.read_text()
    anchors = {
        8: '"05177a5cb397745ccf2ddafa8a0364684e5ffbcdfe5e4be03b4088c8c9d90df1",\n\t\t};',
        16: '"543846ff19163d48daae7f16a50fcaf17eb95e9954de64ea23b7e1b3495be901",\n\t\t};',
    }
    for depth, anchor in anchors.items():
        if text.count(anchor) != 1:
            raise RuntimeError(f"source anchor drift at PF{depth}")
        replacement = anchor[:-3] + f'\t\t\t"{layer_hashes[depth]}",\n\t\t}};'
        text = text.replace(anchor, replacement)
    count_anchor = "MatchesType3SmallActiveHash<PixelT>(noise_world, layers, 2)"
    if text.count(count_anchor) != 2:
        raise RuntimeError("integer Layer count anchors drift")
    text = text.replace(count_anchor, "MatchesType3SmallActiveHash<PixelT>(noise_world, layers, 3)")
    return text


def main() -> int:
    base = load_base()
    layers = {depth: natural_layer(base, depth) for depth in (8, 16)}
    layer_hashes = {depth: sha(active_rows(base, depth, payload)) for depth, payload in layers.items()}
    rows = []
    with tempfile.TemporaryDirectory(prefix="radial-type3-integer-natural-") as temporary:
        source_path = Path(temporary) / "OLMRadialBlur.cpp"
        source_path.write_text(patched_source(base, layer_hashes))
        old_source = base.SOURCE
        base.SOURCE = source_path
        try:
            for depth in (8, 16):
                for source_kind in ("canonical", "zero", "constant", "impulse", "checker"):
                    source_bytes = base.source(depth, source_kind)
                    observed = base.actual(depth, source_bytes, layers[depth])
                    produced = base.candidate(depth, observed, source_bytes, layers[depth])
                    keys = ("source_span", "pre_blur", "post_blur", "output")
                    matches = {key: produced[key] == observed[key] for key in keys}
                    matches["classic_output"] = produced["classic_output"] == observed["output"]
                    matches["smart_output"] = produced["smart_output"] == observed["output"]
                    rows.append({
                        "depth": depth,
                        "source_kind": source_kind,
                        "layer_active_sha256": layer_hashes[depth],
                        "matches": matches,
                        "actual": {key: sha(observed[key]) for key in keys},
                        "candidate": {key: sha(produced[key]) for key in (*keys, "classic_output", "smart_output")},
                        "reject_controls": produced["reject_controls"],
                    })
        finally:
            base.SOURCE = old_source
    result = {
        "schema": "olmradialblur.type3-integer-natural-layer-diagnostic/1",
        "status": "exact" if all(all(row["matches"].values()) for row in rows) else "mismatch",
        "rows": rows,
        "rows_sha256": sha(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()),
        "scope": "temporary source candidate only; no tracked production edit, install, AE, or arbitrary-source claim",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "exact" else 1


if __name__ == "__main__":
    raise SystemExit(main())
