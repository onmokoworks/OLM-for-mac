#!/usr/bin/env python3
"""Smoke the deterministic, same-run fail-closed Mode2 writeback package."""
from __future__ import annotations
import json, subprocess, sys, tempfile, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.windows_witness.runtime import validate_trace
GEN = ROOT / "scripts/package_olmkirakira_mode2_compose_writeback_20260716.py"
SPEC = ROOT / "refs/windows_witness_specs/olmkirakira_mode2_compose_writeback_20260716/witness-spec.json"
HASH = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
CASE = "kk_vertical_len50_brightness1_strength100"
ID = {"run_id":"kk-mode2-fixture","ae_pid":20260716,"module_base":"0x7ff600000000"}

def trace() -> str:
    c = f"run_id={ID['run_id']} ae_pid={ID['ae_pid']} module_base={ID['module_base']} aex_sha256={HASH} project_bpc=32 renderer=Software case_id={CASE} witness_id=olmkirakira-mode2-compose-writeback-v1"
    return "\n".join([
        f"KK_MODE2_RETURN {c} stage=mode2_return target_rva=14ffd0 dispatch_slot=+0x10 threshold_f64=0.001 output_ptr=0x1000 pre_clamp_rgba_f32=0.25,0.5,0.75,0.9 post_clamp_rgba_f32=0.25,0.5,0.75,0.9 clamp_count=4",
        f"KK_HOST_COMPOSE {c} stage=host_compose input_ptr=0x1000 output_ptr=0x2000 compose_formula=src_plus_glow source_rgba_f32=0.25,0.5,0.75,0.9 glow_rgba_f32=0.1,0.1,0.1,0.0 typed_prewriteback_rgba_f32=0.35,0.6,0.85,0.9",
        f"KK_PF16_ENTRY {c} stage=pf16_entry entry_rva=230bd0 input_scale=65535 destination_addr=0x3000",
        f"KK_SELECTED_WRITER {c} stage=selected_writer writer_family=PF16 entry_rva=230bd0 input_scale=65535 conversion=clamp_round_f32_to_u16 destination_addr=0x3000 typed_prewriteback_rgba_f32=0.35,0.6,0.85,0.9",
        f"KK_STORE_AFTER {c} stage=store_after writer_family=PF16 entry_rva=230bd0 destination_addr=0x3000 after_store_words=5999,9999,d999,e666 store_width=16",
    ]) + "\n"

def main() -> int:
    spec = json.loads(SPEC.read_text())
    assert spec["project"] == {"bits_per_channel": 32, "renderer": "Software"}
    assert spec["cases"][0]["id"] == CASE
    template = (SPEC.parent / "mode2_compose_writeback.cdb.in").read_text()
    for term in ("KK_MODE2_RETURN", "KK_HOST_COMPOSE", "KK_SELECTED_WRITER", "KK_STORE_AFTER", "PF8", "PF16", "PF32", "threshold_f64", "post_clamp_rgba_f32"):
        assert term in template
    accepted = validate_trace(spec, trace(), ID)
    assert accepted["status"] == "answered" and len(accepted["events"]) == 5
    for missing in ("KK_MODE2_RETURN", "KK_HOST_COMPOSE", "KK_SELECTED_WRITER", "KK_STORE_AFTER"):
        rejected = validate_trace(spec, trace().replace(missing + " ", missing + "_MISSING "), ID)
        assert rejected["status"] == "exact_bind_failure", missing
    with tempfile.TemporaryDirectory(prefix="kk_mode2_wb_smoke_") as d:
        out = Path(d) / "package"
        archive = Path(d) / "package.zip"
        r = subprocess.run([sys.executable, str(GEN), "--output-dir", str(out), "--zip", str(archive)], cwd=ROOT, check=True, text=True, capture_output=True)
        assert json.loads(r.stdout)["status"] == "ok"
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            names = z.namelist()
            assert names == sorted(names)
            contract = json.loads(z.read("witness-contract.json"))
            package_manifest = json.loads(z.read("package-manifest.json"))
            assert contract["failure_status"] == "exact_bind_failure"
            assert package_manifest["queue"]["profile"] == "olmkirakira-mode2-compose-writeback"
            assert package_manifest["queue"]["stop_condition"]
    print("[OK] Mode2 compose/writeback package is deterministic and fail-closed")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
