#!/usr/bin/env python3
"""Smoke the bounded OLMColorKey 32bpc Mac host/path static contract."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_olmcolorkey_32bpc_host_path_20260716 import build_report  # noqa: E402


def main() -> int:
    report = build_report(ROOT)
    facts = report["facts"]
    assert report["status"] == "pass_static_contract"
    assert facts["smart_render_reads_explicit_bitdepth"]
    assert facts["smart_render_captures_float_entry_at_bitdepth_32"]
    assert facts["smart_render_dispatches_explicit_bitdepth"]
    assert facts["render_world_has_float_branch"]
    assert facts["float_pixel_traits_are_native_float"]
    assert facts["mac_pair_is_host_conversion_blocked"]
    assert facts["mac_pair_not_ae_exact"]
    assert facts["existing_gate_remains_closed"]
    print("[OK] OLMColorKey 32bpc Mac host-path static contract smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
