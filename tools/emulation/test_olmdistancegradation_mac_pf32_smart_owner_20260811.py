#!/usr/bin/env python3
"""Compile and execute the production Mac PF32 Smart owner adapter."""
import hashlib, json, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
HARNESS = ROOT / "tools/emulation/dg_mac_pf32_smart_owner_harness_20260811.cpp"
REPORT = ROOT / "refs/conformance/olmdistancegradation_mac_pf32_smart_owner_20260811.json"
DOC = REPORT.with_suffix(".md")

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    with tempfile.TemporaryDirectory(prefix="dg_mac_pf32_smart_") as temporary:
        executable = Path(temporary) / "harness"
        build = subprocess.run(["clang++", "-std=c++17", "-O0",
            "-I", str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"),
            str(HARNESS), str(ROOT / "core/olmdistancegradation_fieldgen.cpp"), "-o", str(executable)],
            text=True, capture_output=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(executable)], text=True, capture_output=True)
        assert run.returncode == 0, run.stderr
        assert run.stdout.strip() == "PASS_OLMDISTANCEGRADATION_MAC_PF32_SMART_OWNER"
    report = {"schema": "olmdistancegradation.mac-pf32-smart-owner/1",
        "status": "PASS_OLMDISTANCEGRADATION_MAC_PF32_SMART_OWNER",
        "production_source_sha256": sha(SOURCE), "harness_sha256": sha(HARNESS),
        "proved": ["SmartRender admits bitdepth 32", "checkout_layer_pixels and checkout_output worlds",
            "parameter checkout feeds production RenderBits", "blank output receives nonzero generated field/output",
            "complete padded PF32 buffer equals direct smart-owner RenderBits", "unsupported depth fails closed"],
        "not_proven": ["native After Effects execution", "partial-world/origin translation",
            "arbitrary Smart parameter and geometry products"]}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLMDistanceGradation Mac PF32 Smart owner\n\n"
        "Status: **PASS_OLMDISTANCEGRADATION_MAC_PF32_SMART_OWNER**.\n\n"
        "The source-included production `SmartRender` adapter admits bitdepth 32, checks out the PF32 "
        "input/output worlds and parameters, generates the field from a blank output, and matches the "
        "direct Smart-owner `RenderBits` buffer including padding. Unsupported depth remains fail-closed. "
        "Native After Effects execution and partial-world origin translation remain separate boundaries.\n")
    print(report["status"])

if __name__ == "__main__": raise SystemExit(main())
