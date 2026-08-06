#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools/emulation/olm_installed_identity.py"


def load():
    spec = importlib.util.spec_from_file_location("olm_installed_identity_test", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_failure(function, phrase: str) -> None:
    try:
        function()
    except RuntimeError as exc:
        assert phrase in str(exc), str(exc)
    else:
        raise AssertionError(f"expected fail-closed error containing {phrase!r}")


def main() -> int:
    module = load()
    with tempfile.TemporaryDirectory(prefix="olm-identity-binding-") as name:
        root = Path(name)
        bundle = root / "OLMSmoother.plugin"
        binary = bundle / "Contents/MacOS/OLMSmoother"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"accepted")
        digest = module.hashlib.sha256(binary.read_bytes()).hexdigest()
        manifest = root / "identity.json"
        row = {
            "plugin": "OLMSmoother",
            "sha256": digest,
            "installed_bundle": str(bundle),
            "source_installed_exact": True,
            "universal_exact": True,
            "codesign_exact": True,
        }

        def write(rows, schema=module.SCHEMA):
            manifest.write_text(json.dumps({"schema": schema, "plugins": rows}), encoding="utf-8")

        module.MANIFEST = manifest
        write([row])
        actual, accepted = module.verified_binary("OLMSmoother")
        assert actual == binary and accepted["sha256"] == digest

        write([])
        expect_failure(lambda: module.verified_binary("OLMSmoother"), "exactly one")
        write([row, row])
        expect_failure(lambda: module.verified_binary("OLMSmoother"), "duplicated")
        write([row], schema="retired")
        expect_failure(lambda: module.verified_binary("OLMSmoother"), "schema mismatch")
        write([row])
        binary.write_bytes(b"drifted")
        expect_failure(lambda: module.verified_binary("OLMSmoother"), "executable drifted")

    runner = (ROOT / "scripts/run_olm_mac_fixed_fixture_regression_20260805.py").read_text(encoding="utf-8")
    for lane, plugin in {
        "smoother": "OLMSmoother",
        "smoother2": "OLMSmoother2",
        "toondilate": "OLMToonDilate",
    }.items():
        assert f'"{lane}": "{plugin}"' in runner
    print("PASS_OLM_FIXED_REGRESSION_IDENTITY_BINDING lanes=3 fail_closed_cases=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
