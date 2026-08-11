#!/usr/bin/env python3
"""Mode 3 Gaussian Length 50 actual exported owner gate."""

from __future__ import annotations

import os
import runpy

os.environ["OLM_KIRA_EXPORTED_CASE"] = "mode3_gaussian_length50"
os.environ["OLM_KIRA_BLUR_MODE"] = "3"
os.environ["OLM_KIRA_MERGE_MODE"] = "1"
os.environ["OLM_KIRA_HORIZONTAL_LENGTH"] = "50"
os.environ["OLM_KIRA_EXPORTED_REPORT"] = (
    "refs/conformance/olmkirakira_mode3_gaussian_length50_exported_effectmain_all_depths_20260812.json"
)
runpy.run_path(
    os.path.join(os.path.dirname(__file__), "test_olmkirakira_mode1_exported_effectmain_all_depths_20260812.py"),
    run_name="__main__",
)
