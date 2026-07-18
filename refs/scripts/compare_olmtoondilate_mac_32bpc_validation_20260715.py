#!/usr/bin/env python3
"""Fail-closed ToonDilate Mac/Windows record comparator."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
HELPER_DIRS = (
    SCRIPT_DIR,
    SCRIPT_DIR.parent / "runtime_trace_packages" / "olmtoondilate_mac_32bpc_validation_20260715",
)
for helper_dir in HELPER_DIRS:
    if (helper_dir / "compare_float_exr.py").is_file():
        sys.path.insert(0, str(helper_dir))
        break
else:
    raise SystemExit("compare_float_exr.py is unavailable")

from compare_float_exr import compare

WINDOWS_PLUGIN_SHA = "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"
def read(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def resolve(root, value):
    path = Path(value)
    return path if path.is_absolute() else root / path
def load_expected_mac_plugin_sha(package_root: Path | None):
    package_roots = ((package_root,) if package_root else ()) + HELPER_DIRS
    for root in package_roots:
        manifest = root / "request_manifest.json"
        if manifest.is_file():
            return read(manifest)["case"]["plugin"]["sha256"]
    return None
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("mac"); ap.add_argument("windows"); ap.add_argument("--json",action="store_true"); ap.add_argument("--package", type=Path); a=ap.parse_args()
    left_path, right_path = Path(a.mac).resolve(), Path(a.windows).resolve()
    left,right=read(left_path),read(right_path)
    if {left.get("platform"),right.get("platform")} != {"macos","windows"}: raise SystemExit("comparison requires Mac and Windows records")
    if left.get("fixture_jsx_sha256") != right.get("fixture_jsx_sha256"): raise SystemExit("fixture JSX hash mismatch")
    expected_mac_plugin_sha = load_expected_mac_plugin_sha(a.package.resolve() if a.package else None)
    for record in (left,right):
        if record.get("required_ae_major_minor") != "26.3" or not str(record.get("ae_version", "")).startswith("26.3") or record.get("output_template") != "OLM EXR 32 Float" or record.get("renderer_class") != "SOFTWARE" or record.get("linear_blending") is not False: raise SystemExit("host/AE contract drifted")
        case=record.get("cases");
        if not isinstance(case,list) or len(case)!=1: raise SystemExit("ToonDilate case missing")
        c=case[0]; plugin=c.get("plugin",{}); expected="OLMToonDilate.plugin" if record["platform"]=="macos" else "OLMToonDilate.aex"
        if plugin.get("name") != expected: raise SystemExit("plugin identity/hash drifted")
        plugin_sha = plugin.get("sha256")
        if not isinstance(plugin_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", plugin_sha):
            raise SystemExit("plugin identity/hash drifted")
        if record["platform"] == "macos" and expected_mac_plugin_sha and plugin_sha != expected_mac_plugin_sha:
            raise SystemExit("mac plugin identity/hash drifted")
        if record["platform"] == "windows" and plugin_sha != WINDOWS_PLUGIN_SHA:
            raise SystemExit("windows plugin identity/hash drifted")
        fixture = c.get("fixture_contract",{})
        if fixture.get("project_bits_per_channel")!=32 or fixture.get("working_space")!="None" or fixture.get("linear_blending") is not False or fixture.get("render_policy")!="same comp, only branch enabled state changes" or fixture.get("source_policy")!="AE-generated solids only; no footage imported": raise SystemExit("32bpc/same-context/color contract missing")
        om=c.get("output_module",{})
        if om.get("template_name")!="OLM EXR 32 Float" or om.get("capture_api")!="OutputModule.getSettings(GetSettingsFormat.STRING)" or not om.get("settings_sha256"): raise SystemExit("Output Module capture missing")
    mc,wc=left["cases"][0],right["cases"][0]; rows={}
    for name in ("no_effect","effect_on"):
        lp=resolve(left_path.parent, mc["outputs"][name]["path"]); rp=resolve(right_path.parent, wc["outputs"][name]["path"])
        if not lp.is_file() or not rp.is_file(): raise SystemExit("FLOAT EXR output missing: "+name)
        for path, row in ((lp, mc["outputs"][name]), (rp, wc["outputs"][name])):
            stated = row.get("sha256")
            if not isinstance(stated, str) or sha(path) != stated: raise SystemExit("artifact SHA-256 mismatch: "+name)
        result=compare(lp,rp)
        if result.get("mismatched_values", 1) != 0: raise SystemExit("raw FLOAT EXR mismatch: "+name)
        rows[name]=result
    output={"status":"pass","ae_exact":True,"comparison":"raw_float_bits_exact","case_id":mc["id"],"outputs":rows}
    print(json.dumps(output,sort_keys=True) if a.json else "PASS: ToonDilate Mac/Windows raw FLOAT EXR exact")
if __name__=="__main__": main()
