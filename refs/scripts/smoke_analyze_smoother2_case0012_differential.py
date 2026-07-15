#!/usr/bin/env python3
"""Smoke-test the local case_0012 producer/config/writer comparator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(root: Path, input_path: Path, output: Path, reference: Path | None = None) -> dict:
    command = [sys.executable, "scripts/analyze_smoother2_case0012_differential.py", "--input", str(input_path), "--output-json", str(output)]
    if reference:
        command += ["--local-reference", str(reference)]
    proc = subprocess.run(command, cwd=root, text=True, capture_output=True)
    if proc.returncode not in (0, 2):
        raise AssertionError(proc.stdout + proc.stderr)
    return json.loads(output.read_text(encoding="utf-8"))


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    fixture = root / "refs/windows_witness_specs/olmsmoother2_case0012_current_aex_20260713/fixtures"
    with tempfile.TemporaryDirectory(prefix="smoother2_case0012_diff_") as raw:
        temp = Path(raw)
        complete = run(root, fixture / "complete_cdb_trace.txt", temp / "complete.json")
        assert complete["verdict"] == "READY_TYPED_FIELDS_ONLY"
        assert complete["FACT"]["completeness"] == {"events": True, "producer": True, "config": True, "writer": True}
        assert complete["FACT"]["typed_snapshot"]["producer"]["e170_c"] == 2
        assert complete["FACT"]["typed_snapshot"]["config"]["c280"]["scale_fixed"] == [65536, 65536]
        assert complete["FACT"]["typed_snapshot"]["config"]["cce0"]["mode_byte"] == 3

        # Exercise the returned-JSON shape separately from the CDB fixture path.
        lines = (fixture / "complete_cdb_trace.txt").read_text(encoding="ascii").splitlines()
        fields = {}
        for line in lines:
            tokens = line.split()
            if tokens and tokens[0] == "S2_BIND":
                fields = {token.split("=", 1)[0]: token.split("=", 1)[1] for token in tokens[1:] if "=" in token}
                break
        returned = {
            "status": "answered",
            "run": {"run_id": fields["run_id"], "ae_pid": int(fields["ae_pid"]), "module_base": fields["module_base"], "aex_sha256": fields["aex_sha256"], "project_bpc": int(fields["project_bpc"]), "renderer": fields["renderer"], "case_id": fields["case_id"], "witness_id": fields["witness_id"]},
            "observations": {
                "bind": {},
                "e170": {"c": 2, "center_class_bytes": "140,141,142,143", "prev_class_bytes": "138,139,140,141", "left_class_bytes": "142,143,144,145"},
                "f270": {"append": 1, "source_xy": "91,841", "weight": 0.625},
                "e3a0": {"append": 1, "source_xy": "91,843", "weight": 0.375},
                "cce0": {"pointer_identity": 1, "config_pointer_source": "poi(rsp+0x28)", "config_raw_bytes": "00,00,80,3f,04,00,03", "mode_byte": 3},
                "c280": {"pointer_identity": 1, "config_pointer_arithmetic": "rax+0x20_scale_fixed_words", "config_raw_bytes": "00,00,01,00,00,00,01,00", "scale_fixed": "65536,65536"},
                "final_writer": {"rgba_u8": "0,0,0,0", "rgba_float": "0,0,0,0"},
            },
        }
        returned_path = temp / "returned.json"
        returned_path.write_text(json.dumps(returned), encoding="utf-8")
        returned_report = run(root, returned_path, temp / "returned-report.json")
        assert returned_report["source_kind"] == "return"
        assert returned_report["verdict"] == "READY_TYPED_FIELDS_ONLY"

        missing = run(root, fixture / "missing_cce0_cdb_trace.txt", temp / "missing.json")
        assert missing["verdict"] == "BLOCKED_INCOMPLETE_RETURN"
        assert "missing_typed_event:S2_CCE0" in missing["blockers"]

        reference = temp / "reference.json"
        reference.write_text(json.dumps(complete), encoding="utf-8")
        matching = run(root, fixture / "complete_cdb_trace.txt", temp / "matching.json", reference)
        assert matching["verdict"] == "MATCHES_LOCAL_REFERENCE"

        changed = temp / "changed.txt"
        changed.write_text((fixture / "complete_cdb_trace.txt").read_text(encoding="ascii").replace("mode_byte=3", "mode_byte=9"), encoding="ascii")
        config_diff = run(root, changed, temp / "config-diff.json", reference)
        assert config_diff["verdict"] == "DIFF_AT_CONFIG"
        assert config_diff["INFERENCE"]["first_divergence"] == "config"
    print("[OK] Smoother2 case_0012 differential smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
