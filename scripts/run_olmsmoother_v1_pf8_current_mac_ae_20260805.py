#!/usr/bin/env python3
"""Audit or explicitly run the hash-bound OLMSmoother v1 PF8 Mac AE fixture.

Without ``--run`` this is read-only with respect to After Effects.  A render is
allowed only when one already-running AE process maps the exact installed
Mach-O pinned by the request.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "refs/mac_validation_requests/olmsmoother_v1_pf8_current_ae_host_20260805.json"
DEFAULT_REPORT = ROOT / "refs/conformance/olmsmoother_v1_pf8_current_ae_host_preflight_20260805.json"
EXPECTED_REQUEST_SHA256 = "f06bbc6af35cceab2cf82d75e865f4afef42a3b1db5998e407a47d6474ef7f94"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decoded_rgba(path: Path) -> tuple[str, list[int]]:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        return hashlib.sha256(rgba.tobytes()).hexdigest(), list(rgba.size)


def ae_pids() -> list[int]:
    proc = subprocess.run(["pgrep", "-x", "After Effects"], text=True,
                          capture_output=True, check=False)
    return [int(value) for value in proc.stdout.split() if value.isdigit()]


def loaded_paths(pid: int) -> list[str]:
    proc = subprocess.run(["lsof", "-Fn", "-p", str(pid)], text=True,
                          capture_output=True, check=False)
    return sorted(set(
        line[1:] for line in proc.stdout.splitlines()
        if line.startswith("n/") and line.endswith("/Contents/MacOS/OLMSmoother")
    ))


def architectures(binary: Path) -> list[str]:
    proc = subprocess.run(["lipo", "-archs", str(binary)], text=True,
                          capture_output=True, check=False)
    return sorted(proc.stdout.split()) if proc.returncode == 0 else []


def deployment_targets(binary: Path) -> list[str]:
    proc = subprocess.run(["otool", "-l", str(binary)], text=True,
                          capture_output=True, check=False)
    return sorted(set(re.findall(r"^\s+minos\s+(\S+)$", proc.stdout, re.MULTILINE)))


def codesign_valid(bundle: Path) -> bool:
    proc = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(bundle)],
                          capture_output=True, check=False)
    return proc.returncode == 0


def jsx_source(spec: dict, output: Path) -> str:
    payload = json.dumps(spec, separators=(",", ":"), ensure_ascii=False)
    root = json.dumps(str(ROOT))
    out = json.dumps(str(output))
    return r'''(function(){
var S=SPEC,ROOT=ROOT_PATH,OUT=OUTPUT_PATH;
function F(m){throw new Error("FAIL_CLOSED: "+m)}
function Q(v){var q=String.fromCharCode(39);return q+String(v).split(q).join(q+String.fromCharCode(92)+q+q)+q}
function J(v){return "\""+String(v).replace(/\\/g,"\\\\").replace(/\"/g,"\\\"").replace(/\r/g,"\\r").replace(/\n/g,"\\n")+"\""}
function H(p){var m=system.callSystem("/usr/bin/shasum -a 256 "+Q(p)).match(/^([0-9a-f]{64})/i);if(!m)F("hash "+p);return m[1].toLowerCase()}
function W(p,text){var f=new File(p);if(f.exists)F("stale "+p);f.encoding="UTF-8";if(!f.open("w"))F("write "+p);if(!f.write(text+"\n")){f.close();F("write body "+p)}if(!f.close())F("close "+p)}
function L(text){var f=new File(OUT+"/host_trace.log");f.encoding="UTF-8";if(f.open("a")){f.write(String(text)+"\n");f.close()}}
function SameParam(x,a){var b=x.value;if(x.match_name==="OLM Smoother-0002"){if(!(a instanceof Array)||!(b instanceof Array)||a.length<3||b.length<3)return false;for(var i=0;i<3;i++)if(Math.round(Number(a[i])*255)!==Math.round(Number(b[i])*255))return false;return true}return Number(a)===Number(b)}
function Find(g,n){for(var i=1;i<=g.numProperties;i++){var p=g.property(i);if(p.matchName===n)return p;if(p.numProperties){var x=Find(p,n);if(x)return x}}return null}
function SetParams(e,c){for(var i=0;i<c.params.length;i++){var x=c.params[i],p=Find(e,x.match_name);if(!p||p.name!==x.name||p.propertyIndex!==x.property_index)F("param identity "+x.match_name);p.setValue(x.value);if(!SameParam(x,p.value))F("param readback "+x.match_name);if(x.match_name==="OLM Smoother-0002")L("color rgb8 "+Math.round(Number(p.value[0])*255)+","+Math.round(Number(p.value[1])*255)+","+Math.round(Number(p.value[2])*255))}return true}
function Render(comp,e,on,name){L("render "+name);e.enabled=on;var f=new File(OUT+"/"+name+".png");if(f.exists)F("stale render "+f.fsName);comp.saveFrameToPng(0,f);for(var i=0;i<1800&&!f.exists;i++){$.sleep(100);f=new File(f.fsName)}if(!f.exists)F("missing render "+name);return {path:f.fsName,file_sha256:H(f.fsName),effect_enabled:on}}
try{
var binary=new File(S.plugin.binary);if(!binary.exists||H(binary.fsName)!==S.plugin.required_binary_sha256)F("binary identity");
L("binary exact");
if(app.project){try{app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES)}catch(e){F("close previous project "+e)}}
L("previous project closed");
var pr=app.newProject();if(!pr)F("new project");pr.bitsPerChannel=8;pr.linearBlending=false;pr.workingSpace="";try{pr.gpuAccelType=GpuAccelType.SOFTWARE}catch(e){F("SOFTWARE "+e)}
var ws=pr.workingSpace;if(pr.bitsPerChannel!==8||Number(pr.gpuAccelType)!==1816||pr.linearBlending||(String(ws)!==""&&String(ws)!=="None"))F("project contract");
L("project exact");
var rows=[];
for(var i=0;i<S.cases.length;i++){var c=S.cases[i],input=new File(ROOT+"/"+c.input.path);if(!input.exists||H(input.fsName)!==c.input.file_sha256)F("input "+c.id);var ft=pr.importFile(new ImportOptions(input));try{ft.mainSource.alphaMode=AlphaMode.STRAIGHT}catch(e){F("alpha "+c.id)}var co=pr.items.addComp(c.id,c.dimensions[0],c.dimensions[1],1,1,24),ly=co.layers.add(ft),e=ly.property("ADBE Effect Parade").addProperty("OLM Smoother");if(!e||e.name!=="OLM Smoother"||e.matchName!=="OLM Smoother")F("effect identity "+c.id);SetParams(e,c);rows.push({id:c.id,comp:co,effect:e});L("case exact "+c.id)}
var projectPath=OUT+"/"+S.project_fixture.generated_filename,projectFile=new File(projectPath);if(projectFile.exists)F("stale project");pr.save(projectFile);if(!projectFile.exists)F("project save");
for(var j=0;j<rows.length;j++){var r=rows[j];Render(r.comp,r.effect,false,r.id+"__no_effect");Render(r.comp,r.effect,true,r.id+"__effect_on")}
var ids=[];for(var k=0;k<rows.length;k++)ids.push(J(rows[k].id));
var resultText="{\"kind\":\"olmsmoother_v1_pf8_current_ae_host_return\",\"schema_version\":1,\"ae_version\":"+J(app.version)+",\"plugin_sha256\":\""+H(binary.fsName)+"\",\"project_sha256\":\""+H(projectFile.fsName)+"\",\"case_ids\":["+ids.join(",")+"]}";
W(OUT+"/ae_return.json",resultText);
L("return written");
try{pr.close(CloseOptions.DO_NOT_SAVE_CHANGES)}catch(e){}
}catch(runError){L("ERROR "+runError.toString()+" line="+String(runError.line));throw runError}
}());'''.replace("SPEC", payload).replace("ROOT_PATH", root).replace("OUTPUT_PATH", out)


def audit(spec: dict) -> tuple[dict, bool]:
    bundle = Path(spec["plugin"]["bundle"])
    binary = Path(spec["plugin"]["binary"])
    ae = Path(spec["target_application"]["executable"])
    checks: dict[str, object] = {
        "request_sha256": sha256(REQUEST),
        "request_hash_matches": sha256(REQUEST) == EXPECTED_REQUEST_SHA256,
        "ae_executable_hash_matches": ae.is_file() and sha256(ae) == spec["target_application"]["executable_sha256"],
        "installed_binary_sha256": sha256(binary) if binary.is_file() else None,
        "installed_binary_hash_matches": binary.is_file() and sha256(binary) == spec["plugin"]["required_binary_sha256"],
        "architectures": architectures(binary) if binary.is_file() else [],
        "architectures_match": set(architectures(binary)) == set(spec["plugin"]["required_architectures"]) if binary.is_file() else False,
        "deployment_targets": deployment_targets(binary) if binary.is_file() else [],
        "deployment_target_matches": deployment_targets(binary) == [spec["plugin"]["required_deployment_target"]] if binary.is_file() else False,
        "codesign_deep_strict": bundle.is_dir() and codesign_valid(bundle),
    }
    refs_ok = True
    for row in spec["reference_manifests"]:
        path = ROOT / row["path"]
        refs_ok &= path.is_file() and sha256(path) == row["sha256"]
    checks["reference_manifests_match"] = refs_ok
    cases = {}
    for case in spec["cases"]:
        case_checks = {}
        for role in ("input", "windows_expected"):
            item = case[role]
            path = ROOT / item["path"]
            decoded, size = decoded_rgba(path) if path.is_file() else (None, None)
            case_checks[role] = {
                "file_sha256": sha256(path) if path.is_file() else None,
                "file_hash_matches": path.is_file() and sha256(path) == item["file_sha256"],
                "decoded_rgba_sha256": decoded,
                "decoded_hash_matches": decoded == item["decoded_rgba_sha256"],
                "dimensions": size,
                "dimensions_match": size == case["dimensions"],
            }
        cases[case["id"]] = case_checks
    checks["cases"] = cases
    static_ok = all(bool(checks[key]) for key in (
        "request_hash_matches", "ae_executable_hash_matches", "installed_binary_hash_matches",
        "architectures_match", "deployment_target_matches", "codesign_deep_strict",
        "reference_manifests_match",
    )) and all(all(all(v for k, v in role.items() if k.endswith("_matches"))
                       for role in row.values()) for row in cases.values())
    return checks, static_ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="operate one already-running, hash-bound AE process")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    spec = json.loads(REQUEST.read_text(encoding="utf-8"))
    checks, static_ok = audit(spec)
    pids = ae_pids()
    mappings = {str(pid): loaded_paths(pid) for pid in pids}
    expected_path = str(Path(spec["plugin"]["binary"]).resolve())
    mapped = len(pids) == 1 and mappings.get(str(pids[0])) == [expected_path]
    status = "ready" if static_ok and mapped else ("ae_restart_required" if static_ok else "artifact_identity_failed")
    report = {
        "kind": "olmsmoother_v1_pf8_current_ae_host_preflight",
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "ae_exact_claim": False,
        "run_requested": args.run,
        "run_executed": False,
        "harness": {
            "runner": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
            "request": {"path": str(REQUEST), "sha256": sha256(REQUEST)},
        },
        "checks": checks,
        "after_effects": {"pids": pids, "loaded_olmsmoother_paths": mappings, "exact_current_mapping": mapped},
        "target_cases": [case["id"] for case in spec["cases"]],
        "pf16_aexcompat_boundary_preserved": True,
    }
    if not args.run:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": status, "report": str(args.report)}))
        return 0 if static_ok else 1
    if status != "ready" or args.output_dir is None:
        print("[FAIL_CLOSED] --run requires --output-dir and one AE process mapping the pinned binary")
        return 2
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        print("[FAIL_CLOSED] output directory must be empty")
        return 1
    jsx = output / "olmsmoother_v1_pf8_host_fixture.jsx"
    jsx.write_text(jsx_source(spec, output), encoding="utf-8")
    apple = (f'if application "Adobe After Effects 2026" is not running then error "AE not running"\n'
             f'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file {json.dumps(str(jsx))} with override\n')
    completed = subprocess.run(["osascript"], input=apple, text=True, capture_output=True,
                               timeout=args.timeout, check=False)
    report["run_executed"] = True
    report["osascript"] = {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    result_path = output / "ae_return.json"
    exact = completed.returncode == 0 and result_path.is_file()
    comparisons = {}
    if exact:
        try:
            returned = json.loads(result_path.read_text(encoding="utf-8"))
            by_id = {case["id"]: case for case in spec["cases"]}
            if returned.get("kind") != "olmsmoother_v1_pf8_current_ae_host_return":
                raise ValueError("returned kind mismatch")
            if returned.get("case_ids") != list(by_id):
                raise ValueError("returned case set mismatch")
            if returned.get("plugin_sha256") != spec["plugin"]["required_binary_sha256"]:
                raise ValueError("returned plugin hash mismatch")
            project_path = output / spec["project_fixture"]["generated_filename"]
            if not project_path.is_file() or sha256(project_path) != returned.get("project_sha256"):
                raise ValueError("returned project identity mismatch")
            report["ae_return"] = returned
            for case_id, expected in by_id.items():
                comparisons[case_id] = {}
                for role, target in (("no_effect", expected["input"]), ("effect_on", expected["windows_expected"])):
                    path = output / f"{case_id}__{role}.png"
                    decoded, size = decoded_rgba(path)
                    ok = size == expected["dimensions"] and decoded == target["decoded_rgba_sha256"]
                    comparisons[case_id][role] = {"path": str(path), "file_sha256": sha256(path),
                                                   "decoded_rgba_sha256": decoded, "exact": ok}
                    exact &= ok
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
            exact = False
            report["return_error"] = str(error)
    post_pids = ae_pids()
    post_mapping = {str(pid): loaded_paths(pid) for pid in post_pids}
    post_identity = post_pids == pids and len(post_pids) == 1 and post_mapping.get(str(post_pids[0])) == [expected_path]
    exact &= post_identity and sha256(Path(spec["plugin"]["binary"])) == spec["plugin"]["required_binary_sha256"]
    report["post_render"] = {"pids": post_pids, "loaded_paths": post_mapping, "identity_unchanged": post_identity,
                              "comparisons": comparisons}
    report["status"] = "pass" if exact else "fail_closed"
    report["ae_exact_claim"] = exact
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(args.report)}))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
