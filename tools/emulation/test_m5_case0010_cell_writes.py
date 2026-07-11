from __future__ import annotations

import json
import struct
import sys
import time
from pathlib import Path

from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_RIP

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
import test_m4_case0010 as m4  # noqa: E402


WATCH_CELLS = [
    (843, 1601),
    (843, 1602),
    (844, 1603),
    (845, 1603),
]


def cell_addr(base: int, cols: int, row: int, col: int) -> int:
    return base + ((row * cols + col) * 16)


def read4f(loader: AexLoader, addr: int) -> tuple[float, float, float, float]:
    return struct.unpack("<4f", loader.read_bytes(addr, 16))


def main() -> int:
    params = m4.load_case0010_params()
    from PIL import Image

    image = Image.open(m4.INPUT_PNG).convert("RGBA")
    width, height = image.size
    r, g, b, a = image.split()
    input_bytes = Image.merge("RGBA", (a, r, g, b)).tobytes()
    output_bytes = bytes(width * height * 4)

    loader = AexLoader(str(m4.AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    spbasic = m4.build_host_suites(loader)
    render_ctx = m4.build_render_context(loader, spbasic)
    input_world = m4.build_world(loader, width, height, input_bytes)
    output_world = m4.build_world(loader, width, height, output_bytes)
    param_ctx = m4.build_param_block(loader)
    provenance = m4.install_reader_detours(loader, params)

    captured = {"rotation_param1": 0, "rotation_param2": 0, "watches": {}, "events": []}

    def capture_rotation(ld: AexLoader, address: int, size: int) -> None:
        if captured["rotation_param1"]:
            return
        captured["rotation_param1"] = ld.uc.reg_read(m4.UC_X86_REG_RCX)
        captured["rotation_param2"] = ld.uc.reg_read(m4.UC_X86_REG_RDX)
        work_param1 = captured["rotation_param1"]
        quality_recip = struct.unpack("<f", ld.read_bytes(work_param1, 4))[0]
        angular_cols = int(round(360.0 / quality_recip)) if quality_recip else 0
        planes = {
            "f250": m4.u64(ld, work_param1 + 0xF250 * 4),
            "f252": m4.u64(ld, work_param1 + 0xF252 * 4),
            "e0e": m4.u64(ld, work_param1 + 0xE * 4),
        }
        watches = {}
        for plane, base in planes.items():
            for row, col in WATCH_CELLS:
                watches[(cell_addr(base, angular_cols, row, col), cell_addr(base, angular_cols, row, col) + 16)] = {
                    "plane": plane,
                    "row": row,
                    "col": col,
                }
        captured["watches"] = watches

        def on_write(uc, access, addr, size, value, user_data):
            for (lo, hi), meta in watches.items():
                if lo <= addr < hi:
                    rip = uc.reg_read(UC_X86_REG_RIP)
                    # Read the full cell after the write has retired enough for
                    # Unicorn's callback ordering. If this is before-write on a
                    # given backend, the next event at the same cell still gives
                    # us the post-state; final values are dumped separately.
                    cell = read4f(ld, lo)
                    captured["events"].append(
                        {
                            "rip": f"0x{rip:x}",
                            "addr": f"0x{addr:x}",
                            "size": size,
                            "value": f"0x{value:x}",
                            "plane": meta["plane"],
                            "row": meta["row"],
                            "col": meta["col"],
                            "cell": cell,
                        }
                    )
                    break

        for lo, hi in watches:
            ld.uc.hook_add(UC_HOOK_MEM_WRITE, on_write, begin=lo, end=hi - 1)

    loader.add_code_hook(m4.FUN_180004640, capture_rotation)

    t0 = time.time()
    loader.call_function(m4.FUN_180008690, int_args=[0, 0, 0, param_ctx, render_ctx], max_instructions=5_000_000)
    param_ctx_dump = m4.read_param_ctx(loader, param_ctx)
    loader.call_function(
        m4.FUN_180007520,
        int_args=[render_ctx, 0, input_world, output_world, param_ctx],
        max_instructions=1_500_000_000,
    )
    elapsed = time.time() - t0

    work_param1 = captured["rotation_param1"]
    quality_recip = struct.unpack("<f", loader.read_bytes(work_param1, 4))[0]
    angular_cols = int(round(360.0 / quality_recip)) if quality_recip else 0
    planes = {
        "f250": m4.u64(loader, work_param1 + 0xF250 * 4),
        "f252": m4.u64(loader, work_param1 + 0xF252 * 4),
        "e0e": m4.u64(loader, work_param1 + 0xE * 4),
    }
    final_cells = {}
    for plane, base in planes.items():
        final_cells[plane] = {}
        for row, col in WATCH_CELLS:
            final_cells[plane][f"row{row}_col{col}"] = read4f(loader, cell_addr(base, angular_cols, row, col))

    interesting_events = [
        event for event in captured["events"]
        if event["plane"] in {"f250", "e0e"}
    ]
    report = {
        "kind": "olmradialblur_m5_case0010_cell_writes",
        "elapsed_seconds": elapsed,
        "reader_provenance_calls": len(provenance),
        "param_ctx": param_ctx_dump,
        "rotation_param1": f"0x{work_param1:x}",
        "rotation_param2": f"0x{captured['rotation_param2']:x}",
        "quality_recip": quality_recip,
        "angular_cols": angular_cols,
        "planes": {name: f"0x{addr:x}" for name, addr in planes.items()},
        "watch_cells": WATCH_CELLS,
        "event_count": len(captured["events"]),
        "events_first_200": interesting_events[:200],
        "events_last_80": interesting_events[-80:],
        "final_cells": final_cells,
    }

    out_json = Path(__file__).parent / "M5_CELL_WRITES.json"
    out_md = Path(__file__).parent / "M5_CELL_WRITES.md"
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# M5 case_0010 cell write trace",
        "",
        f"- elapsed: `{elapsed:.2f}s`",
        f"- angular_cols: `{angular_cols}`",
        f"- events captured: `{len(captured['events'])}`",
        "",
        "## Final Cells",
        "",
    ]
    for plane, cells in final_cells.items():
        lines.append(f"### {plane}")
        for key, values in cells.items():
            lines.append(f"- `{key}`: `{tuple(round(v, 9) for v in values)}`")
        lines.append("")
    lines.extend(["## Last Events", ""])
    for event in interesting_events[-40:]:
        rounded = tuple(round(v, 9) for v in event["cell"])
        lines.append(
            f"- rip `{event['rip']}` {event['plane']} row{event['row']} col{event['col']} "
            f"addr `{event['addr']}` size `{event['size']}` value `{event['value']}` cell `{rounded}`"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_md.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
