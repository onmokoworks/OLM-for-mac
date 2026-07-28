#!/usr/bin/env python3
"""Smoke-test package shape and fail-closed writer/PF identity validation."""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/package_windows_witness_olmdirectionalblur_writer_entry_20260716.py"
HASH = "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e"

def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dblur_writer_pkg_") as tmp:
        out = Path(tmp) / "writer.zip"
        subprocess.run(["python3", str(SCRIPT), "--output-dir", str(Path(tmp) / "pkg"), "--zip", str(out)], cwd=ROOT, check=True)
        with zipfile.ZipFile(out) as zf:
            names = set(zf.namelist())
            contract = json.loads(zf.read("witness-contract.json"))
            package_manifest = json.loads(zf.read("package-manifest.json"))
            probe = zf.read("cdb/000_db_angle0_alpha_fade_hard_edges.cdb.in").decode()
            renderer = zf.read("scripts/renderer.jsx").decode()
            readme = zf.read("README.md").decode()
        assert contract["plugin"]["aex_sha256"] == HASH
        assert contract["project"]["renderer"] == "Software"
        assert contract["cases"][0]["id"] == "db_angle0_alpha_fade_hard_edges"
        assert contract["cases"][0]["addresses"]["effect_dispatch"] == "0x83f0"
        assert contract["cases"][0]["addresses"]["output_iterate_call"] == "0x5665"
        assert contract["cases"][0]["addresses"]["writer_entry"] == "0x6b30"
        assert contract["cases"][0]["addresses"]["pf_store"] == "0x6bc7"
        assert package_manifest["queue"]["profile"] == "olmdirectionalblur-front-alpha-writer-entry"
        assert package_manifest["queue"]["stop_condition"]
        prefixes = {event["prefix"] for event in contract["validation"]["events"]}
        assert {"DBR_EFFECT_DISPATCH", "DBR_OUTPUT_ITERATE", "DBR_TARGET_ARM", "DBR_TARGET_STORE", "DBR_PF_OUTPUT", "DBR_EXPORT"} <= prefixes
        events = {event["name"]: event for event in contract["validation"]["events"]}
        assert events["target_arm"]["cardinality"] == {"scope": "per_case", "min": 1, "max": 1}
        assert events["target_store"]["cardinality"] == {"scope": "per_case", "min": 1, "max": 1}
        for token in ("rgba_f32_bits", "pf_argb_bytes", "same_run_key", "typed_f32", "typed_argb8"):
            assert token in probe or token in json.dumps(contract)
        assert "(@r8d*0n7680)-(@edx*4)" in probe
        assert "@$t6+(0n169*0n7680)+(0n494*4)" in probe
        assert "dwo(@rcx+0x8098)+0n169" in probe
        assert "dwo(@rcx+0x809c)+0n494" in probe
        assert "poi(@rcx+0x8090)" in probe
        assert "poi(@rsp+0x28)" in probe
        assert "@ecx==0x18" in probe
        assert "{{ADDRESS:effect_dispatch}}" in probe
        assert "{{ADDRESS:output_iterate_call}}" in probe
        assert "DBR_WRITER_CENSUS" not in probe
        assert "DBR_TARGET_CLASS" not in probe
        assert "DBR_TARGET_ARM" in probe
        assert "DBR_TARGET_STORE" in probe
        assert "ba w1 @$t7" in probe
        assert "bc @$bpnum" in probe
        assert "DBR_WRITER_ENTRY_COMPLETE" in probe
        assert "&&" not in probe
        assert 'getenv("WINDOWS_WITNESS_RUN_ID")' in renderer
        assert "witness_input_" in renderer
        assert "run_unique_copy" in renderer
        assert "wrapper_sha256_prevalidated" in renderer
        assert "source=absolute_override" in renderer
        assert "run-unique input copy validation failed" in renderer
        assert "destination_parent_exists=" in renderer
        assert "uniqueInput.remove" not in renderer
        assert "INPUT_COPY_PREFLIGHT.json" in contract["return_bundle"]["include_logs"]
        assert "exact_bind_failure" in readme
        assert "return/writer_pf_argb8.bin" in json.dumps(contract)
        missing = dict(run_id="run-a", ae_pid="1", module_base="0x180000000", aex_sha256=HASH, project_bpc="8", renderer="Software", case_id="db_angle0_alpha_fade_hard_edges", witness_id="olmdirectionalblur-writer-entry-v1")
        trace = "DBR_TARGET_ARM " + " ".join(f"{k}={v}" for k, v in {**missing, "stage":"target_arm", "hook_rva":"6b30", "occurrence":"1", "params":"0x1", "source_base":"0x2", "row_shift":"563", "col_shift":"143", "stride":"2206", "first_local_x":"0", "first_local_y":"0", "first_pf_output":"0x3", "output_base":"0x3", "target_output":"0x4", "target_source":"0x5", "output_rowbytes":"7680", "x":"494", "y":"169", "same_run_key":"writer-pf-494-169"}.items()) + "\n"
        identity = Path(tmp) / "identity.json"
        identity.write_text(json.dumps({"run_id":"run-a", "ae_pid":1, "module_base":"0x180000000"}))
        trace_path = Path(tmp) / "trace.txt"
        trace_path.write_text(trace)
        result = subprocess.run(["python3", str(Path(ROOT / "tools/windows_witness/runtime.py")), "validate", "--contract", str(Path(tmp) / "pkg/witness-contract.json"), "--trace", str(trace_path), "--identity", str(identity), "--output", str(Path(tmp) / "result.json")], cwd=ROOT)
        assert result.returncode != 0
        assert json.loads((Path(tmp) / "result.json").read_text())["status"] == "exact_bind_failure"
    print("[OK] DirectionalBlur writer-entry package smoke passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
