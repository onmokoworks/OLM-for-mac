#!/usr/bin/env python3
"""Static smoke test for the live-AE Output Module probe wrapper."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "run_ae_output_module_probe.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_output_module_probe_") as tmp:
        wrapper = Path(tmp) / "wrapper.jsx"
        result = subprocess.run(
            [sys.executable, str(RUNNER), "--output", str(Path(tmp) / "probe.json"), "--dump-js", str(wrapper)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        assert result.returncode == 0, result.stdout
        source = wrapper.read_text(encoding="utf-8")
        assert "OLM_AE_OUTPUT_MODULE_PROBE" in source, source
        assert "ae_probe_output_module_templates.jsx" in source, source
    print("[OK] Output Module probe wrapper generation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
