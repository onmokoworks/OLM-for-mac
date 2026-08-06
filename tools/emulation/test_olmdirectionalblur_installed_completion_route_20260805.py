#!/usr/bin/env python3
"""Fail-closed DirectionalBlur entry-to-installed-bundle completion route."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.emulation.olm_installed_identity import MANIFEST as IDENTITY_MANIFEST
from tools.emulation.olm_installed_identity import verified_binary

PF16 = ROOT / "tools/emulation/test_olmdirectionalblur_minimal_pf16_production_20260805.py"
PF32 = ROOT / "tools/emulation/test_olmdirectionalblur_minimal_pf32_production_20260805.py"
SMART = ROOT / "tools/emulation/test_olmdirectionalblur_mac_smartrender_adapter_20260717.py"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDirectionalBlur.plugin"


def run_json(path: Path) -> dict:
    run = subprocess.run([sys.executable, str(path)], cwd=ROOT, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: {path.name} failed\n{run.stdout}\n{run.stderr}")
    lines = [line for line in run.stdout.splitlines() if line.startswith("{")]
    if not lines:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: {path.name} emitted no JSON")
    return json.loads(lines[-1].replace("'", '"'))


def main() -> int:
    binary, identity = verified_binary("OLMDirectionalBlur")
    if Path(identity["installed_bundle"]) != INSTALLED or identity.get("installed_bundle_count") != 1:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: manifest selects an unexpected DirectionalBlur installation")
    pf16 = run_json(PF16)
    pf32 = run_json(PF32)
    smart = run_json(SMART)
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    arch = subprocess.run(["lipo", "-archs", str(binary)], capture_output=True, text=True, check=True).stdout.split()
    sign = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(INSTALLED)], capture_output=True)
    active = list(INSTALLED.parent.glob("OLMDirectionalBlur.plugin"))
    public_effectmain_exact = bool(smart.get("cases")) and all(
        case.get("public_effectmain_exact") is True for case in smart["cases"]
    )
    if (pf16.get("status") != "pass" or pf32.get("status") != "pass" or
            smart.get("status") != "pass" or not public_effectmain_exact or
            digest != identity["sha256"] or
            set(arch) != {"arm64", "x86_64"} or sign.returncode != 0 or len(active) != 1):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: installed completion route is not closed")
    report = {
        "status": "pass",
        "route": [
            "actual AEX typed entry/callbacks",
            "portable float processing and typed writer full-frame equality",
            "public EffectMain SmartPreRender/SmartRender exact typed-core output, callbacks, and row padding",
            "installed signed Universal bundle identity",
        ],
        "actual_production": {
            "PF16_cases": len(pf16["cases"]), "PF32_cases": len(pf32["cases"]),
            "PF16_callbacks": ["0x1800068e0", "0x180006a90"],
            "PF32_callbacks": pf32["callbacks"],
        },
        "smart_render": {"status": smart["status"], "public_effectmain_exact": public_effectmain_exact,
                         "depths": [case["pixel_format"] for case in smart["cases"]]},
        "installed": {"path": str(INSTALLED), "binary_sha256": digest,
                      "identity_manifest": str(IDENTITY_MANIFEST.relative_to(ROOT)),
                      "architectures": arch, "codesign": "valid", "active_bundle_count": len(active)},
        "claim_boundary": "AE was not launched; cross-host interactive AE output remains unclaimed",
    }
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
