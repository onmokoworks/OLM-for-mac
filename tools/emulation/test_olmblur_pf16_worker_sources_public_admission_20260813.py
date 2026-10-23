#!/usr/bin/env python3
"""Real-SDK closure for eight bounded PF16 source-bound public cells."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMBlur/OLMBlur.cpp"
WORKER = ROOT / "core/olmblur_worker16_nonlegacy.cpp"
LEGACY_WORKER = ROOT / "core/olmblur_worker16_legacy.cpp"
SHA_HELPER = ROOT / "core/olm_sha256_rows.h"
PROBE = ROOT / "tools/emulation/probe_olmblur_pf16_worker_sources_public_admission_20260813.cpp"
OWNER = ROOT / "refs/conformance/olmblur_pf16_worker_sources_exported_public_owner_20260813.json"
RETAINED_OWNER = ROOT / "refs/conformance/olmblur_pf16_retained_tuples_exported_public_owner_20260813.json"
LEGACY_OWNER = ROOT / "refs/conformance/olmblur_pf16_legacy_retained_exported_public_owner_20260813.json"
REPORT = ROOT / "refs/conformance/olmblur_pf16_worker_sources_public_admission_20260813.json"
DOC = ROOT / "refs/conformance/olmblur_pf16_worker_sources_public_admission_20260813.md"
EXPECTED = {
    "source": "22eb712a2485e080d811d2c064fe78bd521ee25434ece9a290a2d9b7b6e1fdd7",
    "worker": "e0cec4230006c518514e4c730fa940fb935074a48e401d8e7f586b46b7b4266e",
    "legacy_worker": "b20228bf8c987940d1dd2922eec9984ac9fbcfbb1450f46a28e44fcf857d90da",
    "sha_helper": "bfdcc9a2f4575aabab692b7b4ca1cf9ddb8188c7fbb1efdae30d197bf0f2d9e5",
    "probe": "a6306a0e613b71d1ab79bdf1c331acd2fc14537679ce9f33cd7705375cf8206a",
    "owner": "523553ad15c34677262f7d54a5418caa96bd9a4b2bcefde8fec781f8df9166a2",
    "retained_owner": "769cce9a2adb8f471b6fd14952038f540acdb0d6de97970f93b9e2194bf87541",
    "legacy_owner": "1726d259afaae558c3f9832e59d7f1b158cffc65c17a441e8668b57ab0af9c96",
}
CELLS = [
    {"id": "12x12_repeat1_nonlegacy", "geometry": [12, 12], "rowbytes": 109, "amount_f64": 3.0, "smoothness_fixed": 6553600, "repeat": 1, "bias": 1, "legacy": 0, "active_source_sha256": "df143537b2c987564fd2c0d0b4f9ad3b2332c4db8d5ccbaf8ac3ebc71b05bb8d", "active_output_sha256": "f4a8b917c50936578f0573b943e5d9baad29af87b8f17f2efec4765c74771922"},
    {"id": "12x12_repeat2_nonlegacy", "geometry": [12, 12], "rowbytes": 109, "amount_f64": 3.0, "smoothness_fixed": 6553600, "repeat": 2, "bias": 1, "legacy": 0, "active_source_sha256": "df143537b2c987564fd2c0d0b4f9ad3b2332c4db8d5ccbaf8ac3ebc71b05bb8d", "active_output_sha256": "28d648118306c3ed9bedbcd7e99c7af8f8bc26813b701b366c56b966f3a3e846"},
    {"id": "18x18_repeat1_nonlegacy", "geometry": [18, 18], "rowbytes": 157, "amount_f64": 11.0, "smoothness_fixed": 6553600, "repeat": 1, "bias": 1, "legacy": 0, "active_source_sha256": "bc3bfbf7c3d5a908690b71819c9dd83e4bddb9b6f09a417ff06ec6cc3d3943ae", "active_output_sha256": "fbf43a4c4832c1c2a8e30187361ddaec6bf95c36a793f71573d8b1db4652a46e"},
    {"id": "18x18_repeat3_nonlegacy", "geometry": [18, 18], "rowbytes": 157, "amount_f64": 11.0, "smoothness_fixed": 6553600, "repeat": 3, "bias": 2, "legacy": 0, "active_source_sha256": "bc3bfbf7c3d5a908690b71819c9dd83e4bddb9b6f09a417ff06ec6cc3d3943ae", "active_output_sha256": "64355b2ce493e3d318de8fa09f45234b98236029347b62e9d09e4ef8cb98a4bc"},
    {"id": "12x12_repeat2_legacy", "geometry": [12, 12], "rowbytes": 109, "amount_f64": 3.0, "smoothness_fixed": 6553600, "repeat": 2, "bias": 1, "legacy": 1, "active_source_sha256": "c97013f8c7c515a75701bb0979f435a0f81bbe9309157cc56a6135e7dbef0eb4", "active_output_sha256": "6119d2c5760e5f5234b9c53c990dad3a529777124bdbab794dc46bd562c1e9c0"},
    {"id": "18x18_repeat3_legacy", "geometry": [18, 18], "rowbytes": 157, "amount_f64": 11.0, "smoothness_fixed": 6553600, "repeat": 3, "bias": 2, "legacy": 1, "active_source_sha256": "6f911aa2fb9d2aa0f5c9db56936ff1bb0b2a5710cd49adc8e05467722ddef565", "active_output_sha256": "b47c25529ac36c0c7af7fb43659d67a5e7d3a4d77172706813dad47e1a700d26"},
    {"id": "18x12_repeat2_legacy_mixed_alpha", "geometry": [18, 12], "rowbytes": 157, "amount_f64": 3.0, "smoothness_fixed": 6553600, "repeat": 2, "bias": 2, "legacy": 1, "active_source_sha256": "c402d7ee39d3ef39015414094c13ca7f7308bad7414872a5edf6aa6005bdc6f9", "active_output_sha256": "28b16efe8ef4535661f1f514ff69195e944d1c071d78df1e8f5a8034cbcdc346"},
]
CELLS.append({"id":"20x16_smooth62_5_legacy","geometry":[20,16],"rowbytes":173,"amount_f64":7.0,"smoothness_fixed":4096000,"repeat":4,"bias":1,"legacy":1,"active_source_sha256":"d73bbdd3cf1872f20883fa596615702552eadf308e40552763d1eaa698007366","active_output_sha256":"2e97a898b15328c6fb11876f88951c9b1a593a66eb23bcbe89b94784c477ca1b"})
CLAIM = "For exactly eight source-bound PF16 cells, current Mac public SmartRender is raw exact to the same-source Windows exported owner. The Smoothness62.5 cell reproduces the owner's signed integer-part materialization while retaining the full fixed value in its exact predicate. Sixteen optional-checkin success controls and 494 bounded one-away/lifecycle controls preserve complete input and commit no failure output."


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> str:
    paths = {"source": SOURCE, "worker": WORKER, "legacy_worker": LEGACY_WORKER, "sha_helper": SHA_HELPER, "probe": PROBE, "owner": OWNER, "retained_owner": RETAINED_OWNER, "legacy_owner": LEGACY_OWNER}
    if {name: sha256(path) for name, path in paths.items()} != EXPECTED:
        raise RuntimeError("identity drift")
    with tempfile.TemporaryDirectory(prefix="olmblur-pf16-worker-sources-") as temp:
        executable = Path(temp) / "probe"
        sources = [
            PROBE,
            ROOT / "mac/OLMBlur/OLMBlur_Strings.cpp",
            *[ROOT / "core" / name for name in (
                "olmblur_helper.cpp", "olmblur_fullworker_helper.cpp",
                "olmblur_worker16_nonlegacy.cpp", "olmblur_worker16_legacy.cpp",
                "olmblur_worker32_nonlegacy.cpp", "olmblur_worker32_legacy.cpp",
                "olmblur_worker8_legacy.cpp", "olmblur_worker_orchestration.cpp",
            )],
            resolve_asset(ROOT / str(resolve_asset("Util/AEGP_SuiteHandler.cpp"))),
            resolve_asset(ROOT / str(resolve_asset("Util/MissingSuiteError.cpp"))),
        ]
        command = [
            "clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
            "-ffp-contract=off", "-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1",
            "-Wno-pragma-pack", "-Wno-deprecated-declarations",
            *[item for directory in ("Headers", "Headers/SP", "Util", "Resources", "core", "mac/OLMBlur") for item in ("-I", str(ROOT / directory))],
            *[str(path) for path in sources], "-framework", "Cocoa", "-o", str(executable),
        ]
        subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
        result = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True)
        if result.returncode or result.stderr:
            raise RuntimeError(f"probe rc={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}")
        return result.stdout


def build(stdout: str) -> dict[str, object]:
    lines = stdout.splitlines()
    positives = [line for line in lines if line.startswith("WORKER ") and " positive " in line]
    negatives = [line for line in lines if line.startswith("WORKER ") and " positive " not in line]
    if len(positives) != 16 or len(negatives) != 494 or lines[-1] != "worker_sources_all_exact=1 positive=16 negative=494":
        raise RuntimeError("run shape")
    if any("exact=0" in line for line in lines):
        raise RuntimeError("failed row")
    return {
        "schema": "olmblur.pf16-worker-sources-public-admission/3",
        "status": "PASS_PF16_8_WINDOWS_EXPORTED_TO_MAC_PUBLIC_RAW_EXACT_AND_494_FAIL_CLOSED",
        "identities": {
            "source": {"path": SOURCE.relative_to(ROOT).as_posix(), "sha256": EXPECTED["source"]},
            "worker": {"path": WORKER.relative_to(ROOT).as_posix(), "sha256": EXPECTED["worker"]},
            "legacy_worker": {"path": LEGACY_WORKER.relative_to(ROOT).as_posix(), "sha256": EXPECTED["legacy_worker"]},
            "sha_helper": {"path": SHA_HELPER.relative_to(ROOT).as_posix(), "sha256": EXPECTED["sha_helper"]},
            "probe": {"path": PROBE.relative_to(ROOT).as_posix(), "sha256": EXPECTED["probe"]},
            "windows_exported_owner": {"path": OWNER.relative_to(ROOT).as_posix(), "sha256": EXPECTED["owner"]},
            "retained_tuple_owner": {"path": RETAINED_OWNER.relative_to(ROOT).as_posix(), "sha256": EXPECTED["retained_owner"]},
            "legacy_retained_owner": {"path": LEGACY_OWNER.relative_to(ROOT).as_posix(), "sha256": EXPECTED["legacy_owner"]},
        },
        "cells": CELLS,
        "shared_parameters": {"depth": "PF16", "padding_per_row": 13},
        "summary": {"cells": 8, "positive_controls": 16, "negative_controls": 494,
                    "integer_materialization_boundary": 1, "all_exact": True},
        "run_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "run_lines": lines,
        "gates": [
            "real AE_Effect.h source-included SmartRender",
            "same-source Windows exported public owner for each cell",
            "active output SHA-256 raw exact and 13 input padding bytes copied only on success",
            "optional pixel checkin present/null and never called",
            "input full storage/header immutable and output header/guards immutable",
            "per-cell source first/middle/last mutation and every tuple one-away",
            "the adjacent admitted 12x12 Repeat1/Repeat2 pair is cross-pinned rather than mislabelled as a reject",
            "retained 18x18 Repeat3/Bias2 is raw exact and admitted only for its exact source and tuple",
            "retained Legacy 20x16 Smoothness62.5 reproduces the exported owner's signed integer-part materialization",
            "per-cell world/layout/format/downsample/nonalias controls",
            "per-cell five checkout and five checkin failure ordinals",
            "per-cell suite/format/copy/allocation failures",
        ],
        "claim_boundary": CLAIM,
        "claims_not_made": ["PF8 or PF32 for these geometries", "another PF16 source/tuple/layout", "fractional internal-worker equality for Smoothness62.5", "native Windows AE", "native Mac AE", "current installed binary", "release gate"],
    }


def validate(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"schema", "status", "identities", "cells", "shared_parameters", "summary", "run_sha256", "run_lines", "gates", "claim_boundary", "claims_not_made"}:
        raise ValueError("top schema")
    if value["schema"] != "olmblur.pf16-worker-sources-public-admission/3" or value["status"] != "PASS_PF16_8_WINDOWS_EXPORTED_TO_MAC_PUBLIC_RAW_EXACT_AND_494_FAIL_CLOSED" or value["claim_boundary"] != CLAIM:
        raise ValueError("authority")
    if value["cells"] != CELLS or value["shared_parameters"] != {"depth": "PF16", "padding_per_row": 13}:
        raise ValueError("contract")
    if value["summary"] != {"cells": 8, "positive_controls": 16, "negative_controls": 494, "integer_materialization_boundary": 1, "all_exact": True}:
        raise ValueError("summary")
    if len(value["run_lines"]) != 511 or sum(line.startswith("WORKER ") and " positive " in line for line in value["run_lines"]) != 16:
        raise ValueError("rows")
    if hashlib.sha256(("\n".join(value["run_lines"]) + "\n").encode()).hexdigest() != value["run_sha256"]:
        raise ValueError("run digest")
    for key, expected in EXPECTED.items():
        name = "windows_exported_owner" if key == "owner" else ("retained_tuple_owner" if key == "retained_owner" else ("legacy_retained_owner" if key == "legacy_owner" else key))
        if value["identities"][name]["sha256"] != expected:
            raise ValueError("identity")
    if value != build("\n".join(value["run_lines"]) + "\n"):
        raise ValueError("recanonicalization")


def markdown(value: dict[str, object]) -> str:
    return f"""# OLMBlur PF16 retained worker sources: Mac public admission

Status: **{value['status']}**

- Positive controls: 16
- Fail-closed controls: 494
- 12x12 Repeat1 output: `{CELLS[0]['active_output_sha256']}`
- 12x12 Repeat2 output: `{CELLS[1]['active_output_sha256']}`
- 18x18 Repeat1 output: `{CELLS[2]['active_output_sha256']}`
- 18x18 Repeat3 output: `{CELLS[3]['active_output_sha256']}`
- 12x12 Legacy Repeat2 output: `{CELLS[4]['active_output_sha256']}`
- 18x18 Legacy Repeat3 output: `{CELLS[5]['active_output_sha256']}`
- 18x12 Legacy mixed-alpha output: `{CELLS[6]['active_output_sha256']}`
- 20x16 Legacy Smoothness62.5 public output: `{CELLS[7]['active_output_sha256']}`

{CLAIM}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    stdout = run()
    fresh = build(stdout)
    validate(fresh)
    if args.write:
        REPORT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n")
        DOC.write_text(markdown(fresh))
        print(fresh["status"])
        return 0
    saved = json.loads(REPORT.read_text())
    validate(saved)
    if saved != fresh or DOC.read_text() != markdown(saved):
        raise RuntimeError("saved evidence drift")
    print(saved["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
