#!/usr/bin/env python3
"""Actual-AEX fixture export and AE-free production replay for OLMBlur branches."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from test_olmblur_worker16_nonlegacy import run_case as run_nonlegacy, source_bytes as nonlegacy_source  # noqa: E402
from test_olmblur_worker16_legacy import run_case as run_legacy, source_bytes as legacy_source  # noqa: E402

FIXTURES = ROOT / "tools/emulation/fixtures/olmblur_current_exact_branches_20260805"
REPLAY = ROOT / "tools/emulation/replay_olmblur_current_exact_branches_20260805.cpp"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
MAC_SHA256 = "c6a9e54b1760fc2c916f4551367666b58c100520b2c6644ebd809d60e3d9d83e"
EVIDENCE = {
    4: (ROOT / "refs/conformance/olmblur_32bpc_case0004_ae_exact_20260727.json",
        "664ce93195accc624d96ae81d25d138d86a799592d95453b5053c5be181ae284"),
    5: (ROOT / "refs/conformance/olmblur_32bpc_case0005_ae_exact_20260727.json",
        "cdb233198f44364c913fa1efbaf2b238918c087578b499fd2d89bceddbcf794b"),
    7: (ROOT / "refs/conformance/olmblur_32bpc_case0007_ae_exact_20260727.json",
        "04759826e849250c33b0bbcca66027a0755b32bb92115eaa81d614fd3f1760ec"),
}
OLD_BINARY_EVIDENCE = {
    2: (ROOT / "refs/conformance/olmblur_32bpc_case0002_ae_exact_20260727.json",
        "fbafcfcd23490ac98c1ca188488c7bd73c63fe28a202322bc10589e0ff41ca15"),
    3: (ROOT / "refs/conformance/olmblur_32bpc_case0003_ae_exact_20260727.json",
        "47ce1c9cf1d077008e6cdb1a3c3ecd13ebf7f5a5bf4d2b23b478064c3333e19e"),
}
CASES = [
    ({"id": "case0001_pending_nonlegacy_repeat1_large_radius", "width": 24, "height": 24,
      "blur_amount": 129.4, "smoothness": 100.0, "repeat": 1, "bias_direction": 1}, False),
    ({"id": "case0002_different_binary_nonlegacy_repeat2_reverse", "width": 24, "height": 24,
      "blur_amount": 129.4, "smoothness": 100.0, "repeat": 2, "bias_direction": 2}, False),
    ({"id": "case0003_different_binary_legacy_repeat10_large_radius", "width": 12, "height": 12,
      "blur_amount": 248.6, "smoothness": 100.0, "repeat": 10, "bias_direction": 1,
      "max_instructions": 30_000_000}, True),
    ({"id": "case0004_nonlegacy_repeat4_large_radius", "width": 24, "height": 24,
      "blur_amount": 125.6, "smoothness": 100.0, "repeat": 4, "bias_direction": 1}, False),
    ({"id": "case0005_nonlegacy_repeat2_small_radius", "width": 16, "height": 16,
      "blur_amount": 5.0, "smoothness": 100.0, "repeat": 2, "bias_direction": 1}, False),
    ({"id": "case0007_legacy_repeat1", "width": 16, "height": 16,
      "blur_amount": 5.0, "smoothness": 100.0, "repeat": 1, "bias_direction": 1}, True),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export() -> None:
    rows = []
    for case, legacy in CASES:
        source = legacy_source(case["width"], case["height"]) if legacy else nonlegacy_source(case["width"], case["height"])
        output, meta = (run_legacy(case) if legacy else run_nonlegacy(case))
        directory = FIXTURES / case["id"]
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "source_argb16.bin").write_bytes(source)
        (directory / "expected_argb16.bin").write_bytes(output)
        rows.append({**case, "legacy": legacy, "aex_entry": "0x180005f20" if legacy else "0x180002280",
                     "source_sha256": hashlib.sha256(source).hexdigest(),
                     "expected_sha256": hashlib.sha256(output).hexdigest(),
                     "instructions": meta["instructions"],
                     "callback_count": len(meta["callbacks"])})
    manifest = {"schema": "olm.aex.cpu-fixture/1", "plugin": "OLMBlur",
                "binary_sha256": AEX_SHA256, "pixel_layout": "little-endian A,R,G,B",
                "cases": rows}
    (FIXTURES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def verify() -> None:
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["binary_sha256"] == AEX_SHA256
    assert [row["id"] for row in manifest["cases"]] == [case["id"] for case, _ in CASES]
    for row in manifest["cases"]:
        directory = FIXTURES / row["id"]
        assert sha256(directory / "source_argb16.bin") == row["source_sha256"]
        assert sha256(directory / "expected_argb16.bin") == row["expected_sha256"]
    # case0001 is deliberately an AE-free typed numerical claim only.  Its
    # retained AE-exact record used a different Mac binary and must not be
    # promoted to the current c6a9... binary by this fixture.
    pending_request = json.loads((
        ROOT / "refs/mac_validation_requests/olmblur_32bpc_mac_validation_repeat1_20260718.json"
    ).read_text(encoding="utf-8"))
    pending_params = pending_request["case"]["effect"]["params"][:5]
    assert [(row["match_name"], row["property_index"], row["value"]) for row in pending_params] == [
        ("OLM OLM Blur-0005", 1, 129.4), ("OLM OLM Blur-0006", 2, 100),
        ("OLM OLM Blur-0003", 3, 1), ("OLM OLM Blur-0004", 4, 1),
        ("OLM OLM Blur-0007", 5, 0),
    ]
    old_case1 = json.loads((
        ROOT / "refs/conformance/olmblur_32bpc_case0001_ae_exact_20260727.json"
    ).read_text(encoding="utf-8"))
    assert old_case1["mac"]["plugin"]["sha256"] != MAC_SHA256
    old_expected_params = {
        2: {"Blur Amount": 129.4, "Blur Amount readback": 129.399993896484,
            "Blur Smoothness": 100, "Number of Repeat": 2, "Bias Direction": 2, "Legacy": 0},
        3: {"Blur Amount": 248.6, "Blur Amount readback": 248.600006103516,
            "Blur Smoothness": 100, "Number of Repeat": 10, "Bias Direction": 1, "Legacy": 1},
    }
    for number, (path, digest) in OLD_BINARY_EVIDENCE.items():
        assert sha256(path) == digest
        row = json.loads(path.read_text(encoding="utf-8"))
        assert row["contract"]["params"] == old_expected_params[number]
        old_hash = row["mac"].get("loaded_plugin_proof", {}).get("module_sha256") or row["mac"]["plugin"]["sha256"]
        assert old_hash != MAC_SHA256
        assert row["windows"]["loaded_plugin_proof"]["aex_sha256"] == AEX_SHA256
    expected_params = {
        4: {"Blur Amount": 125.6, "Blur Amount readback": 125.599998474121,
            "Blur Smoothness": 100, "Number of Repeat": 4, "Bias Direction": 1, "Legacy": 0},
        5: {"Blur Amount": 5, "Blur Amount readback": 5,
            "Blur Smoothness": 100, "Number of Repeat": 2, "Bias Direction": 1, "Legacy": 0},
        7: {"Blur Amount": 5, "Blur Amount readback": 5, "Blur Smoothness": 100,
            "Number of Repeat": 1, "Bias Direction": 1, "Legacy": 1},
    }
    for number, (path, digest) in EVIDENCE.items():
        assert sha256(path) == digest
        row = json.loads(path.read_text(encoding="utf-8"))
        assert row["contract"]["params"] == expected_params[number]
        assert row["mac"]["loaded_plugin_proof"]["module_sha256"] == MAC_SHA256
        assert row["windows"]["loaded_plugin_proof"]["aex_sha256"] == AEX_SHA256
        assert all(row["comparison"][branch]["mismatched_values"] == 0 for branch in ("no_effect_control", "effect_on"))
    with tempfile.TemporaryDirectory(prefix="olmblur_current_branches_") as temp:
        executable = Path(temp) / "replay"
        build = subprocess.run([
            "c++", "-std=c++17", "-O2", "-ffp-contract=off", str(REPLAY),
            str(ROOT / "core/olmblur_helper.cpp"),
            str(ROOT / "core/olmblur_worker16_nonlegacy.cpp"),
            str(ROOT / "core/olmblur_worker16_legacy.cpp"),
            str(ROOT / "core/olmblur_fullworker_helper.cpp"), "-o", str(executable),
        ], cwd=ROOT, text=True, capture_output=True, check=False)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(executable), str(FIXTURES)], text=True, capture_output=True, check=False)
        assert run.returncode == 0, run.stderr + run.stdout
        assert "PASS case0001_pending_nonlegacy_repeat1_large_radius" in run.stdout
        assert "PASS case0002_different_binary_nonlegacy_repeat2_reverse" in run.stdout
        assert "PASS case0003_different_binary_legacy_repeat10_large_radius" in run.stdout
        assert "PASS case0004_nonlegacy_repeat4_large_radius" in run.stdout
        assert "PASS case0005_nonlegacy_repeat2_small_radius" in run.stdout
        assert "PASS case0007_legacy_repeat1" in run.stdout
        print(run.stdout, end="")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    export() if args.export else verify()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
