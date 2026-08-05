#!/usr/bin/env python3
"""Static-only contract test for the two OLMRadialBlur AE runners."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
EVIDENCE = ROOT / "refs/conformance/olmradialblur_mac_ae_minimal_es3_loader_static_20260806.json"
RUNNERS = [
    SCRIPTS / "run_olmradialblur_case0010_pf8_mac_20260805.py",
    SCRIPTS / "run_olmradialblur_case0009_pf32_mac_20260805.py",
]


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    sys.path.insert(0, str(SCRIPTS))
    checks = []
    required = ["LOADER_ENTER payload=", "$.evalFile(payloadFile)", "LOADER_RETURN", "LOADER_FAIL error=", " line=", " file="]
    forbidden = ["alert(", "throw e", "JSON.stringify"]
    for runner in RUNNERS:
        module = load(runner)
        payload = Path("/tmp/olm radial payload.jsx")
        trace = Path("/tmp/olm radial host trace.log")
        loader = module.minimal_es3_loader(payload, trace)
        source = runner.read_text(encoding="utf-8")
        assertions = {
            "absolute_payload_literal": str(payload.resolve()) in loader,
            "absolute_trace_literal": str(trace.resolve()) in loader,
            "required_tokens": all(token in loader for token in required),
            "forbidden_tokens_absent": all(token not in loader for token in forbidden),
            "minimal_size": len(loader.encode("utf-8")) < 1200,
            "ae26_new_project_contract": "app.newProject();var project=app.project;if(!project)F(\"new project\")" in module.jsx(Path("/tmp/out"), Path("/tmp/result.json")),
            "doscriptfile_targets_loader": 'DoScriptFile POSIX file {json.dumps(str(loader))}' in source,
            "stale_trace_fails_closed": 'if trace.exists():' in source and '"stale_host_trace"' in source,
        }
        checks.append({"runner": str(runner.relative_to(ROOT)), "loader_bytes": len(loader.encode("utf-8")), "assertions": assertions})
    passed = all(all(item["assertions"].values()) for item in checks)
    report = {"kind": "olmradialblur_mac_ae_minimal_es3_loader_static", "status": "PASS" if passed else "FAIL", "ae_executed": False, "checks": checks}
    EVIDENCE.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
