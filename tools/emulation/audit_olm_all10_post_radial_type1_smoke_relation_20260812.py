#!/usr/bin/env python3
"""Validate the post-Radial all-ten AE smoke relation.

The default invocation is read-only.  It binds the new summary and raw report
to the Radial-only incremental identity transition, the exact current identity
manifest, the producer runner/payload, and every durable handoff artifact.  It
also preserves the preceding Distance snapshot as immutable history and proves
that the producer validator cannot substitute it for the post-Radial capture.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "refs/conformance/olm_all10_post_radial_rotation_type1_inverse_cell_fresh_ae_smoke_20260812.json"
RAW = ROOT / "refs/conformance/olm_all10_post_radial_rotation_type1_inverse_cell_fresh_ae_smoke_raw_20260812.json"
DISTANCE_SUMMARY = ROOT / "refs/conformance/olm_all10_post_distance_mode5_fresh_ae_smoke_20260812.json"
DISTANCE_RAW = ROOT / "refs/conformance/olm_all10_post_distance_mode5_fresh_ae_smoke_raw_20260812.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
INCREMENTAL_INSTALL = ROOT / "refs/conformance/olmradialblur_type1_incremental_install_identity_20260812.json"
RUNNER = ROOT / "scripts/run_olm_all10_current_install_fresh_ae_smoke_20260812.py"
PAYLOAD = ROOT / "scripts/ae_host_all10_current_install_fresh_validation_20260812.jsx"
REPORT = ROOT / "refs/conformance/olm_all10_post_radial_type1_smoke_relation_20260812.json"
DOC = REPORT.with_suffix(".md")

SUMMARY_SHA = "fbfed8d7d83d0a53221e71ea6192ac135a4efd0438ee51277a45817ec0330b47"
RAW_SHA = "70af4ec2e13a569e5e4865f5140e89333c4b6c305e7bac8fdd10bf6d319eaafa"
DISTANCE_SUMMARY_SHA = "f8c0e884b1dbbade2fa58a2ca33d452459610716efc78089741bac29bee4d61c"
DISTANCE_RAW_SHA = "a2dca875aa7572aceeeb5b0300bb8d83689135975abe14ccd50172def1d1bd6d"
IDENTITY_SHA = "44e1dca88bb9413ca28e86792fcf9b7d5b48f71a6b770f35bd414897f5bc0061"
INCREMENTAL_INSTALL_SHA = "044a50eec5226a5c58c1d3e06788c602705385724071b77ea514f14897df6b0f"
RUNNER_SHA = "35fa2ecde4299dd9084ed1c89e50f20fd5ee016477cf18c9a460e696ddd6d459"
PAYLOAD_SHA = "ef0477d30d30b1b5c587ebcc511864bd4692ae0ef9cc2d656975a209df4ad511"
ARTIFACT_SET_SHA = "1e6740425b2cd8eda1eefa3c9f0a4ec82a6c2faacfff1bef06a28cb6406ab0eb"
RADIAL_OLD_SHA = "dee346586c21d9dbf04d89c6bac8a4f61f1e475b647f1df1fcb77a1eba536e97"
RADIAL_NEW_SHA = "03e837e8a9ccebbc3e03479b4d8a66f65aa85cce1ac0be616b14dac82284d548"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binding(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha(path),
        "size": path.stat().st_size,
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_producer():
    spec = importlib.util.spec_from_file_location("olm_all10_post_radial_smoke_producer", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def durable_artifact_rows(summary: dict[str, Any], raw: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for key in ("ae_return", "vmmap"):
        item = summary["artifacts"][key]
        rows.append([item["path"], item["sha256"], item["size"]])
    for key in ("launch_wrapper", "vmmap_ack"):
        item = raw["artifacts"][key]
        rows.append([item["path"], item["sha256"], item["size"]])
    for plugin in summary["plugins"]:
        item = plugin["png"]
        rows.append([item["path"], item["sha256"], item["size"]])
    return sorted(rows)


def artifact_set_sha(rows: list[list[Any]]) -> str:
    encoded = (json.dumps(rows, ensure_ascii=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(encoded).hexdigest()


def expected_bindings() -> dict[str, dict[str, Any]]:
    return {
        "post_radial_summary": binding(SUMMARY),
        "post_radial_raw": binding(RAW),
        "identity_manifest": binding(IDENTITY),
        "radial_incremental_install": binding(INCREMENTAL_INSTALL),
        "producer_runner": binding(RUNNER),
        "producer_payload": binding(PAYLOAD),
        "preserved_distance_summary": binding(DISTANCE_SUMMARY),
        "preserved_distance_raw": binding(DISTANCE_RAW),
    }


def validate(report: dict[str, Any]) -> None:
    assert report["schema"] == "olm.all10-post-radial-type1-smoke-relation/1"
    assert report["status"] == "PASS_POST_RADIAL_SMOKE_IDENTITY_RELATION"
    assert report["claim_boundary"] == (
        "Fresh installed-host plumbing for the exact Radial-only incremental identity; "
        "no AE numerical exactness and no replacement or mutation of the Distance snapshot"
    )
    datetime.fromisoformat(report["generated_at"].replace("Z", "+00:00"))

    assert sha(SUMMARY) == SUMMARY_SHA
    assert sha(RAW) == RAW_SHA
    assert sha(DISTANCE_SUMMARY) == DISTANCE_SUMMARY_SHA
    assert sha(DISTANCE_RAW) == DISTANCE_RAW_SHA
    assert sha(IDENTITY) == IDENTITY_SHA
    assert sha(INCREMENTAL_INSTALL) == INCREMENTAL_INSTALL_SHA
    assert sha(RUNNER) == RUNNER_SHA
    assert sha(PAYLOAD) == PAYLOAD_SHA
    assert report["bindings"] == expected_bindings()

    summary = load_json(SUMMARY)
    raw = load_json(RAW)
    old_summary = load_json(DISTANCE_SUMMARY)
    old_raw = load_json(DISTANCE_RAW)
    identity = load_json(IDENTITY)
    install = load_json(INCREMENTAL_INSTALL)
    producer = load_producer()

    assert summary["schema"] == "olm.all10-current-install-fresh-ae-smoke/1"
    assert raw["schema"] == "olm.all10-current-install-fresh-ae-smoke-raw/1"
    assert summary["status"] == raw["status"] == "pass"
    assert summary["passed"] is raw["passed"] is True
    assert producer.validate_persisted_summary(summary, raw, RAW) is True

    assert summary["installed_identity_manifest"] == raw["installed_identity_manifest"]
    manifest_binding = summary["installed_identity_manifest"]
    assert manifest_binding["path"] == IDENTITY.relative_to(ROOT).as_posix()
    assert manifest_binding["sha256"] == IDENTITY_SHA
    assert manifest_binding["accepted_at"] == identity["accepted_at"]
    assert manifest_binding["accepted_manifest_status"] == "verified_before_launch"
    assert summary["runner"] == binding(RUNNER)
    assert summary["artifacts"]["payload"] == binding(PAYLOAD)
    assert summary["raw_report"] == {
        "path": RAW.relative_to(ROOT).as_posix(),
        "sha256": RAW_SHA,
    }

    identity_rows = {row["plugin"]: row for row in identity["plugins"]}
    summary_rows = {row["plugin"]: row for row in summary["plugins"]}
    raw_rows = {row["plugin"]: row for row in raw["plugins"]}
    assert set(identity_rows) == set(summary_rows) == set(raw_rows)
    radial_identity = identity_rows["OLMRadialBlur"]
    radial_summary = summary_rows["OLMRadialBlur"]
    radial_raw = raw_rows["OLMRadialBlur"]
    assert radial_identity["sha256"] == radial_identity["source_sha256"] == RADIAL_NEW_SHA
    assert radial_summary["accepted_executable_sha256"] == RADIAL_NEW_SHA
    assert radial_summary["installed_executable_sha256"] == RADIAL_NEW_SHA
    assert radial_summary["post_render_on_disk_sha256"] == RADIAL_NEW_SHA
    assert radial_raw["accepted_executable_sha256"] == RADIAL_NEW_SHA
    assert radial_raw["pre_launch_executable_sha256"] == RADIAL_NEW_SHA
    assert radial_raw["post_render_on_disk_sha256"] == RADIAL_NEW_SHA
    assert radial_summary["loaded_module_count"] == radial_raw["loaded_module_count"] == 1
    assert radial_summary["post_render_mapping_exact"] is radial_raw["post_render_mapping_exact"] is True

    transition = install["identity_transition"]
    assert install["schema"] == "olmradialblur.type1-incremental-install-identity/1"
    assert install["status"] == "PASS_RECOVERABLE_RADIAL_ONLY_INSTALL_IDENTITY"
    assert install["accepted_identity_manifest_sha256"] == IDENTITY_SHA
    assert transition["changed_plugins"] == ["OLMRadialBlur"]
    assert transition["changed_fields"] == {"OLMRadialBlur": ["sha256", "source_sha256"]}
    assert transition["top_level_changed_fields"] == []
    assert transition["old_executable_sha256"] == RADIAL_OLD_SHA
    assert transition["new_executable_sha256"] == RADIAL_NEW_SHA

    artifacts = durable_artifact_rows(summary, raw)
    assert len(artifacts) == report["durable_artifacts"]["count"] == 14
    assert artifact_set_sha(artifacts) == report["durable_artifacts"]["canonical_sha256"] == ARTIFACT_SET_SHA
    assert len({row[0] for row in artifacts}) == 14
    for path_text, expected_sha, expected_size in artifacts:
        path = (ROOT / path_text).resolve()
        path.relative_to(ROOT)
        assert path.is_file()
        assert sha(path) == expected_sha
        assert path.stat().st_size == expected_size

    # The preserved Distance capture is intentionally historical.  Its bytes
    # remain fixed, but it cannot validate against the new identity manifest or
    # be paired with the post-Radial summary/raw authority.
    assert old_summary["raw_report"]["path"] == DISTANCE_RAW.relative_to(ROOT).as_posix()
    assert old_summary["installed_identity_manifest"]["sha256"] != IDENTITY_SHA
    assert producer.validate_persisted_summary(old_summary, old_raw, DISTANCE_RAW) is False
    assert producer.validate_persisted_summary(summary, old_raw, DISTANCE_RAW) is False
    assert producer.validate_persisted_summary(old_summary, raw, RAW) is False
    assert report["relations"] == {
        "distance_snapshot_bytes_preserved": True,
        "distance_snapshot_substitution_rejected": True,
        "incremental_identity_changed_plugins": ["OLMRadialBlur"],
        "post_radial_producer_validation": True,
        "radial_executable_sha256": RADIAL_NEW_SHA,
    }


def generate() -> dict[str, Any]:
    summary = load_json(SUMMARY)
    raw = load_json(RAW)
    rows = durable_artifact_rows(summary, raw)
    report = {
        "schema": "olm.all10-post-radial-type1-smoke-relation/1",
        "status": "PASS_POST_RADIAL_SMOKE_IDENTITY_RELATION",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": (
            "Fresh installed-host plumbing for the exact Radial-only incremental identity; "
            "no AE numerical exactness and no replacement or mutation of the Distance snapshot"
        ),
        "bindings": expected_bindings(),
        "durable_artifacts": {
            "count": len(rows),
            "canonical_sha256": artifact_set_sha(rows),
        },
        "relations": {
            "distance_snapshot_bytes_preserved": True,
            "distance_snapshot_substitution_rejected": True,
            "incremental_identity_changed_plugins": ["OLMRadialBlur"],
            "post_radial_producer_validation": True,
            "radial_executable_sha256": RADIAL_NEW_SHA,
        },
    }
    validate(report)
    return report


def write(report: dict[str, Any]) -> None:
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DOC.write_text(
        "# Post-Radial Type 1 all-ten fresh AE smoke relation\n\n"
        "Status: **PASS_POST_RADIAL_SMOKE_IDENTITY_RELATION**. The new all-ten "
        "fresh host-plumbing capture is bound to identity manifest `44e1dca8...`, "
        "the Radial-only incremental transition, installed OLMRadialBlur executable "
        "`03e837e8...`, the exact producer runner/payload, raw report, vmmap, AE "
        "return, launch/ack files, and ten PNGs. The preceding Distance summary/raw "
        "retain their exact historical bytes and fail producer validation when "
        "substituted for the post-Radial authority. This makes no AE numerical or "
        "cross-host exactness claim.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Explicitly regenerate the relation report and note.")
    args = parser.parse_args()
    if args.write:
        write(generate())
    else:
        validate(load_json(REPORT))
    print("PASS_OLM_ALL10_POST_RADIAL_TYPE1_SMOKE_RELATION_20260812")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
