#!/usr/bin/env python3
"""Validate a DirectionalBlur Mac return and optionally compare a Windows pair."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "refs/mac_validation_requests/olmdirectionalblur_32bpc_mac_validation_20260715.json"
PLUGIN = "OLMDirectionalBlur.plugin"


def digest(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()


def words(path: Path) -> list[int]:
    raw = path.read_bytes(); attrs, end = _header(raw); info = _info(attrs, path)
    if info["compression"] != 0 or any(c["sample_type"] != 2 for c in info["channels"]): raise VerificationError(f"{path}: not raw FLOAT scanlines")
    width, height, channels = info["width"], info["height"], len(info["channels"]); table_end = end + height * 8; offsets = struct.unpack_from("<" + "Q" * height, raw, end); result=[]
    for offset in offsets:
        _, size = struct.unpack_from("<iI", raw, offset); result.extend(struct.unpack_from("<" + "I" * (size // 4), raw, offset + 8))
    if len(result) != width * height * channels: raise VerificationError(f"{path}: incomplete image")
    return result


def _header(raw: bytes):
    if len(raw) < 8 or struct.unpack_from("<I", raw)[0] != 20000630: raise VerificationError("not OpenEXR")
    p=8; attrs={}
    while True:
        end=raw.index(b"\0",p); name=raw[p:end].decode(); p=end+1
        if not name:return attrs,p
        end=raw.index(b"\0",p); typ=raw[p:end].decode(); p=end+1; size=struct.unpack_from("<I",raw,p)[0]; p+=4; attrs[name]=(typ,raw[p:p+size]); p+=size


def _info(attrs, path):
    typ, raw = attrs["channels"]; p=0; channels=[]
    while raw[p]:
        end=raw.index(b"\0",p); name=raw[p:end].decode(); p=end+1; sample_type,_,xs,ys=struct.unpack_from("<iB3xii",raw,p); p+=16; channels.append({"name":name,"sample_type":sample_type,"x":xs,"y":ys})
    _, box=attrs["dataWindow"]; x0,y0,x1,y1=struct.unpack("<4i",box); _, comp=attrs["compression"]
    if [c["name"] for c in channels] != ["A","B","G","R"]: raise VerificationError(f"{path}: channel order drift")
    return {"width":x1-x0+1,"height":y1-y0+1,"channels":channels,"compression":comp[0]}


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("return_json",type=Path); ap.add_argument("--output-dir",type=Path); ap.add_argument("--windows-manifest",type=Path); args=ap.parse_args()
    request=json.loads(REQUEST.read_text(encoding="utf-8")); data=json.loads(args.return_json.read_text(encoding="utf-8")); out=(args.output_dir or args.return_json.parent).resolve(); failures=[]
    if data.get("kind") != "olmdirectionalblur_32bpc_mac_validation_return": failures.append("wrong return kind")
    if data.get("ae_exact_claim") is not False: failures.append("ae_exact_claim must be false")
    if not str(data.get("ae_version", "")).startswith(request["ae_contract"]["major_minor"]): failures.append("AE version drift")
    if data.get("project") != {"bits_per_channel":32,"renderer":"SOFTWARE","working_space":"None","linear_blending":False}: failures.append("project contract drift")
    if data.get("output_module",{}).get("template_name") != "OLM EXR 32 Float" or data.get("output_module",{}).get("capture_api") != "OutputModule.getSettings(GetSettingsFormat.STRING)": failures.append("output module contract drift")
    plugin=data.get("loaded_plugin",{}); pp=Path(plugin.get("path",""))
    if plugin.get("filename") != PLUGIN or len(plugin.get("sha256","")) != 64 or plugin.get("expected_sha256") != plugin.get("sha256") or not pp.is_file() or digest(pp) != plugin.get("sha256"): failures.append("loaded plugin hash missing or mismatched")
    case=(data.get("cases") or [{}])[0]
    if len(data.get("cases",[])) != 1 or case.get("id") != request["case"]["id"] or case.get("input",{}).get("sha256") != request["case"]["input"]["sha256"]: failures.append("case/input identity drift")
    if case.get("params") != request["case"]["effect"]["params"]: failures.append("parameter identity drift")
    outputs=case.get("outputs",{}); mac_words={}
    setting_serial=[]
    for branch in ("no_effect","effect_on"):
        item=outputs.get(branch,{}) ; path=Path(item.get("path","")); path=path if path.is_absolute() else out/path.name
        if not path.is_file(): failures.append(f"missing {branch} EXR"); continue
        if item.get("sha256") != digest(path): failures.append(f"{branch} hash mismatch")
        try: inspect_float_rgba_exr(path,(1920,1080)); mac_words[branch]=words(path)
        except (VerificationError,OSError,ValueError) as exc: failures.append(f"{branch} EXR contract: {exc}")
        settings=item.get("output_module_settings",{}); sp=Path(settings.get("path","")); sp=sp if sp.is_absolute() else out/sp.name
        if not sp.is_file() or settings.get("sha256") != digest(sp): failures.append(f"{branch} Output Module capture missing/hash mismatch")
        setting_serial.append(settings.get("serialization"))
    if len(setting_serial)==2 and setting_serial[0] != setting_serial[1]: failures.append("control/effect Output Module settings differ")
    comparison={"status":"not_run","equal":False,"reason":"Windows manifest/control is missing; exactness remains prohibited"}
    if args.windows_manifest:
        try:
            win=json.loads(args.windows_manifest.read_text(encoding="utf-8")); wc=win.get("no_effect") or win.get("windows_no_effect") or {}; we=win.get("effect_on") or win.get("windows_effect") or {}
            for label,item,branch in (("windows_no_effect",wc,"no_effect"),("windows_effect_on",we,"effect_on")):
                p=Path(item.get("path","")); p=p if p.is_absolute() else args.windows_manifest.parent/p
                if not p.is_file() or item.get("sha256") != digest(p): raise VerificationError(f"{label}: missing/hash mismatch")
                inspect_float_rgba_exr(p,(1920,1080)); delta=sum(a!=b for a,b in zip(words(p),mac_words[branch]))
                comparison[label]={"raw_float32_word_delta":delta};
                if delta: raise VerificationError(f"{label}: raw FLOAT32 word delta {delta}")
            comparison={"status":"pass","equal":True,"raw_float32_word_delta":0}
        except (OSError,KeyError,ValueError,VerificationError) as exc: failures.append(f"cross-host comparison: {exc}"); comparison["reason"]=str(exc)
    status="candidate_return_verified" if not failures else "fail_closed_pending"
    report={"kind":"olmdirectionalblur_32bpc_mac_validation_report","schema_version":1,"status":status,"ae_exact_claim":False,"case_id":request["case"]["id"],"failures":failures,"raw_float32_comparison":comparison,"next_gate":"supply Windows effect/control manifest and require zero raw FLOAT32 word deltas"}
    target=out/"validation_report.json"; target.write_text(json.dumps(report,indent=2,ensure_ascii=True)+"\n",encoding="utf-8"); print(("[OK]" if not failures else "[FAIL_CLOSED]")+f" wrote {target}"); return 0 if not failures else 2


if __name__ == "__main__": raise SystemExit(main())
