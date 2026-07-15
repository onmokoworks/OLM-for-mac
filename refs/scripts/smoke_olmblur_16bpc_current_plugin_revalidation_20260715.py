#!/usr/bin/env python3
"""Validate the immutable OLMBlur 16bpc current-plugin revalidation record."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / "refs/conformance/olmblur_16bpc_current_plugin_revalidation_20260715.json"
AUDIT = ROOT / "refs/conformance/olmblur_case0006_reference_provenance_audit_20260701.json"
REQUEST = ROOT / "refs/mac_validation_requests/olmblur_case0006_mac_observation_20260715.json"
PLUGIN_SHA = "c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206"
CASE6_SHA = "27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    record = load(RECORD)
    audit = load(AUDIT)
    request = load(REQUEST)
    cases = record["verification"]["cases"]
    exact = [case for case in cases if case["status"] == "exact"]
    unresolved = [case for case in cases if case["status"] == "unresolved"]
    assert record["immutable"] is True
    assert len(cases) == 7
    assert len(exact) == record["verification"]["summary"]["exact"] == 5
    assert len(unresolved) == record["verification"]["summary"]["unresolved"] == 2
    assert record["verification"]["summary"]["total"] == 7
    assert record["provenance"]["installed_plugin"]["sha256"] == PLUGIN_SHA
    assert request["observation"]["mac_plugin_binary_sha256"] == PLUGIN_SHA
    verifier = record["provenance"]["verifier_report"]
    observation = record["provenance"]["observation_report"]
    assert verifier["retained"] is True
    assert observation["retained"] is True
    assert sha256(ROOT / verifier["path"]) == verifier["sha256"]
    assert sha256(ROOT / observation["path"]) == observation["sha256"]
    retained_verifier = load(ROOT / verifier["path"])
    assert retained_verifier["summary"] == {"fail": 2, "missing": 0, "ok": 5, "total": 7}
    case6 = next(case for case in cases if case["case_id"] == "olmblur__case_0006")
    retained = audit["files"]["canonical_ref"]
    assert retained["exists"] is True
    assert retained["sha256"] == CASE6_SHA
    assert sha256(ROOT / retained["path"]) == CASE6_SHA
    assert case6["candidate_sha256"] == CASE6_SHA
    assert case6["canonical_windows_sha256"] == CASE6_SHA
    for case in cases:
        reference_sha = sha256(ROOT / case["canonical_windows_path"])
        assert reference_sha == case["canonical_windows_sha256"]
        if case["status"] == "exact":
            assert case["candidate_sha256"] == reference_sha
    assert next(case for case in cases if case["case_id"] == "olmblur__case_0003")["reported_sample_count"] == 20
    assert next(case for case in cases if case["case_id"] == "olmblur__case_0004")["reported_sample_count"] == 2
    print("[OK] OLMBlur 16bpc current-plugin revalidation record smoke")


if __name__ == "__main__":
    main()
