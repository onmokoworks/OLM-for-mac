#!/usr/bin/env python3
"""Compare the bounded production ramp seam with four actual-AEX cases."""

from __future__ import annotations

import json
import hashlib
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "refs/conformance/olmkirakira_mode2_ramp_actual_aex_boundary_20260805.json"
CPP = ROOT / "tools/emulation/test_kirakira_merge2.cpp"
MAC = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
ENTRY_PROBE = ROOT / "tools/emulation/test_olmkirakira_ramp_arbitrary_entrypoint_20260805.py"
ENTRY_REPORT = ROOT / "refs/conformance/olmkirakira_ramp_arbitrary_entrypoint_20260805.json"


def main() -> int:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["status"] == "captured_exact"
    names = ["below_first_stop", "between_stops", "above_last_stop", "same_ray_ramp_off", "four_stop_nonuniform", "five_stop_mixed_toggle", "two_enabled_distinct_five_stop"]
    expected = [fixture["cases"][name]["output_rgba_f32_bits"] for name in names]

    with tempfile.TemporaryDirectory(prefix="olmkirakira_merge2_ramp_seam_") as td:
        executable = Path(td) / "merge2"
        subprocess.run(["c++", "-std=c++17", "-O2", str(CPP), "-o", str(executable)], check=True)
        lines = subprocess.check_output([str(executable)], text=True).splitlines()
    actual = [[f"0x{word}" for word in line.split()[1:]] for line in lines]
    assert actual == expected

    four = fixture["four_stop_fixture"]
    env = os.environ.copy()
    env["OLM_KK_RAMP_CUSTOM_STOPS_JSON"] = json.dumps(four["stops"])
    env["OLM_KK_RAMP_MODE2_RAY"] = str(four["ray"])
    subprocess.run(["python3", str(ENTRY_PROBE)], cwd=ROOT, env=env, check=True,
                   stdout=subprocess.DEVNULL)
    serialized = json.loads(ENTRY_REPORT.read_text(encoding="utf-8"))
    canonical_flat = bytes.fromhex(four["canonical_flat_hex"])
    actual_flat = bytes.fromhex(serialized["flat_hex"])
    meaningful_end = 1 + 4 + 4 * 20
    assert actual_flat[:meaningful_end] == canonical_flat[:meaningful_end]
    assert serialized["canonical_flat_sha256"] == hashlib.sha256(canonical_flat).hexdigest()
    assert serialized["mode2_output_bits"]["source"] == expected[names.index("four_stop_nonuniform")]
    assert serialized["wire_fields"]["count"]["value"] == 4

    five = fixture["five_stop_mixed_toggle_fixture"]
    env["OLM_KK_RAMP_CUSTOM_STOPS_JSON"] = json.dumps(five["stops"])
    env["OLM_KK_RAMP_MODE2_RAY"] = str(five["rays"][0])
    subprocess.run(["python3", str(ENTRY_PROBE)], cwd=ROOT, env=env, check=True,
                   stdout=subprocess.DEVNULL)
    serialized_five = json.loads(ENTRY_REPORT.read_text(encoding="utf-8"))
    canonical_five = bytes.fromhex(five["canonical_flat_hex"])
    actual_five = bytes.fromhex(serialized_five["flat_hex"])
    five_meaningful_end = 1 + 4 + 5 * 20
    assert actual_five[:five_meaningful_end] == canonical_five[:five_meaningful_end]
    assert serialized_five["canonical_flat_sha256"] == five["canonical_flat_sha256"]
    assert serialized_five["wire_fields"]["count"]["value"] == 5

    two = fixture["two_enabled_distinct_five_stop_fixture"]
    for key, flat_key in (("stops_a", "canonical_flat_a_hex"), ("stops_b", "canonical_flat_b_hex")):
        env["OLM_KK_RAMP_CUSTOM_STOPS_JSON"] = json.dumps(two[key])
        subprocess.run(["python3", str(ENTRY_PROBE)], cwd=ROOT, env=env, check=True,
                       stdout=subprocess.DEVNULL)
        serialized_group = json.loads(ENTRY_REPORT.read_text(encoding="utf-8"))
        canonical_group = bytes.fromhex(two[flat_key])
        actual_group = bytes.fromhex(serialized_group["flat_hex"])
        assert actual_group[:105] == canonical_group[:105]
        assert serialized_group["canonical_flat_sha256"] == hashlib.sha256(canonical_group).hexdigest()
        assert serialized_group["wire_fields"]["count"]["value"] == 5
    # Keep the default arbitrary-entrypoint report canonical for downstream lanes.
    subprocess.run(["python3", str(ENTRY_PROBE)], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)

    mac = MAC.read_text(encoding="utf-8")
    assert "add_colored_merge2(" in mac
    assert "use_ramp ? &ramp : nullptr" in mac
    assert "info.vertical_use_ramp, info.vertical_ramp" in mac
    assert "info.diagonal2_use_ramp, info.diagonal2_ramp" in mac
    print("PASS_OLMKIRAKIRA_MODE2_RAMP_PRODUCTION_SEAM_20260805 cases=7 words=28 two_enabled_serialized=exact max_ulp=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
