#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "refs/reports/dblur_ucrt_expf_return/20260712_132106__RETURN__olm_runtime_trace_olmdirectionalblur_ucrt_expf_gaussian_tables_20260711__answered_portable_validated_tables.json"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dblur_ucrt_gaussian_") as temp:
        binary = Path(temp) / "test_dblur_gaussian_ucrt"
        subprocess.run(
            [
                "c++", "-std=c++17", "-O2", "-fno-fast-math",
                "-ffp-contract=off",
                str(ROOT / "tools/emulation/test_dblur_gaussian_ucrt.cpp"),
                "-o", str(binary),
            ],
            cwd=ROOT,
            check=True,
        )
        output = subprocess.check_output([str(binary)], cwd=ROOT, text=True)

    actual = {}
    for line in output.splitlines():
        count_text, index_text, bits = line.split()
        actual[(int(count_text), int(index_text))] = bits.upper()

    payload = json.loads(TABLES.read_text(encoding="utf-8"))
    expected = {}
    for table in payload["tables"]:
        count = int(table["n"])
        for index, bits in enumerate(table["words"]):
            expected[(count, index)] = bits.upper()

    if actual != expected:
        mismatches = [
            (key, expected.get(key), actual.get(key))
            for key in sorted(set(expected) | set(actual))
            if expected.get(key) != actual.get(key)
        ]
        raise SystemExit(f"UCRT Gaussian table mismatch: {mismatches[:8]}")

    print(f"[OK] DirectionalBlur Gaussian model matches {len(expected)}/336 UCRT words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
