#!/usr/bin/env python3
"""Bind the 2026-08-22 Public Beta RC quick host run to its exact artifacts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PLUGINS = {
    "ColorKeep", "OLMBlur", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur", "OLMSmoother",
    "OLMSmoother2", "OLMToonDilate",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return value


def load_verifier():
    path = ROOT / "scripts/run_ae_single_case.py"
    spec = importlib.util.spec_from_file_location("olm_single_case_verifier", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    campaign_path = args.campaign.resolve(strict=True)
    identity_path = args.identity.resolve(strict=True)
    package_path = args.package.resolve(strict=True)
    campaign = load_json(campaign_path)
    identity = load_json(identity_path)
    matrix = campaign.get("matrix")
    plugins = campaign.get("plugins")
    identity_plugins = identity.get("plugins")
    if (
        campaign.get("status") != "completed"
        or campaign.get("profile") != "quick"
        or not isinstance(matrix, list)
        or not isinstance(plugins, list)
        or not isinstance(identity_plugins, list)
    ):
        raise ValueError("campaign or identity is not an accepted quick-run input")
    if len(matrix) != 10 or {row.get("plugin") for row in matrix if isinstance(row, dict)} != EXPECTED_PLUGINS:
        raise ValueError("campaign is not the exact ten-plugin matrix")

    identity_by_plugin = {
        row["plugin"]: row
        for row in identity_plugins
        if isinstance(row, dict) and isinstance(row.get("plugin"), str)
    }
    campaign_by_plugin = {
        row["binary"]: row
        for row in plugins
        if isinstance(row, dict) and isinstance(row.get("binary"), str)
    }
    if set(identity_by_plugin) != EXPECTED_PLUGINS or set(campaign_by_plugin) != EXPECTED_PLUGINS:
        raise ValueError("identity or campaign plugin set differs")

    verifier = load_verifier()
    accepted_cases = []
    ae_versions = set()
    for row in matrix:
        if not isinstance(row, dict):
            raise ValueError("matrix row is not an object")
        plugin = row.get("plugin")
        if (
            row.get("status") != "passed"
            or row.get("returncode") != 0
            or row.get("depth") != 8
            or row.get("width") != 1920
            or row.get("height") != 1080
            or not isinstance(plugin, str)
        ):
            raise ValueError(f"matrix row is not an accepted HD 8bpc result: {plugin}")
        identity_row = identity_by_plugin[plugin]
        campaign_plugin = campaign_by_plugin[plugin]
        plugin_sha = identity_row.get("sha256")
        if (
            campaign_plugin.get("installed_sha256") != plugin_sha
            or campaign_plugin.get("current_build_installed") is not True
            or identity_row.get("source_installed_exact") is not True
            or identity_row.get("codesign_exact") is not True
            or identity_row.get("universal_exact") is not True
        ):
            raise ValueError(f"installed identity is not exact: {plugin}")

        stdout = row.get("stdout")
        if not isinstance(stdout, str):
            raise ValueError(f"missing runner stdout: {plugin}")
        commit_match = re.search(r"^\[INFO\] commit_json: (.+)$", stdout, re.MULTILINE)
        digest_match = re.search(r"^\[INFO\] commit_sha256: ([0-9a-f]{64})$", stdout, re.MULTILINE)
        if commit_match is None or digest_match is None:
            raise ValueError(f"missing commit anchor: {plugin}")
        commit_path = Path(commit_match.group(1)).resolve(strict=True)
        commit_digest = digest_match.group(1)
        commit_bytes = commit_path.read_bytes()
        run_id = commit_path.parents[1].name.removeprefix("single_run_")
        verification = verifier.verify_single_case_commit(
            commit_path,
            expected_run_id=run_id,
            expected_commit_sha256=commit_digest,
            expected_commit_bytes=commit_bytes,
        )
        if verification.get("status") != "passed":
            raise ValueError(f"consumer verification failed for {plugin}: {verification}")
        commit = json.loads(commit_bytes.decode("utf-8"))
        result_path = commit_path.parent / "AE_SINGLE_CASE_RESULT.json"
        result = load_json(result_path)
        raw_log = commit_path.parents[1] / "raw_output/AE_SINGLE_CASE.log"
        raw_log_text = raw_log.read_text(encoding="utf-8-sig")
        if (
            result.get("status") != "ok"
            or result.get("project_bits_per_channel") != 8
            or "gpuAccelType=SOFTWARE" not in raw_log_text
            or "effect added " not in raw_log_text
        ):
            raise ValueError(f"host/effect attestation differs: {plugin}")
        ae_versions.add(result.get("ae_version"))
        artifact = commit.get("validated_output")
        if not isinstance(artifact, dict):
            raise ValueError(f"missing validated artifact: {plugin}")
        accepted_cases.append({
            "plugin": plugin,
            "plugin_sha256": plugin_sha,
            "case_id": row.get("case_id"),
            "depth": 8,
            "width": 1920,
            "height": 1080,
            "execution_route": row.get("execution_route"),
            "parameter_overrides": row.get("parameter_overrides"),
            "commit_sha256": commit_digest,
            "validated_output_sha256": artifact.get("sha256"),
            "validated_output_size_bytes": artifact.get("size_bytes"),
        })

    report = {
        "schema": "olm.public-beta-rc-native-ae-quick/1",
        "status": "accepted_exact",
        "scope": "ten-plugin HD 8bpc quick smoke only; not the full depth/route/parameter matrix",
        "host": {
            "application": "Adobe After Effects 2026",
            "ae_versions": sorted(ae_versions),
            "renderer": "SOFTWARE",
        },
        "package": {
            "filename": package_path.name,
            "sha256": sha256(package_path),
        },
        "installed_identity_manifest": {
            "path": str(identity_path.relative_to(ROOT)),
            "sha256": sha256(identity_path),
            "accepted_at": identity.get("accepted_at"),
        },
        "campaign": {
            "path": str(campaign_path.relative_to(ROOT)),
            "sha256": sha256(campaign_path),
            "profile": "quick",
            "accepted_cases": len(accepted_cases),
        },
        "accepted_cases": sorted(accepted_cases, key=lambda item: item["plugin"]),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
