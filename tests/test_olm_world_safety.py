#!/usr/bin/env python3
"""Compile and exercise the SDK-light world layout/staging helper."""

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class OLMWorldSafetyTests(unittest.TestCase):
    def test_cpp_contract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm_world_safety_") as raw:
            binary = Path(raw) / "test_olm_world_safety"
            subprocess.run(
                ["c++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
                 str(ROOT / "tests/test_olm_world_safety.cpp"), "-o", str(binary)],
                check=True,
            )
            subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    unittest.main()
