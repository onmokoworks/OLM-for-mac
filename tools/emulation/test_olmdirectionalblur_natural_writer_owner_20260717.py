#!/usr/bin/env python3
"""Bound the angle-0 natural caller's ownership of writer-entry float RGBA."""

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
REPORT = ROOT / "refs/conformance/olmdirectionalblur_natural_writer_owner_20260717.json"
WRAPPER = 0x180006700
WRITER = 0x180006B30
NATURAL_CALLSITES = (0x18000528A, 0x180005665)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_fixture():
    sys.path.insert(0, str(FIXTURE_PATH.parent))
    import dblur_fullrender_host_fixture_20260711 as fixture  # noqa: E402

    return fixture


def main() -> int:
    fixture = load_fixture()
    original_model_output = fixture.model_output
    captured: list[dict] = []

    def natural_writer(ld, params: int, y: int, x: int, out: bytearray,
                       out_ptr: int, width: int) -> None:
        stride = fixture.u32(ld, params + 0x80A0)
        row0 = fixture.u32(ld, params + 0x8098)
        col0 = fixture.u32(ld, params + 0x809C)
        base = fixture.u64(ld, params + 0x8090)
        index = ((row0 + y) * stride + col0 + x)
        rgba = list(struct.unpack("<4f", ld.read_bytes(base + index * 16, 16)))
        ld.call_function(WRITER, int_args=[params, x, y, 0, out_ptr], max_instructions=1000)
        packed = list(ld.read_bytes(out_ptr, 4))
        address = (y * width + x) * 4
        out[address:address + 4] = bytes(packed)
        if len(captured) < 8:
            captured.append({
                "xy": [x, y],
                "params": hex(params),
                "float_base": hex(base),
                "row0": row0,
                "col0": col0,
                "stride_floats": stride,
                "float_cell_index": index,
                "float_byte_offset": index * 16,
                "writer_entry_rgba_f32": rgba,
                "writer_entry_argb8": packed,
            })

    fixture.model_output = natural_writer
    with tempfile.TemporaryDirectory(prefix="olm_directionalblur_natural_owner_") as name:
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

    execution = fixture_report["execution"]
    checkpoints = execution["checkpoints"]
    callbacks = [call["callback"] for call in execution["iterate_calls"]]
    required_checkpoints = {"first_iterate", "rotateback", "final_host_output"}
    blocked = fixture_report.get("blocked", {})
    writer_checkpoint = (
        fixture_report["status"] == "ok"
        or blocked.get("reason") == "iterate8-suite-abi"
    )
    if fixture_status != 0 or not writer_checkpoint or not fixture_report["output"].get("complete", False):
        raise RuntimeError(
            "BLOCKED_FAIL_CLOSED: natural fixture did not reach bounded writer checkpoint: "
            + json.dumps(blocked, sort_keys=True)
        )
    if not required_checkpoints.issubset(checkpoints) or callbacks != ["0x180006980", "0x180006b30"]:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: natural caller checkpoints are incomplete")
    if not captured:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: real writer entry was not observed")
    output_call = execution["iterate_calls"][1]
    natural_captured = [item for item in captured if item["params"] == output_call["params"]]
    if not natural_captured:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: no writer sample belongs to natural output Iterate8 refcon")

    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_natural_writer_owner_checkpoint",
        "status": "pass",
        "scope": "Mac-local Unicorn natural 8bpc caller at requested angle 0; bounded writer-entry ownership only",
        "claim_scope": "No Windows live values and no AE-exact claim",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": sha256(AEX),
            "fixture": str(FIXTURE_PATH.relative_to(ROOT)),
            "fixture_sha256": sha256(FIXTURE_PATH),
            "source": str(SOURCE.relative_to(ROOT)),
            "source_sha256": sha256(SOURCE),
        },
        "natural_path": {
            "requested_angle_degrees": 0,
            "observed_internal_angle_radians": execution["param_context"]["angle_radians"],
            "upstream_callsites": [hex(address) for address in NATURAL_CALLSITES],
            "wrapper": hex(WRAPPER),
            "iterate_callbacks": callbacks,
            "iterate_area": execution["iterate_calls"][0]["area_words"],
            "checkpoints": checkpoints,
        },
        "ownership": {
            "owner": "output Iterate8 callback refcon at [RSP+0x30]; its +0x8090 field owns the writer-entry float buffer",
            "output_iterate_refcon": output_call["params"],
            "output_iterate_stack_slot": "[RSP+0x30]",
            "writer_entry_samples": natural_captured,
            "writer": hex(WRITER),
            "upstream_producer": "unresolved beyond this refcon; post-rotateback internal context is a distinct object",
        },
        "fail_closed": {
            "status": "pass",
            "natural_fixture_status": fixture_report["status"],
            "natural_fixture_blocker": blocked.get("reason"),
            "production_source_edited": False,
            "ledger_edited": False,
            "windows_values_fabricated": False,
            "ae_exact_claim": False,
            "bounded_stop": "real 0x180006b30 writer invoked per natural output callback; no AE host claim",
        },
        "command": "python3 tools/emulation/test_olmdirectionalblur_natural_writer_owner_20260717.py",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "report": str(REPORT.relative_to(ROOT)), "samples": len(natural_captured)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
