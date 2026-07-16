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
            readme = zf.read("README.md").decode()
        assert contract["plugin"]["aex_sha256"] == HASH
        assert contract["project"]["renderer"] == "Software"
        assert contract["cases"][0]["id"] == "db_angle0_alpha_fade_hard_edges"
        assert package_manifest["queue"]["profile"] == "olmdirectionalblur-front-alpha-writer-entry"
        assert package_manifest["queue"]["stop_condition"]
        prefixes = {event["prefix"] for event in contract["validation"]["events"]}
        assert {"DBR_WRITER_ENTRY", "DBR_PF_STORE", "DBR_PF_OUTPUT", "DBR_EXPORT"} <= prefixes
        for token in ("rgba_f32_bits", "pf_argb_bytes", "same_run_key", "typed_f32", "typed_argb8"):
            assert token in probe or token in json.dumps(contract)
        assert "exact_bind_failure" in readme
        assert "return/writer_pf_argb8.bin" in json.dumps(contract)
        missing = dict(run_id="run-a", ae_pid="1", module_base="0x180000000", aex_sha256=HASH, project_bpc="8", renderer="Software", case_id="db_angle0_alpha_fade_hard_edges", witness_id="olmdirectionalblur-writer-entry-v1")
        trace = "DBR_WRITER_ENTRY " + " ".join(f"{k}={v}" for k, v in {**missing, "stage":"writer_entry", "hook_rva":"566a", "x":"494", "y":"169", "writer_addr":"0x1", "pf_output_addr":"0x2", "rgba_f32_bits":"0x00000000,0x00000000,0x00000000,0x3f800000", "typed_f32":"1", "same_run_key":"writer-pf-494-169"}.items()) + "\n"
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
