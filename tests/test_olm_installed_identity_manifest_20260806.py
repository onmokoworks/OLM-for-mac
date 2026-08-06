#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPDATER = ROOT / "scripts/update_olm_installed_identity_manifest_20260806.py"
PREFLIGHT = ROOT / "scripts/preflight_olm_all_universal_installs_20260805.py"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    updater = load("identity_updater", UPDATER)
    preflight = load("identity_preflight", PREFLIGHT)
    payload = json.loads(preflight.IDENTITY_MANIFEST.read_text(encoding="utf-8"))
    assert payload["schema"] == "olm.installed-identity-manifest/1"
    assert len(payload["plugins"]) == 10
    assert {row["plugin"] for row in payload["plugins"]} == set(updater.PLUGINS)
    assert all(row["source_installed_exact"] is True for row in payload["plugins"])
    assert all(row["universal_exact"] is True for row in payload["plugins"])
    assert all(row["codesign_exact"] is True for row in payload["plugins"])
    assert preflight.EXPECTED == {row["plugin"]: row["sha256"] for row in payload["plugins"]}
    current = updater.collect(payload["configuration"])
    assert [(row["plugin"], row["sha256"]) for row in current] == [
        (row["plugin"], row["sha256"]) for row in payload["plugins"]
    ]
    print("PASS_OLM_INSTALLED_IDENTITY_MANIFEST plugins=10 source_installed_exact=10 universal=10 signed=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
