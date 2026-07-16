#!/usr/bin/env python3
"""Continuation-safe actual populate plus first downstream target-cell write."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

from PIL import Image
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RIP, UC_X86_REG_RSP

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_iterate8_continuation_transform_20260717.json"
POPULATE = 0x180006980
ROTATE = 0x180001EC0
OUTPUT = 0x180006B30


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_fixture():
    sys.path.insert(0, str(FIXTURE_PATH.parent))
    import dblur_fullrender_host_fixture_20260711 as fixture  # noqa: E402

    return fixture


def f32_cell(ld, address: int) -> list[float]:
    return list(struct.unpack("<4f", ld.read_bytes(address, 16)))


def main() -> int:
    fixture = load_fixture()
    events: list[dict] = []
    state: dict = {"source_ready": False, "target_source": None, "target_writer": None}

    class TracingLoader(fixture.AexLoader):
        last = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.write_events: list[dict] = []
            TracingLoader.last = self

            def mem_write(uc, _access, address, size, value, _user_data):
                if state.get("writer_cell") is None:
                    return
                writer_cell = state["writer_cell"]
                if address < writer_cell + 16 and address + size > writer_cell:
                    self.write_events.append({
                        "address": hex(address), "size": size, "value": hex(value),
                        "rip": hex(uc.reg_read(UC_X86_REG_RIP)),
                        "after_source_ready": state["source_ready"],
                    })

    nested_return = 0x90001000

    def actual_populate(ld, params: int, y: int, x: int, pixel: bytes) -> None:
        pixel_ptr = ld.bump_alloc(4, align=4)
        ld.write_bytes(pixel_ptr, pixel)
        source_base = fixture.u64(ld, params + 0x8078)
        writer_base = fixture.u64(ld, params + 0x8090)
        stride = fixture.u32(ld, params + 0x80A0)
        height = fixture.u32(ld, params + 0x80A4)
        row0 = fixture.u32(ld, params + 0x8098)
        col0 = fixture.u32(ld, params + 0x809C)
        index = (row0 + y) * stride + col0 + x
        source_cell = source_base + index * 16
        writer_cell = writer_base + index * 16
        state["writer_cell"] = writer_cell
        saved = ld.uc.context_save()
        try:
            try:
                ld.uc.mem_map(nested_return, 0x1000)
            except Exception:
                pass
            nested_rsp = 0x0F080000
            ld.uc.mem_write(nested_rsp, struct.pack("<Q", nested_return))
            for register, value in ((UC_X86_REG_RCX, params), (UC_X86_REG_RDX, x),
                                    (UC_X86_REG_R8, y), (UC_X86_REG_R9, pixel_ptr)):
                ld.uc.reg_write(register, value)
            ld.uc.reg_write(UC_X86_REG_RSP, nested_rsp)
            ld.uc.reg_write(UC_X86_REG_RIP, POPULATE)
            ld.uc.emu_start(POPULATE, nested_return, count=10000)
            if ld.uc.reg_read(UC_X86_REG_RIP) != nested_return:
                raise RuntimeError("BLOCKED_FAIL_CLOSED: actual populate missed private continuation")
        finally:
            ld.uc.context_restore(saved)
        # callback_model_check uses a synthetic 16-wide, height-zero buffer;
        # only the natural 26x26 render owns the requested target state.
        if x == 0 and y == 0 and stride == 26 and height == 26 and not state["source_ready"]:
            state["target_source"] = f32_cell(ld, source_cell)
            state["target_writer"] = f32_cell(ld, writer_cell)
            state["source_ready"] = True
            events.append({
                "event": "actual_populate_return",
                "entry": hex(POPULATE), "xy": [x, y],
                "params": hex(params),
                "source_base_0x8078": hex(source_base),
                "writer_base_0x8090": hex(writer_base),
                "width": stride,
                "row0": row0,
                "col0": col0,
                "source_cell": hex(source_cell), "writer_cell": hex(writer_cell),
                "source_rgba_f32": state["target_source"],
                "writer_rgba_f32_before_downstream": state["target_writer"],
            })

    fixture.AexLoader = TracingLoader
    fixture.callback_model_check = lambda _loader, _source, _width: {"status": "skipped", "reason": "natural-only checkpoint"}
    fixture.model_populate = actual_populate
    fixture.model_output = lambda _ld, _params, _y, _x, _out, _out_ptr, _width: None
    with tempfile.TemporaryDirectory(prefix="olm_directionalblur_iterate8_continuation_") as name:
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
    if loader is None:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: actual populate continuation did not construct a loader")
    downstream = [item for item in loader.write_events if item["after_source_ready"]]
    first = downstream[0] if downstream else None
    blocker = fixture_report.get("blocked", {})
    status = "pass" if events and first else "blocked"
    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_iterate8_continuation_transform_checkpoint",
        "status": status,
        "scope": "Mac-local Unicorn natural angle-0 8bpc path with continuation-safe actual populate",
        "claim_scope": "First grounded downstream target-cell write only; no Windows or AE-exact claim",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)), "aex_sha256": sha256(AEX),
            "fixture": str(FIXTURE_PATH.relative_to(ROOT)), "fixture_sha256": sha256(FIXTURE_PATH),
            "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha256(SOURCE),
        },
        "continuation": {
            "callback": hex(POPULATE), "private_return": hex(nested_return),
            "context_save_restore": True, "natural_callback_continued": True,
            "fixture_status": fixture_report["status"], "fixture_blocker": blocker.get("reason"),
            "fixture_blocker_message": blocker.get("message"),
            "write_events": loader.write_events[:16],
        },
        "target": {
            "before": events[0] if events else None,
            "downstream_first_write": first,
            "all_downstream_writes": downstream[:16],
            "writer_transform_entry": hex(ROTATE),
            "writer_callback": hex(OUTPUT),
            "alias_assessment": ("natural source/writer pointers are distinct"
                                 if events and events[0]["source_base_0x8078"] != events[0]["writer_base_0x8090"]
                                 else "unresolved; no natural target event"),
        },
        "nearest_function": {
            "function": "FUN_180001EC0" if first else None,
            "entry": hex(ROTATE),
            "first_write_instruction": first["rip"] if first else None,
            "classification": ("first observed AEX write overlapping the target params+0x8090 cell after actual population"
                                if first else "no downstream write observed"),
        },
        "fail_closed": {
            "status": status,
            "next_unresolved_boundary": blocker.get("reason"),
            "reason": "no downstream write before fixture pre-render-return" if not first else None,
            "production_source_edited": False, "ledger_edited": False,
            "windows_values_fabricated": False, "ae_exact_claim": False,
        },
        "command": "python3 tools/emulation/test_olmdirectionalblur_iterate8_continuation_transform_20260717.py",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "report": str(REPORT.relative_to(ROOT)),
                      "first_write_rip": first["rip"] if first else None,
                      "source_rgba_f32": events[0]["source_rgba_f32"] if events else None}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
