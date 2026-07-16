#!/usr/bin/env python3
"""Resolve R15 allocation/layout and fail closed at the natural population boundary."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

from PIL import Image
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_RIP

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_r15_population_owner_20260717.json"
POPULATE = 0x180006980
OUTPUT = 0x180006B30
PRODUCER = 0x180004A20
ALLOC_SIZE_SITE = 0x180004C02
ALLOC_HANDLE_CALL = 0x180004C0C
LOCK_CALL = 0x180004C79
LOCK_RETURN = 0x180004C7C


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_fixture():
    sys.path.insert(0, str(FIXTURE_PATH.parent))
    import dblur_fullrender_host_fixture_20260711 as fixture  # noqa: E402

    return fixture


def main() -> int:
    fixture = load_fixture()
    output_samples: list[dict] = []

    class TracingLoader(fixture.AexLoader):
        last = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.heap_writes: list[dict] = []
            TracingLoader.last = self

            def mem_write(uc, _access, address, size, value, _user_data):
                if 0x20000000 <= address < 0x21000000 and size in (4, 8, 16):
                    self.heap_writes.append({
                        "address": hex(address), "size": size, "value": hex(value),
                        "rip": hex(uc.reg_read(UC_X86_REG_RIP)),
                    })

            self.uc.hook_add(UC_HOOK_MEM_WRITE, mem_write)

    original_model_output = fixture.model_output

    def capture_model_output(ld, params: int, y: int, x: int, out: bytearray,
                             out_ptr: int, width: int) -> None:
        if len(output_samples) < 12:
            stride = fixture.u32(ld, params + 0x80A0)
            height = fixture.u32(ld, params + 0x80A4)
            row0 = fixture.u32(ld, params + 0x8098)
            col0 = fixture.u32(ld, params + 0x809C)
            base = fixture.u64(ld, params + 0x8090)
            index = (row0 + y) * stride + col0 + x
            output_samples.append({
                "params": hex(params), "xy": [x, y], "float_base": hex(base),
                "row0": row0, "col0": col0, "stride_floats": stride,
                "height": height,
                "cell_index": index, "cell_address": hex(base + index * 16),
            })
        original_model_output(ld, params, y, x, out, out_ptr, width)

    fixture.AexLoader = TracingLoader
    fixture.model_output = capture_model_output
    with tempfile.TemporaryDirectory(prefix="olm_directionalblur_r15_owner_") as name:
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

    loader = TracingLoader.last
    if loader is None or not output_samples:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: natural output callback did not expose target layout")
    output_call = next((call for call in fixture_report["execution"]["iterate_calls"]
                        if call["callback"] == hex(OUTPUT)), None)
    if output_call is None:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: output Iterate8 ABI missing")
    natural_samples = [item for item in output_samples if item["params"] == output_call["params"]]
    if not natural_samples:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: natural output refcon did not reach model population")
    sample = natural_samples[0]
    target = int(sample["cell_address"], 16)
    target_writes = [item for item in loader.heap_writes
                     if int(item["address"], 16) < target + 16
                     and int(item["address"], 16) + item["size"] > target]
    callback_log = fixture_report["execution"].get("callback_log", [])
    lock_returns = [item for item in callback_log
                    if item["label"] == "PFHandle.lock" and item["ret"] == int(sample["float_base"], 16)]
    new_calls = [item for item in callback_log if item["label"] == "PFHandle.new"]
    allocation_size = sample["stride_floats"] * (fixture.u32(loader, int(sample["params"], 16) + 0x80A4)) * 4
    actual_aex_population_writes = [item for item in target_writes if int(item["rip"], 16) == POPULATE]
    fixture_population_writes = [item for item in target_writes if int(item["rip"], 16) != POPULATE]

    if fixture_status != 0 or not fixture_report["output"].get("complete", False):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: natural fixture did not complete")
    if not lock_returns:
        raise RuntimeError(
            "BLOCKED_FAIL_CLOSED: PF Handle lock did not return R15 buffer: "
            + json.dumps({"base": sample["float_base"], "locks": [item for item in callback_log if item["label"] == "PFHandle.lock"][-8:]}, sort_keys=True)
        )
    if actual_aex_population_writes:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: unexpected AEX population write classification")
    if not fixture_population_writes:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: target pixel population was not observed")

    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_r15_population_owner_checkpoint",
        "status": "blocked",
        "scope": "Mac-local natural angle-0 fixture; R15 allocation and target float-cell population ownership",
        "claim_scope": "Allocation/layout resolved to the fixture host suite; population owner escapes the natural AEX path",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)), "aex_sha256": sha256(AEX),
            "fixture": str(FIXTURE_PATH.relative_to(ROOT)), "fixture_sha256": sha256(FIXTURE_PATH),
            "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha256(SOURCE),
        },
        "allocation": {
            "producer_function": hex(PRODUCER),
            "size_formula": "params+0x80a0 * params+0x80a4 * 4 bytes",
            "size_site": hex(ALLOC_SIZE_SITE),
            "observed_width": sample["stride_floats"],
            "observed_height": sample["height"],
            "observed_size_bytes": allocation_size,
            "handle_creation_call": hex(ALLOC_HANDLE_CALL),
            "lock_call": hex(LOCK_CALL),
            "lock_return": hex(LOCK_RETURN),
            "lock_return_samples": lock_returns,
            "handle_new_call_count": len(new_calls),
            "ownership_boundary": "PF Handle Suite new/lock callback; suite internals are not production-AEX execution",
        },
        "layout": {
            "writer_float_base": sample["float_base"],
            "row0": sample["row0"], "col0": sample["col0"],
            "stride_floats": sample["stride_floats"],
            "target_xy": sample["xy"], "target_cell_index": sample["cell_index"],
            "target_cell_address": sample["cell_address"],
            "target_cell_bytes": 16,
        },
        "population": {
            "nearest_actual_aex_population_function": hex(POPULATE),
            "actual_aex_population_writes": actual_aex_population_writes,
            "observed_fixture_population_writes": fixture_population_writes[:8],
            "owner": "fixture.model_populate invoked by the emulated PF Iterate8 callback",
            "natural_aex_population_observed": False,
        },
        "natural_checkpoint": {
            "fixture_status": fixture_report["status"],
            "callbacks": [call["callback"] for call in fixture_report["execution"]["iterate_calls"]],
            "checkpoints": fixture_report["execution"]["checkpoints"],
            "output_samples": natural_samples,
        },
        "fail_closed": {
            "status": "blocked",
            "reason": "population-owner-escaped-natural-fixture",
            "first_missing_boundary": "PF Iterate8 callback 0x180006980 was replaced by fixture.model_populate",
            "production_source_edited": False, "ledger_edited": False,
            "windows_values_fabricated": False, "ae_exact_claim": False,
        },
        "command": "python3 tools/emulation/test_olmdirectionalblur_r15_population_owner_20260717.py",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "blocked", "report": str(REPORT.relative_to(ROOT)),
                      "allocation_bytes": allocation_size, "target_writes": len(target_writes)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
