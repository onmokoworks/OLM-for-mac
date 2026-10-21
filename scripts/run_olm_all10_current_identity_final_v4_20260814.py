#!/usr/bin/env python3
"""One-shot final current-identity AE host smoke.

This is a narrow live adapter over the reviewed base producer.  It changes
only the payload and generic-frame policy: OLMBlur and OLMDirectionalBlur are
enabled for a host-frame save; the other eight effects are loaded/applied and
then disabled before the generic save.  No numerical result is assessed.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/run_olm_all10_current_install_fresh_ae_smoke_20260812.py"
PAYLOAD = ROOT / "scripts/ae_host_all10_current_identity_deferred_v3_20260814.jsx"
CLAIM_BOUNDARY = (
    "Current installed host load/add/enable-state and exact mapping for all ten; "
    "generic effect-enabled host-frame render only for OLMBlur and "
    "OLMDirectionalBlur. The other eight are disabled before generic "
    "saveFrameToPng. Numerical behavior is not assessed. No pixel-exact, "
    "Windows-equivalence, typed-plane, padding, admission, or public-owner "
    "numerical-exact claim."
)


def load_base():
    spec = importlib.util.spec_from_file_location("olm_all10_final_v4_base", BASE)
    if not spec or not spec.loader:
        raise RuntimeError("cannot load base AE smoke producer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.RUNNER = Path(__file__).resolve()
    module.PAYLOAD = PAYLOAD
    module.ENABLED_HOST_FRAME_PLUGINS = {"OLMBlur", "OLMDirectionalBlur"}
    module.CLAIM_BOUNDARY = CLAIM_BOUNDARY
    return module


def main() -> int:
    return load_base().main()


if __name__ == "__main__":
    raise SystemExit(main())
