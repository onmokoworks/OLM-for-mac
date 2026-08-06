#!/usr/bin/env python3
"""PF16 Legacy production BlurRender dispatch versus actual-AEX fixtures."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import test_olmblur_32bpc_source_aex_adapter_20260717 as base

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tools/emulation/fixtures/olmblur_worker16_legacy/manifest.json"
MANIFEST_SHA256 = "11ac4c8600f41ce8e3dcbb6aa41999817a3d4dc4c089d563e8f3b1eeb30b53d6"


def pf16_probe_source() -> str:
    source = base.probe_source()
    replacements = {
        "const int rowbytes = width * 16 + 32; const std::size_t active = static_cast<std::size_t>(width) * 16;":
            "const int rowbytes = width * 8 + 23; const std::size_t active = static_cast<std::size_t>(width) * 8;",
        "PF_EffectWorld in{input.data(), rowbytes, width, height, 32,":
            "PF_EffectWorld in{input.data(), rowbytes, width, height, 16,",
        "PF_EffectWorld out{output.data(), rowbytes, width, height, 32,":
            "PF_EffectWorld out{output.data(), rowbytes, width, height, 16,",
        "BlurRender(&in_data, &in, &out, 32, &params)":
            "BlurRender(&in_data, &in, &out, 16, &params)",
        "for (int i = 0; i < 32; ++i)": "for (int i = 0; i < 23; ++i)",
        "actual + x * 16, source.data() + y * active + x * 16, 4":
            "actual + x * 8, source.data() + y * active + x * 8, 2",
    }
    for old, new in replacements.items():
        if old not in source:
            raise RuntimeError(f"base probe shape changed: {old}")
        source = source.replace(old, new)
    return source


def compile_probe(directory: Path) -> Path:
    compiler = shutil.which(os.environ.get("CXX", "clang++"))
    if not compiler:
        raise RuntimeError("clang++ is unavailable")
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True,
                         text=True, check=True).stdout.strip()
    source = directory / "probe.cpp"
    executable = directory / "probe"
    source.write_text(pf16_probe_source().replace(
        "__OLMBLUR_MAC_SOURCE__",
        str(ROOT / "mac/OLMBlur/OLMBlur.cpp").replace("\\", "\\\\").replace('"', '\\"')),
        encoding="utf-8")
    command = [compiler, "-std=c++17", "-arch", "arm64", "-O2",
               "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk,
               "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
               "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
               "-I", str(ROOT / "core"), str(source),
               str(ROOT / "core/olmblur_helper.cpp"),
               str(ROOT / "core/olmblur_fullworker_helper.cpp"),
               str(ROOT / "core/olmblur_worker16_nonlegacy.cpp"),
               str(ROOT / "core/olmblur_worker16_legacy.cpp"),
               str(ROOT / "core/olmblur_worker32_nonlegacy.cpp"),
               str(ROOT / "core/olmblur_worker32_legacy.cpp"),
               str(ROOT / "core/olmblur_worker8_legacy.cpp"),
               str(ROOT / "core/olmblur_worker_orchestration.cpp"),
               "-framework", "Cocoa", "-o", str(executable)]
    subprocess.run(command, cwd=ROOT, check=True)
    return executable


def main() -> int:
    assert hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == MANIFEST_SHA256
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["bit_depth"] == 16 and manifest["legacy"] == 1
    results = []
    with tempfile.TemporaryDirectory(prefix="olmblur_pf16_legacy_adapter_") as name:
        executable = compile_probe(Path(name))
        for case in manifest["cases"]:
            directory = MANIFEST.parent / case["id"]
            run = subprocess.run([
                str(executable), str(case["width"]), str(case["height"]),
                str(case["blur_amount"]), str(case["smoothness"]),
                str(case["repeat"]), str(case["bias_direction"]), "1",
                str(directory / "source_argb16.bin"),
                str(directory / "expected_argb16.bin")],
                cwd=ROOT, capture_output=True, text=True, check=False)
            if run.returncode:
                raise RuntimeError(f"{case['id']}: {run.stdout} {run.stderr}")
            row = json.loads(run.stdout)
            assert row == {"status": "pass", "mismatched_bytes": 0,
                           "alpha_mismatches": 0, "padding_mismatches": 0}
            row["id"] = case["id"]
            results.append(row)
    print(json.dumps({
        "schema": "olmblur.mac-source-aex-adapter/1",
        "status": "pass", "bit_depth": 16, "legacy": 1,
        "dispatch": "Mac production BlurRender -> PF16 Legacy worker",
        "aex_sha256": manifest["binary_sha256"], "case_count": len(results),
        "cases": results,
        "scope": "production public render dispatcher against retained actual-AEX complete worker fixtures; no AE-host or EffectMain command invocation claim"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
