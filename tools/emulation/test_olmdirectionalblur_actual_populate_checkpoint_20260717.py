#!/usr/bin/env python3
"""Attempt the real 8bpc populate callback on the natural 26x26 state."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_actual_populate_checkpoint_20260717.json"
POPULATE = 0x180006980


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_fixture():
    sys.path.insert(0, str(FIXTURE_PATH.parent))
    import dblur_fullrender_host_fixture_20260711 as fixture  # noqa: E402

    return fixture


class StopAfterActualPopulate(RuntimeError):
    pass


def main() -> int:
    fixture = load_fixture()
    captured: dict = {}
    callback_attempts = 0

    class TracingLoader(fixture.AexLoader):
        last = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            TracingLoader.last = self

    def actual_populate(ld, params: int, y: int, x: int, pixel: bytes) -> None:
        nonlocal callback_attempts
        callback_attempts += 1
        pixel_ptr = ld.bump_alloc(4, align=4)
        ld.write_bytes(pixel_ptr, pixel)
        result = ld.call_function(
            POPULATE,
            int_args=[params, x, y, pixel_ptr],
            max_instructions=10000,
        )
        stride = fixture.u32(ld, params + 0x80A0)
        height = fixture.u32(ld, params + 0x80A4)
        row0 = fixture.u32(ld, params + 0x8098)
        col0 = fixture.u32(ld, params + 0x809C)
        source_base = fixture.u64(ld, params + 0x8078)
        writer_base = fixture.u64(ld, params + 0x8090)
        index = (row0 + y) * stride + col0 + x
        source_cell = source_base + index * 16
        writer_cell = writer_base + index * 16
        captured.update({
            "params": hex(params), "xy": [x, y], "source_pixel_argb8": list(pixel),
            "callback_attempt": callback_attempts, "callback_instructions": result["instructions"],
            "plane": {"source_base_0x8078": hex(source_base), "writer_base_0x8090": hex(writer_base),
                      "width": stride, "height": height,
                      "row0": row0, "col0": col0, "cell_index": index,
                      "source_cell_address": hex(source_cell), "writer_cell_address": hex(writer_cell),
                      "cell_bytes": 16},
            "raw_source_rgba_f32": list(struct.unpack("<4f", ld.read_bytes(source_cell, 16))),
            "raw_writer_rgba_f32_before_downstream_copy": list(struct.unpack("<4f", ld.read_bytes(writer_cell, 16))),
        })
        raise StopAfterActualPopulate("checkpoint stop after actual populate callback")

    fixture.AexLoader = TracingLoader
    fixture.model_populate = actual_populate
    fixture.model_output = lambda ld, params, y, x, out, out_ptr, width: None
    with tempfile.TemporaryDirectory(prefix="olm_directionalblur_actual_populate_") as name:
        temp = Path(name)
        source = temp / "source_16x16.png"
        Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278)).save(source)
        output = temp / "fixture.json"
        sys.argv = [
            str(FIXTURE_PATH), "--source", str(source), "--output", str(output),
            "--angle", "0", "--downsample-num", "1", "--downsample-den", "1",
            "--front-strength", "8", "--size-variation", "0", "--front-sharp-tail", "0",
            "--back-strength", "0", "--back-alpha-fade", "0", "--noise-variation", "0",
            "--world-area", "0", "0", "16", "16", "--row-padding", "12",
            "--no-detour-rotate", "--max-instructions", "20000000",
        ]
        fixture_status = fixture.main()
        fixture_report = json.loads(output.read_text(encoding="utf-8"))

    if not captured:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: actual 0x180006980 did not return a captured cell")

    blocked = fixture_report.get("blocked", {})
    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_actual_populate_checkpoint",
        "status": "pass",
        "scope": "Mac-local Unicorn natural angle-0 8bpc callback attempt; first-cell raw float capture",
        "claim_scope": "Actual AEX populate callback only; no Windows or AE-exact claim",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)), "aex_sha256": sha256(AEX),
            "fixture": str(FIXTURE_PATH.relative_to(ROOT)), "fixture_sha256": sha256(FIXTURE_PATH),
            "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha256(SOURCE),
        },
        "actual_callback": {
            "entry": hex(POPULATE),
            "fixture_model_populate_replaced": True,
            "minimum_abi": "(params, x=RDX, y=R8, source_pixel=R9)",
            "captured": captured,
            "callback_attempts": callback_attempts,
        },
        "natural_fixture": {
            "status": fixture_report["status"],
            "fixture_return": fixture_status,
            "blocked": blocked,
            "callbacks_before_stop": fixture_report["execution"]["iterate_calls"],
            "checkpoints": fixture_report["execution"]["checkpoints"],
        },
        "nearest_blocker": {
            "kind": "intentional_checkpoint_stop",
            "reason": str(StopAfterActualPopulate("checkpoint stop after actual populate callback")),
            "continuation_tested": False,
            "first_unresolved_boundary": "PF Iterate8 continuation after actual callback; no synthetic recovery",
            "fixture_report_reason": blocked.get("reason"),
        },
        "fail_closed": {
            "status": "pass",
            "actual_population_owner": hex(POPULATE),
            "production_source_edited": False, "ledger_edited": False,
            "windows_values_fabricated": False, "ae_exact_claim": False,
        },
        "command": "python3 tools/emulation/test_olmdirectionalblur_actual_populate_checkpoint_20260717.py",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "report": str(REPORT.relative_to(ROOT)),
                      "callback": hex(POPULATE), "raw_source_rgba_f32": captured["raw_source_rgba_f32"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
