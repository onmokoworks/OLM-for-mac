#!/usr/bin/env python3
"""Audit the installed 45-pair OLMRadialBlur transaction without launching AE."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "tools/emulation/audit_olmradialblur_type3_35_pair_install_20260813.py"
SPEC = importlib.util.spec_from_file_location("radial_35_install_audit_base", BASE_PATH)
assert SPEC and SPEC.loader
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

base.INSTALLER = ROOT / "scripts/install_olmradialblur_type3_45_pair_20260813.py"
base.INSTALLER_SHA = "793eacdccd65de8363d1c6bf439802b0fc762a9a855135e535fcd916d6a43fff"
base.PREPARED_SHA = "9074b9ca40d67e0c31d30511784c9c4daf6a1630919a6be5eb92287fc8409dc0"
base.TRANSACTION_SHA = "31237d469eda5b2242b47384aedbacff1d5912d10907122315379f5f2e1ea8a6"
base.PRE_IDENTITY_SHA = "7be33d88077c3ba90f7d9eeb73c156b0de53ac173d6bb46b5a15d46b0155fce3"
base.POST_IDENTITY_SHA = "c56a25298870d8aff5c9dfeef8f5229cb448160688e3121fcb0b186947c129d2"
base.BUILD_IDENTITY_SHA = "e9a45dfb386a3d5902ca34430ab488df31de5d34068cf2dc939a90530e648a04"
base.CLOSURE_SHA = "7c6a9f5a8ded8de9f9c0949099fe6acc18e229e49c5448ae7eaa86750b46ce11"
base.REPORT = ROOT / "refs/conformance/olmradialblur_type3_45_pair_install_20260813.json"
base.DOC = base.REPORT.with_suffix(".md")
base.STATUS = "PASS_RADIAL_TYPE3_45_PAIR_INSTALLED_ROLLBACK_CLOSED_AE_DEFERRED"
base.DOC_TEXT = """# OLMRadialBlur Type 3 45-pair incremental install

Verdict: `PASS_RADIAL_TYPE3_45_PAIR_INSTALLED_ROLLBACK_CLOSED_AE_DEFERRED`.

The signed Universal minOS 11 candidate `1b29b5ea...643c` is full-inventory
exact to the sole installed OLMRadialBlur bundle. The superseded
`ce5b57e1...0e7a` bundle remains in three full-inventory-exact rollback copies.
Only the Radial identity row and the two top-level timestamps changed.

Two all-ten preflights were byte-identical and observed no After Effects
process. This closes installed identity only. Native AE and the formal release
gate remain deferred to a later batched checkpoint.
"""


def generate() -> dict[str, object]:
    value = base.generate()
    value["schema"] = "olmradialblur.type3-45-pair-install/1"
    return value


def validate(value: object) -> None:
    keys = {"schema", "status", "authorities", "installed", "identity_change", "all10_preflight", "after_effects_processes", "scope"}
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("schema")
    if value != generate() or base.DOC.read_text() != base.DOC_TEXT:
        raise ValueError("live state or documentation drift")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    value = generate()
    if args.write:
        base.REPORT.write_bytes(base.canonical(value))
        base.DOC.write_text(base.DOC_TEXT)
    if not base.REPORT.exists() or not base.DOC.exists():
        raise SystemExit("missing report; use --write")
    before = base.REPORT.read_bytes()
    validate(json.loads(before))
    if before != base.canonical(value) or base.REPORT.read_bytes() != before:
        raise SystemExit("not canonical/read-only")
    print(base.STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
