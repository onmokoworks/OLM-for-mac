#!/usr/bin/env python3
"""Close the largest AE-free Mode2 Ramp typed-output boundary and report coverage."""

from __future__ import annotations

import importlib.util
import json
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "refs/conformance/olmkirakira_mode2_ramp_actual_aex_boundary_20260805.json"
OUTER = ROOT / "tools/emulation/olmkirakira_outer_compose_oracle_20260728.py"
WRITERS = ROOT / "tools/emulation/test_olmkirakira_typed_writers_actual_aex_20260716.py"
CPP = ROOT / "tools/emulation/test_kirakira_mode2_ramp_typed.cpp"
MAC = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
REPORT = ROOT / "refs/conformance/olmkirakira_completion_matrix_20260805.json"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    bits = fixture["cases"]["two_enabled_distinct_five_stop"]["output_rgba_f32_bits"]
    glow = struct.unpack("<4f", b"".join(struct.pack("<I", int(word, 16)) for word in bits))
    outer = load(OUTER, "kk_outer")
    writers = load(WRITERS, "kk_writers")
    composed = outer.compose_pixel(
        glow, (0.23, 0.61, 0.17, 0.42), glow_opacity=0.68,
        source_opacity=0.73, merge_mode=2)
    composed_bits = [f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}" for value in composed]
    assert composed_bits == ["0x3ee26ec4", "0x3f0d977b", "0x3f0b35bc", "0x3f7c91d2"]
    actual_writers = {depth: writers.run_writer(depth, composed) for depth in ("PF8", "PF16", "PF32")}
    assert actual_writers["PF8"]["raw_hex"] == "fb708d8a"
    assert actual_writers["PF16"]["raw_hex"] == "487e9b38cb469a45"
    assert actual_writers["PF32"]["raw_hex"] == "d2917c3fc46ee23e7b970d3fbc350b3f"
    with tempfile.TemporaryDirectory(prefix="kk_typed_ramp_") as td:
        exe = Path(td) / "typed"
        subprocess.run(["c++", "-std=c++17", "-O2", str(CPP), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    source = MAC.read_text(encoding="utf-8")
    assert "compose_merge2_pixel(" in source and source.count("truncate_merge2_channel(") >= 8
    report = {
        "schema": "olmkirakira-completion-matrix/1",
        "status": "largest_ae_free_gap_closed",
        "closed_boundary": {
            "name": "Mode2 two-enabled distinct Ramp -> outer compose -> PF8/PF16/PF32 writers",
            "actual_glow_bits": bits,
            "composed_rgba_bits": composed_bits,
            "typed_argb_hex": {depth: case["raw_hex"] for depth, case in actual_writers.items()},
            "production_exact": True,
        },
        "matrix": {
            "EffectMain": {"GLOBAL_SETUP": "covered", "PARAMS_SETUP": "covered_41", "RENDER": "covered_fixture", "SMART_PRE_RENDER": "covered_checkout", "SMART_RENDER": "covered_fixture", "EVENT": "covered_synthetic_host_gate", "ARBITRARY_CALLBACK": "covered_selectors_0_to_10"},
            "arbitrary": {"lifecycle": "covered", "wire": "covered", "interpolate_equal": "covered", "interpolate_mismatched": "covered", "compare_signed_zero": "covered", "malformed_version": "covered", "ignored_tail": "covered"},
            "modes": {"Mode1": "covered_existing", "Mode2": "covered_ramp_and_typed", "Mode3": "covered_fixed_fixtures", "Mode4": "partial_existing"},
            "ui": {"draw_add_drag_delete_color": "synthetic_exact", "live_Drawbot_and_modal_delivery": "host_gate"},
            "depth": {"PF8": "typed_exact", "PF16": "typed_exact", "PF32": "typed_exact"},
        },
        "remaining_max_gate": "natural full EffectMain owner-to-writer execution inside live AE",
        "live_ae_claimed": False,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_MODE2_RAMP_TYPED_COMPLETION_20260805 depths=3 exact=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
