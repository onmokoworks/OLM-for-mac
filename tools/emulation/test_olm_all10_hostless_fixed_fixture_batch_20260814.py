#!/usr/bin/env python3
"""Persist and validate the final all-ten hostless fixed-fixture batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/run_olm_mac_fixed_fixture_regression_20260805.py"
HANDOFF = ROOT / "handoffs/olm_all10_hostless_fixed_fixture_20260814"
LOG = HANDOFF / "fixed_fixture.log"
REPORT = HANDOFF / "report.json"
README = HANDOFF / "README.md"

SCHEMA = "olm.all10-hostless-fixed-fixture-batch/1"
STATUS = "PASS_ALL10_HOSTLESS_FIXED_FIXTURE_BATCH"
EXPECTED_RUNNER_SHA256 = "8be841691b2881c42c104ee79b9b0625697d96adf2d3d55a25e281ad29285e5f"
EXPECTED_LOG_SHA256 = "d5ae41d5ccd0c2b3800071cf6a56516deeb2b41358b6d29a5a7362d295e1cde3"
EXPECTED_LOG_BYTES = 578361
EXPECTED_LOG_LINES = 15663
EXPECTED_MARKER = "PASS_OLM_MAC_FIXED_FIXTURE_REGRESSION lanes=10 elapsed=1607.27s"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_report(log_bytes: bytes) -> dict:
    runner_bytes = RUNNER.read_bytes()
    text = log_bytes.decode("utf-8")
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "runner": {
            "path": str(RUNNER.relative_to(ROOT)),
            "sha256": sha256_bytes(runner_bytes),
        },
        "log": {
            "path": str(LOG.relative_to(ROOT)),
            "sha256": sha256_bytes(log_bytes),
            "bytes": len(log_bytes),
            "lines": len(text.splitlines()),
            "final_marker": text.splitlines()[-1],
        },
        "result": {
            "lanes": 10,
            "elapsed_seconds": 1607.27,
            "returncode": 0,
        },
        "scope": {
            "after_effects_launched": False,
            "aerender_launched": False,
            "installed_or_mediacore_mutated": False,
            "network_or_remote_windows_used": False,
            "hostless_fixed_fixtures_only": True,
            "native_ae_claim": False,
        },
        "claim_boundary": (
            "One exact invocation of the final checked-in all-ten fixed-fixture runner. "
            "It proves the runner's hostless fixture, public-entry, lifecycle, identity, "
            "and fail-close gates in their recorded order; it is not a native-AE smoke "
            "or an authorization to widen any production admission predicate."
        ),
    }


def validate_report(report: dict, log_bytes: bytes) -> None:
    expected_top = {"schema", "status", "runner", "log", "result", "scope", "claim_boundary"}
    assert set(report) == expected_top
    assert report["schema"] == SCHEMA
    assert report["status"] == STATUS
    assert report["runner"] == {
        "path": "scripts/run_olm_mac_fixed_fixture_regression_20260805.py",
        "sha256": EXPECTED_RUNNER_SHA256,
    }
    assert sha256_bytes(RUNNER.read_bytes()) == EXPECTED_RUNNER_SHA256
    assert report["log"] == {
        "path": "handoffs/olm_all10_hostless_fixed_fixture_20260814/fixed_fixture.log",
        "sha256": EXPECTED_LOG_SHA256,
        "bytes": EXPECTED_LOG_BYTES,
        "lines": EXPECTED_LOG_LINES,
        "final_marker": EXPECTED_MARKER,
    }
    assert sha256_bytes(log_bytes) == EXPECTED_LOG_SHA256
    assert len(log_bytes) == EXPECTED_LOG_BYTES
    assert len(log_bytes.decode("utf-8").splitlines()) == EXPECTED_LOG_LINES
    assert log_bytes.decode("utf-8").splitlines()[-1] == EXPECTED_MARKER
    assert report["result"] == {"lanes": 10, "elapsed_seconds": 1607.27, "returncode": 0}
    assert report["scope"] == {
        "after_effects_launched": False,
        "aerender_launched": False,
        "installed_or_mediacore_mutated": False,
        "network_or_remote_windows_used": False,
        "hostless_fixed_fixtures_only": True,
        "native_ae_claim": False,
    }
    assert report["claim_boundary"] == build_report(log_bytes)["claim_boundary"]


def render_readme(report: dict) -> str:
    return f"""# All-ten hostless fixed-fixture batch (2026-08-14)

Status: `{report['status']}`

- Exact final runner SHA-256: `{report['runner']['sha256']}`
- Complete log SHA-256: `{report['log']['sha256']}`
- Result: `{report['log']['final_marker']}`
- Log: `{report['log']['lines']}` lines / `{report['log']['bytes']}` bytes

This was one hostless batch. After Effects, `aerender`, network/remote Windows,
installation, and MediaCore mutation were not used. It is not native-AE smoke
evidence and does not widen any production admission predicate.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--source-log", type=Path)
    args = parser.parse_args()

    if args.write:
        if args.source_log is None:
            parser.error("--write requires --source-log")
        source = args.source_log.resolve()
        log_bytes = source.read_bytes()
        report = build_report(log_bytes)
        validate_report(report, log_bytes)
        HANDOFF.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, LOG)
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        README.write_text(render_readme(report), encoding="utf-8")

    log_bytes = LOG.read_bytes()
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    validate_report(report, log_bytes)
    assert README.read_text(encoding="utf-8") == render_readme(report)
    print(json.dumps({"status": report["status"], "lanes": 10, "elapsed_seconds": 1607.27}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
