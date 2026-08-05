#!/usr/bin/env python3
"""Hash-bound Mac AE PF32 runner for canonical OLMRadialBlur case0009."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from compare_float_exr import read_planes
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
MANIFEST = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/reference_manifest.json"
INSTALLED_BUNDLE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMRadialBlur.plugin"
INSTALLED_BINARY = INSTALLED_BUNDLE / "Contents/MacOS/OLMRadialBlur"
EXPECTED_BINARY_SHA256 = "2e079e3c168666c2f3509f8d4c90ab107301880bce43f538cf4e16bcb8047732"
EXPECTED_INPUT_SHA256 = "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4"
EXPECTED_FRAME_SHA256 = "7de7d9700fddce9f77261fe3e81db8b89ffc88a06c897b866ffe512392562010"
TEMPLATE = "OLM EXR 32 Float"
PARAMS = [
    ("OLM RadialBlur-0001", 1), ("OLM RadialBlur-0002", [960, 540]),
    ("OLM RadialBlur-0004", 1717), ("OLM RadialBlur-0028", 1),
    ("OLM RadialBlur-0029", 0), ("OLM RadialBlur-0005", 0),
    ("OLM RadialBlur-0008", 0), ("OLM RadialBlur-0030", 1),
    ("OLM RadialBlur-0031", 0), ("OLM RadialBlur-0009", 0),
    ("OLM RadialBlur-0026", 1), ("OLM RadialBlur-0012", 1),
    ("OLM RadialBlur-0013", 0), ("OLM RadialBlur-0015", 5),
    ("OLM RadialBlur-0016", 1), ("OLM RadialBlur-0017", 0),
    ("OLM RadialBlur-0019", 0), ("OLM RadialBlur-0020", 1),
    ("OLM RadialBlur-0021", 0),
    ("OLM RadialBlur-0022", 1), ("OLM RadialBlur-0023", 0),
    ("OLM RadialBlur-0024", 10),
    ("ADBE Effect Mask Opacity", 100), ("ADBE Force CPU GPU", 1),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ae_pids() -> list[int]:
    found = subprocess.run(["pgrep", "-x", "After Effects"], capture_output=True, text=True)
    return [int(line) for line in found.stdout.splitlines() if line.strip().isdigit()]


def loaded_radialblur(pid: int) -> list[str]:
    result = subprocess.run(["lsof", "-Fn", "-p", str(pid)], capture_output=True, text=True)
    return [line[1:] for line in result.stdout.splitlines()
            if line.startswith("n/") and line.endswith("/Contents/MacOS/OLMRadialBlur")]


def semantic_rgba_sha256(exr: Path) -> str:
    planes, width, height = read_planes(exr)
    if (width, height) != (1920, 1080):
        raise VerificationError(f"unexpected dimensions {width}x{height}")
    output = bytearray(width * height * 16)
    for pixel in range(width * height):
        dst = pixel * 16
        src = pixel * 4
        for channel, name in enumerate("RGBA"):
            output[dst + channel * 4:dst + channel * 4 + 4] = planes[name][src:src + 4]
    return hashlib.sha256(output).hexdigest()


def jsx(output_dir: Path, result_path: Path) -> str:
    params = json.dumps(PARAMS, separators=(",", ":"))
    return r'''(function(){
function F(m){throw new Error("FAIL_CLOSED: "+m)}
function W(p,o){var f=new File(p);f.encoding="UTF-8";if(!f.open("w"))F("write "+p);f.write(JSON.stringify(o));f.close()}
function H(p){var q="'"+String(p).replace(/'/g,"'\\''")+"'",m=system.callSystem("/usr/bin/shasum -a 256 "+q).match(/^([0-9a-f]{64})/i);if(!m)F("hash "+p);return m[1].toLowerCase()}
function Find(g,n){for(var i=1;i<=g.numProperties;i++){var p=g.property(i);if(p.matchName===n)return p;if(p.numProperties){var q=Find(p,n);if(q)return q}}return null}
function FindRendered(path){var target=new File(path);if(target.exists)return target;var matches=target.parent.getFiles(function(f){return f instanceof File&&f.name.indexOf(target.name)===0});if(matches.length!==1)F("rendered output cardinality "+path+" count="+matches.length);return matches[0]}
var input=new File(INPUT),outDir=OUTPUT,result=RESULT,params=PARAMS;
if(!input.exists)F("input missing");app.newProject();var project=app.project;if(!project)F("new project");project.bitsPerChannel=32;project.linearBlending=false;project.workingSpace="";project.gpuAccelType=GpuAccelType.SOFTWARE;
if(project.bitsPerChannel!==32||project.gpuAccelType!==GpuAccelType.SOFTWARE||project.linearBlending||(project.workingSpace!==""&&project.workingSpace!=="None"))F("project contract");
var footage=project.importFile(new ImportOptions(input)),comp=project.items.addComp("OLMRadialBlur_case0009_pf32",1920,1080,1,1,24),layer=comp.layers.add(footage);
comp.resolutionFactor=[1,1];comp.time=0;
var effect=layer.property("ADBE Effect Parade").addProperty("OLM RadialBlur");if(!effect||effect.matchName!=="OLM RadialBlur")F("effect identity");
var readback=[];for(var i=0;i<params.length;i++){var p=Find(effect,params[i][0]);if(!p)F("missing "+params[i][0]);p.setValue(params[i][1]);if(JSON.stringify(p.value)!==JSON.stringify(params[i][1]))F("readback "+params[i][0]);readback.push([p.matchName,p.value])}if(JSON.stringify(readback)!==JSON.stringify(params))F("aggregate parameter readback");
function Render(enabled,name){effect.enabled=enabled;var rq=project.renderQueue.items.add(comp),om=rq.outputModule(1),path=outDir+"/"+name+".exr";rq.timeSpanStart=comp.time;rq.timeSpanDuration=1/comp.frameRate;om.applyTemplate("OLM EXR 32 Float");om.file=new File(path);var settings=om.getSettings(GetSettingsFormat.STRING);app.project.renderQueue.render();var rendered=FindRendered(path);rq.remove();return {path:rendered.fsName,sha256:H(rendered.fsName),settings:settings}}
var control=Render(false,"control"),effectOn=Render(true,"effect_on");
W(result,{kind:"olmradialblur_case0009_pf32_mac_return",ae_version:app.version,os:$.os,project:{bits_per_channel:project.bitsPerChannel,renderer:"SOFTWARE",working_space:project.workingSpace,linear_blending:project.linearBlending,resolution_factor:comp.resolutionFactor,time:comp.time},plugin:{effect_name:effect.name,effect_match_name:effect.matchName,path:PLUGIN,sha256:PLUGIN_SHA},input:{path:INPUT,sha256:H(INPUT)},params:params,param_readback:readback,outputs:{control:control,effect_on:effectOn}});
try{project.close(CloseOptions.DO_NOT_SAVE_CHANGES)}catch(e){}
}());'''.replace("INPUT", json.dumps(str(INPUT))).replace("OUTPUT", json.dumps(str(output_dir))).replace("RESULT", json.dumps(str(result_path))).replace("PARAMS", params).replace("PLUGIN_SHA", json.dumps(EXPECTED_BINARY_SHA256)).replace("PLUGIN", json.dumps(str(INSTALLED_BINARY)))


def minimal_es3_loader(payload: Path, trace: Path) -> str:
    return (
        "(function(){\n"
        f"var traceFile=new File({json.dumps(str(trace.resolve()))}),payloadFile=new File({json.dumps(str(payload.resolve()))});\n"
        'function append(s){traceFile.encoding="UTF-8";if(traceFile.open("a")){traceFile.writeln(s);traceFile.close();}}\n'
        'append("LOADER_ENTER payload="+payloadFile.fsName);\n'
        'try{$.evalFile(payloadFile);append("LOADER_RETURN");}catch(e){append("LOADER_FAIL error="+e.toString()+" line="+(e.line||0)+" file="+(e.fileName||""));}\n'
        "}());\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    pids = ae_pids()
    modules = {str(pid): loaded_radialblur(pid) for pid in pids}
    installed_hash = sha256(INSTALLED_BINARY) if INSTALLED_BINARY.is_file() else None
    expected_path = str(INSTALLED_BINARY.resolve()) if INSTALLED_BINARY.exists() else None
    exact_mapping = len(pids) == 1 and expected_path is not None and modules.get(str(pids[0])) == [expected_path]
    checks = {
        "input_hash": sha256(INPUT) if INPUT.is_file() else None,
        "input_hash_matches": INPUT.is_file() and sha256(INPUT) == EXPECTED_INPUT_SHA256,
        "manifest_present": MANIFEST.is_file(),
        "installed_binary_hash": installed_hash,
        "installed_binary_hash_matches": installed_hash == EXPECTED_BINARY_SHA256,
        "single_ae_process": len(pids) == 1,
        "loaded_module_paths": modules,
        "loaded_module_is_sole_exact_installed_binary": exact_mapping,
    }
    ready = all((checks["input_hash_matches"], checks["manifest_present"],
                 checks["installed_binary_hash_matches"], checks["single_ae_process"],
                 checks["loaded_module_is_sole_exact_installed_binary"]))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = (args.output_root or ROOT / f"refs/reports/olmradialblur_case0009_pf32_mac_{timestamp}").resolve()
    root.mkdir(parents=True, exist_ok=True)
    report_path, result_path = root / "runner_report.json", root / "ae_return.json"
    report = {"kind": "olmradialblur_case0009_pf32_mac_runner_20260805", "schema": 1,
              "status": "ready" if ready else "restart_required", "checks": checks,
              "expected_internal_frame_sha256": EXPECTED_FRAME_SHA256,
              "run_requested": args.run, "run_executed": False,
              "claim_boundary": {"internal_pf32_exact": False, "mac_ae_rendered": False,
                                   "windows_ae_exact": False}}
    if not ready or not args.run:
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"status": report["status"], "report": str(report_path), "checks": checks}))
        return 2 if not ready else 0
    with tempfile.TemporaryDirectory(prefix="olmradialblur_case0009_pf32_") as temp:
        script = Path(temp) / "payload.jsx"
        loader = Path(temp) / "loader.jsx"
        trace = root / "host_trace.log"
        if trace.exists():
            report["status"] = "stale_host_trace"
            report["validation"] = {"status": "FAIL", "reason": f"refusing to append {trace}"}
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            return 2
        script.write_text(jsx(root, result_path), encoding="utf-8")
        loader.write_text(minimal_es3_loader(script, trace), encoding="utf-8")
        apple = f'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file {json.dumps(str(loader))} with override\n'
        completed = subprocess.run(["osascript"], input=apple, text=True, capture_output=True, timeout=args.timeout)
    report["run_executed"] = True
    report["osascript"] = {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    report["host_trace"] = trace.read_text(encoding="utf-8") if trace.is_file() else None
    if completed.returncode or not result_path.is_file():
        report["status"] = "render_failed"
    else:
        returned = json.loads(result_path.read_text())
        if returned.get("params") != [list(item) for item in PARAMS] or returned.get("param_readback") != [list(item) for item in PARAMS]:
            raise VerificationError("returned parameter contract/readback drifted")
        if returned.get("plugin") != {"effect_name": "OLM RadialBlur", "effect_match_name": "OLM RadialBlur", "path": str(INSTALLED_BINARY), "sha256": EXPECTED_BINARY_SHA256}:
            raise VerificationError("returned effect/plugin identity drifted")
        project = returned.get("project", {})
        if project not in (
            {"bits_per_channel": 32, "renderer": "SOFTWARE", "working_space": "", "linear_blending": False, "resolution_factor": [1, 1], "time": 0},
            {"bits_per_channel": 32, "renderer": "SOFTWARE", "working_space": "None", "linear_blending": False, "resolution_factor": [1, 1], "time": 0},
        ):
            raise VerificationError(f"returned project contract drifted: {project!r}")
        effect_path = Path(returned["outputs"]["effect_on"]["path"])
        control_path = Path(returned["outputs"]["control"]["path"])
        report["exr"] = {"effect_on": inspect_float_rgba_exr(effect_path, (1920, 1080)),
                         "control": inspect_float_rgba_exr(control_path, (1920, 1080))}
        frame_hash = semantic_rgba_sha256(effect_path)
        report["mac_effect_semantic_rgba_sha256"] = frame_hash
        report["mac_matches_internal_actual_aex"] = frame_hash == EXPECTED_FRAME_SHA256
        report["claim_boundary"]["internal_pf32_exact"] = report["mac_matches_internal_actual_aex"]
        report["status"] = "mac_internal_exact" if report["mac_matches_internal_actual_aex"] else "mac_mismatch"
        report["claim_boundary"]["mac_ae_rendered"] = True
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "report": str(report_path)}))
    return 0 if report["status"] == "mac_internal_exact" else 1


if __name__ == "__main__":
    raise SystemExit(main())
