#!/usr/bin/env python3
"""PF8 Legacy production BlurRender dispatch versus actual-AEX fixtures."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import test_olmblur_pf8_nonlegacy_source_aex_adapter_20260805 as adapter

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tools/emulation/fixtures/olmblur_worker8_legacy/manifest.json"
MANIFEST_SHA256 = "144d0f8bfdccc6d8d6aa48344addb4dc9b10b280cbdfd585059c35d9f2bf4fa1"


def main() -> int:
    assert hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == MANIFEST_SHA256
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["bit_depth"] == 8 and manifest["legacy"] == 1
    results = []
    with tempfile.TemporaryDirectory(prefix="olmblur_pf8_legacy_adapter_") as name:
        executable = adapter.compile_probe(Path(name))
        for case in manifest["cases"]:
            directory = MANIFEST.parent / case["id"]
            run = subprocess.run([
                str(executable), str(case["width"]), str(case["height"]),
                str(case["blur_amount"]), str(case["smoothness"]),
                str(case["repeat"]), str(case["bias_direction"]), "1",
                str(directory / "source_argb.bin"),
                str(directory / "expected_argb.bin")],
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
        "status": "pass", "bit_depth": 8, "legacy": 1,
        "dispatch": "Mac production BlurRender -> PF8 Legacy worker",
        "aex_sha256": manifest["binary_sha256"], "case_count": len(results),
        "cases": results,
        "scope": "production public render dispatcher against retained actual-AEX complete worker fixtures; no AE-host or EffectMain command invocation claim"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
