#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path


PROBE = Path(__file__).with_name("probe_olmkirakira_mode4_fullcaller_scaffold_20260807.py")
spec = importlib.util.spec_from_file_location("olmkira_fullcaller", PROBE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


if __name__ == "__main__":
    raise SystemExit(module.main(natural=True))
