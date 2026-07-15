#!/usr/bin/env python3
"""Run the bounded two-case OLM RadialBlur Mac FLOAT EXR validation lane."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "refs/mac_validation_requests/olmradialblur_32bpc_mac_validation_20260715.json"
AUDIT = ROOT / "refs/conformance/olmradialblur_32bpc_float_evidence_audit_20260715.json"
STEM = "olmradialblur_32bpc_mac_validation_20260715"
TEMPLATE = "OLM EXR 32 Float"
CAPTURE_API = "OutputModule.getSettings(GetSettingsFormat.STRING)"
MATCH_NAMES = [
    "OLM RadialBlur-0001", "OLM RadialBlur-0002", "OLM RadialBlur-0004",
    "OLM RadialBlur-0028", "OLM RadialBlur-0029", "OLM RadialBlur-0005",
    "OLM RadialBlur-0008", "OLM RadialBlur-0030", "OLM RadialBlur-0031",
    "OLM RadialBlur-0009", "OLM RadialBlur-0026", "OLM RadialBlur-0012",
    "OLM RadialBlur-0013", "OLM RadialBlur-0015", "OLM RadialBlur-0016",
    "OLM RadialBlur-0017", "OLM RadialBlur-0019", "OLM RadialBlur-0020",
    "OLM RadialBlur-0022", "OLM RadialBlur-0023", "OLM RadialBlur-0024",
    "ADBE Effect Mask Opacity", "ADBE Force CPU GPU",
]
PROPERTY_INDICES = [1, 2, 4, 5, 6, 7, 10, 11, 12, 13, 15, 17, 18, 20, 21, 22, 24, 25, 27, 28, 29, 2, 3]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def load_request() -> dict[str, Any]:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    if request.get("status") != "blocked_pending_mac_noop_control" or request.get("ae_exact_claim") is not False:
        raise ValueError("request status/claim drifted")
    if [c["id"] for c in request.get("cases", [])] != ["final_random10_olm_radialblur_01", "final_random10_olm_radialblur_02"]:
        raise ValueError("selected case set/order drifted")
    if audit.get("smallest_fully_pinned_candidate", {}).get("case_ids") != [c["id"] for c in request["cases"]]:
        raise ValueError("request does not match audit candidate")
    return request


def enrich_case(case: dict[str, Any]) -> dict[str, Any]:
    values = list(case["params"].items())
    if len(values) != len(MATCH_NAMES):
        raise ValueError(f"{case['id']}: parameter count drifted")
    params = []
    for property_index, ((name, value), match_name) in zip(PROPERTY_INDICES, zip(values, MATCH_NAMES)):
        params.append({"name": name, "match_name": match_name, "property_index": property_index, "value": value})
    return {**case, "params_full": params, "params_sha256": canonical_sha256(params)}


def jsx_source(cases: list[dict[str, Any]]) -> str:
    payload = json.dumps(cases, ensure_ascii=True, separators=(",", ":"))
    return r'''(function () {
var CASES = CASES_JSON, TEMPLATE = "OLM EXR 32 Float", CAPTURE_API = "OutputModule.getSettings(GetSettingsFormat.STRING)";
function fail(m) { throw new Error("FAIL_CLOSED: " + m); }
function env(n) { try { return $.getenv(n) || ""; } catch (e) { return ""; } }
function stable(v) { if (v === null) return "null"; if (typeof v === "string") return '"'+String(v).replace(/\\/g,"\\\\").replace(/"/g,'\\"')+'"'; if (typeof v === "number") { if (!isFinite(v)) fail("non-finite"); return String(v); } if (typeof v === "boolean") return v?"true":"false"; if (v instanceof Array) { var a=[]; for(var i=0;i<v.length;i++) a.push(stable(v[i])); return "["+a.join(",")+"]"; } if (typeof v === "object") { var k=[],o=[]; for(var n in v) if(v.hasOwnProperty(n)) k.push(n); k.sort(); for(var j=0;j<k.length;j++) o.push(stable(k[j])+":"+stable(v[k[j]])); return "{"+o.join(",")+"}"; } fail("unsupported value"); }
function write(p,t) { var f=new File(p); f.encoding="UTF-8"; if(!f.open("w")) fail("cannot write "+p); f.write(t); f.close(); }
function shell(c) { return system.callSystem(c).replace(/[\r\n]+$/g,""); }
function sq(p) { return "'"+String(p).replace(/'/g,"'\\''")+"'"; }
function hash(p) { var m=shell("/usr/bin/shasum -a 256 "+sq(p)).match(/^([0-9a-fA-F]{64})\s/); if(!m) fail("cannot hash "+p); return m[1].toLowerCase(); }
function find(group, match) { for(var i=1;i<=group.numProperties;i++){var p=group.property(i); if(p.matchName===match)return p; if(p.numProperties>0){var q=find(p,match);if(q)return q;}} return null; }
function setParams(effect, params) { for(var i=0;i<params.length;i++){var x=params[i],p=find(effect,x.match_name);if(!p)fail("missing "+x.match_name);p.setValue(x.value);} }
function capture(module, path) { if(!module.getSettings || typeof GetSettingsFormat==="undefined" || typeof GetSettingsFormat.STRING==="undefined")fail("settings API unavailable"); var s=module.getSettings(GetSettingsFormat.STRING); if(!s)fail("empty output settings"); var side=path.replace(/\.exr$/i,".output_module_settings.json"); write(side,stable({kind:"olm_output_module_settings_capture",template:TEMPLATE,capture_api:CAPTURE_API,settings:s})+"\n"); return {path:side,sha256:hash(side),serialization:stable(s)}; }
function render(comp,effect,enabled,outDir,name){effect.enabled=enabled;var item=app.project.renderQueue.items.add(comp);item.timeSpanStart=0;item.timeSpanDuration=1.0/comp.frameRate;var om=item.outputModule(1);om.applyTemplate(TEMPLATE);var path=outDir+"/"+name+".exr";var settings=capture(om,path);om.file=new File(path);app.project.renderQueue.render();if(!new File(path).exists)fail("missing "+path);var out={path:path,sha256:hash(path),output_module_settings:settings};item.remove();return out;}
var inputDir=env("OLM_AE_MAC_INPUT_DIR"),outDir=env("OLM_AE_MAC_OUTPUT_DIR"),resultPath=env("OLM_AE_MAC_RESULT_JSON"),pluginPath=env("OLM_AE_MAC_PLUGIN_PATH");if(!inputDir||!outDir||!resultPath||!pluginPath)fail("required environment missing");
var plugin=new File(pluginPath);if(!plugin.exists||plugin.name!=="OLMRadialBlur.plugin")fail("plugin identity mismatch");var loaded={filename:plugin.name,path:plugin.fsName,sha256:hash(plugin.fsName)};
var project=app.newProject();project.bitsPerChannel=32;project.linearBlending=false;try{project.gpuAccelType=GpuAccelType.SOFTWARE;}catch(e){fail("cannot set SOFTWARE");}if(Number(project.bitsPerChannel)!==32||String(project.gpuAccelType).toUpperCase()!=="SOFTWARE")fail("project contract mismatch");
var returned=[];for(var ci=0;ci<CASES.length;ci++){var spec=CASES[ci],input=new File(inputDir+"/"+spec.input_name);if(!input.exists)fail("missing input "+spec.id);var footage=project.importFile(new ImportOptions(input));var comp=project.items.addComp(spec.id,1920,1080,1,1,24);var layer=comp.layers.add(footage);var effect=layer.property("ADBE Effect Parade").addProperty("OLM RadialBlur");if(!effect||effect.matchName!=="OLM RadialBlur")fail("effect identity mismatch "+spec.id);setParams(effect,spec.params_full);var control=render(comp,effect,false,outDir,spec.id+"__no_effect_control"),on=render(comp,effect,true,outDir,spec.id+"__effect_on");if(control.output_module_settings.serialization!==on.output_module_settings.serialization)fail("output settings differ "+spec.id);returned.push({id:spec.id,blur_type:spec.blur_type,input:{path:spec.input_exr,sha256:spec.input_sha256},params_full:spec.params_full,params_sha256:spec.params_sha256,outputs:{no_effect_control:control,effect_on:on},no_effect_control_passed:true});}
write(resultPath,stable({kind:"olmradialblur_32bpc_mac_validation_return",schema_version:1,status:"candidate_return_only",ae_exact_claim:false,platform:"macOS",host:{os:$.os,ae_version:app.version},project:{bits_per_channel:project.bitsPerChannel,renderer:"SOFTWARE",working_space:project.workingSpace,linear_blending:project.linearBlending,frame:0,frame_rate:24},output_module:{template_name:TEMPLATE,capture_api:CAPTURE_API,format:"OpenEXR",compression:"uncompressed scanline",channels:["A","B","G","R"],sample_type:"FLOAT",dimensions:[1920,1080]},loaded_plugin:loaded,cases:returned})+"\n");try{project.close(CloseOptions.DO_NOT_SAVE_CHANGES);}catch(e){}
}());
'''.replace("CASES_JSON", payload)


def prepare(support: Path) -> tuple[dict[str, Any], Path]:
    request = load_request()
    support.mkdir(parents=True, exist_ok=True)
    input_dir = support / "input"
    input_dir.mkdir(exist_ok=True)
    cases = []
    for raw in request["cases"]:
        source = ROOT / raw["input_exr"]
        if not source.is_file() or sha256(source) != raw["input_sha256"]:
            raise ValueError(f"input missing or hash mismatch: {raw['id']}")
        name = source.name
        (input_dir / name).write_bytes(source.read_bytes())
        case = enrich_case(raw)
        cases.append({**case, "input_name": name})
    (support / "request_manifest.json").write_text(json.dumps({"request": request, "cases": cases}, indent=2) + "\n", encoding="utf-8")
    jsx = support / "run_mac_olmradialblur_32bpc_validation.jsx"
    jsx.write_text(jsx_source(cases), encoding="utf-8")
    return request, jsx


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plugin-path", type=Path, required=True)
    ap.add_argument("--support-dir", type=Path)
    ap.add_argument("--output-dir", type=Path)
    ap.add_argument("--result-json", type=Path)
    ap.add_argument("--dump-js", type=Path)
    ap.add_argument("--app-name", default="Adobe After Effects 2026")
    ap.add_argument("--timeout", type=int, default=7200)
    args = ap.parse_args()
    if args.plugin_path.name != "OLMRadialBlur.plugin" or not args.plugin_path.is_file():
        print("[FAIL_CLOSED] --plugin-path must name an existing OLMRadialBlur.plugin", file=sys.stderr); return 2
    support = (args.support_dir or Path(tempfile.mkdtemp(prefix=STEM + "_"))).resolve()
    output = (args.output_dir or support / "return").resolve(); output.mkdir(parents=True, exist_ok=True)
    result = (args.result_json or output / "mac_validation_return.json").resolve()
    try: _, jsx = prepare(support)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL_CLOSED] {exc}", file=sys.stderr); return 1
    env = {"OLM_AE_MAC_INPUT_DIR": str((support / "input").resolve()), "OLM_AE_MAC_OUTPUT_DIR": str(output), "OLM_AE_MAC_RESULT_JSON": str(result), "OLM_AE_MAC_PLUGIN_PATH": str(args.plugin_path.resolve())}
    wrapper = support / "run_mac_wrapper.jsx"
    wrapper.write_text("\n".join(f"$.setenv({json.dumps(k)},{json.dumps(v)});" for k,v in env.items()) + f"\n$.evalFile(new File({json.dumps(str(jsx))}));\n", encoding="utf-8")
    if args.dump_js:
        args.dump_js.parent.mkdir(parents=True, exist_ok=True); args.dump_js.write_text(wrapper.read_text(encoding="utf-8"), encoding="utf-8"); print(f"[OK] wrote {args.dump_js}"); return 0
    script = f'tell application {json.dumps(args.app_name)} to DoScriptFile POSIX file {json.dumps(str(wrapper))} with override\n'
    try: proc = subprocess.run(["osascript"], input=script, text=True, capture_output=True, timeout=args.timeout)
    except (OSError, subprocess.TimeoutExpired): print("[FAIL_CLOSED] AE did not produce a return", file=sys.stderr); return 1
    if proc.returncode != 0 or not result.is_file(): print("[FAIL_CLOSED] AE did not produce a return", file=sys.stderr); return 1
    report = subprocess.run([sys.executable, str(ROOT / "scripts/report_olmradialblur_32bpc_mac_validation_20260715.py"), str(result), "--output-dir", str(output)], text=True)
    if report.returncode: print("[FAIL_CLOSED] candidate return failed report validation", file=sys.stderr); return 1
    print(f"[OK] candidate return: {result}"); return 0


if __name__ == "__main__": raise SystemExit(main())
