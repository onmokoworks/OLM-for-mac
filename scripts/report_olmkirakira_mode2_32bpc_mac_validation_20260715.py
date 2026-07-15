#!/usr/bin/env python3
"""Verify the Mode 2 Mac return and emit exactness only after raw FLOAT32 equality."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_float_exr import read_planes  # noqa: E402
from verify_32bpc_float_return import canonical_sha256, inspect_float_rgba_exr, VerificationError  # noqa: E402

REQUEST = ROOT / "refs/mac_validation_requests/olmkirakira_mode2_32bpc_mac_validation_20260715.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_artifact(item: dict, output_dir: Path, label: str) -> Path:
    path = Path(item.get("path", ""))
    if not path.is_absolute(): path = output_dir / path.name
    if path.parent.resolve() != output_dir.resolve(): raise VerificationError(label + " path escapes output directory")
    if not path.is_file() or path.suffix.lower() != ".exr": raise VerificationError(label + " is missing or not EXR")
    if item.get("sha256") != digest(path): raise VerificationError(label + " SHA-256 mismatch")
    inspect_float_rgba_exr(path, (1920, 1080))
    return path


def compare(expected: Path, actual: Path) -> dict:
    left, lw, lh = read_planes(expected); right, rw, rh = read_planes(actual)
    if (lw, lh) != (rw, rh): raise VerificationError("raw comparison dimensions differ")
    mismatches = sum(a != b for name in sorted(left) for a, b in zip(left[name], right[name]))
    return {"equal": mismatches == 0, "mismatched_samples": mismatches, "dimensions": [lw, lh], "channel_mapping": "semantic channel names A/B/G/R"}


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("return_json",type=Path); ap.add_argument("--output-dir",type=Path,required=True); ap.add_argument("--report-json",type=Path); a=ap.parse_args(); failures=[]
    request=json.loads(REQUEST.read_text(encoding="utf-8")); data=json.loads(a.return_json.read_text(encoding="utf-8")); case=request["case"]
    try:
        if data.get("kind")!="olmkirakira_mode2_32bpc_mac_validation_return": raise VerificationError("wrong return kind")
        if data.get("ae_exact_claim") is not False: raise VerificationError("exact claim must be false before comparison")
        if data.get("request_id")!=request["request_id"] or data.get("case",{}).get("id")!=case["id"]: raise VerificationError("request/case identity mismatch")
        if data.get("plugin",{}).get("filename")!=request["plugin"]["filename"] or data["plugin"].get("sha256")!=request["plugin"]["sha256"]: raise VerificationError("loaded plugin identity mismatch")
        if not Path(data["plugin"].get("path","")).is_file() or digest(Path(data["plugin"]["path"]))!=data["plugin"]["sha256"]: raise VerificationError("loaded plugin hash is not bound to a file")
        if data.get("project") != {"bits_per_channel":32,"renderer":"SOFTWARE","working_space":"None","linear_blending":False,"frame":0}: raise VerificationError("AE/project/color contract drift")
        if data.get("output_module",{}).get("template_name")!="OLM EXR 32 Float" or data["output_module"].get("capture_api")!="OutputModule.getSettings(GetSettingsFormat.STRING)": raise VerificationError("Output Module contract drift")
        returned=data.get("case",{}); params=returned.get("params_full")
        if not isinstance(params,list) or len(params)!=42 or params!=case["effect"]["params_full"]: raise VerificationError("selected 42-property manifest drift")
        if returned.get("params_sha256")!=case["params_sha256"] or canonical_sha256(params)!=case["params_sha256"]: raise VerificationError("params_sha256 mismatch")
        values={p.get("name"):p.get("value") for p in params};
        if values.get("Blur Mode")!=2: raise VerificationError("Mode 3/4 or unresolved mode entered lane")
        if returned.get("same_comp_control") is not True: raise VerificationError("same-context control missing")
        outputs=returned.get("outputs",{}); mac_control=resolve_artifact(outputs.get("before_effects_control",{}),a.output_dir,"before_effects_control"); mac_effect=resolve_artifact(outputs.get("effect_on",{}),a.output_dir,"effect_on")
        settings=[outputs[k].get("output_module_settings",{}) for k in ("before_effects_control","effect_on")]
        if any(s.get("sha256")!=digest((a.output_dir/Path(s.get("path","")).name)) for s in settings): raise VerificationError("Output Module settings capture missing or unhashed")
        if settings[0].get("serialization")!=settings[1].get("serialization"): raise VerificationError("Output Module settings differ")
        windows=request["case"]["windows_outputs"]
        comparisons={}
        for branch, key in (("before_effects","before_effects_control"),("effect_on","effect_on")):
            expected=ROOT/windows[branch]["path"]
            if digest(expected)!=windows[branch]["sha256"]: raise VerificationError("Windows reference hash drift")
            comparisons[branch]=compare(expected, outputs[key] and (mac_control if key=="before_effects_control" else mac_effect))
        exact=all(row["equal"] for row in comparisons.values())
        report={"kind":"olmkirakira_mode2_32bpc_mac_validation_report","schema_version":1,"status":"raw_float32_exact" if exact else "candidate_return_verified_pending_raw_float32_equality","ae_exact_claim":exact,"case_id":case["id"],"comparisons":comparisons,"reason":"both before-effects control and effect-on semantic FLOAT32 words must match"}
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError, VerificationError) as exc:
        failures.append(str(exc)); report={"kind":"olmkirakira_mode2_32bpc_mac_validation_report","schema_version":1,"status":"fail_closed","ae_exact_claim":False,"failures":failures}
    target=(a.report_json or a.output_dir/"validation_report.json"); target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2)); return 1 if failures else 0


if __name__ == "__main__": raise SystemExit(main())
