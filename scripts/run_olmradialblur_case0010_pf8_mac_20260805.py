#!/usr/bin/env python3
"""Hash-bound Mac AE Software/PF8 runner for OLMRadialBlur case0010.

The runner intentionally refuses to render until one already-running After
Effects process has mapped the exact installed executable pinned below.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur"
INPUT = REFERENCE_DIR / "case_0010_before_effects.png"
REFERENCE = REFERENCE_DIR / "case_0010.png"
MANIFEST = REFERENCE_DIR / "reference_manifest.json"
INSTALLED_BUNDLE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMRadialBlur.plugin"
INSTALLED_BINARY = INSTALLED_BUNDLE / "Contents/MacOS/OLMRadialBlur"

EXPECTED_BINARY_SHA256 = "2e079e3c168666c2f3509f8d4c90ab107301880bce43f538cf4e16bcb8047732"
EXPECTED_INPUT_SHA256 = "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4"
EXPECTED_REFERENCE_SHA256 = "6d54dcfcd073b0cd1d90be2a9dcf020fb5d852a6a963e0246e521cc882d9960c"
EXPECTED_MANIFEST_SHA256 = "7ec542fad64cc210474c6309c3e48c9f12bd0885f54d31943da873d94024b565"
OUTPUT_TEMPLATE = "PNG Sequence"
WITNESSES = {(1612, 6): [5, 5, 5, 255], (1614, 6): [255, 255, 255, 255]}

# All readable values recorded for the sole case0010 effect. This includes the
# two AE-owned effect controls, so the live readback is not a narrowed subset.
PARAMS: list[tuple[str, Any]] = [
    ("OLM RadialBlur-0001", 2), ("OLM RadialBlur-0002", [960, 540]),
    ("OLM RadialBlur-0004", 4), ("OLM RadialBlur-0028", 1),
    ("OLM RadialBlur-0029", 0), ("OLM RadialBlur-0005", 0),
    ("OLM RadialBlur-0008", 0), ("OLM RadialBlur-0030", 1),
    ("OLM RadialBlur-0031", 0), ("OLM RadialBlur-0009", 0),
    ("OLM RadialBlur-0026", 1), ("OLM RadialBlur-0012", 1),
    ("OLM RadialBlur-0013", 0), ("OLM RadialBlur-0015", 5),
    ("OLM RadialBlur-0016", 1), ("OLM RadialBlur-0017", 0),
    ("OLM RadialBlur-0019", 0), ("OLM RadialBlur-0020", 1),
    ("OLM RadialBlur-0021", 0), ("OLM RadialBlur-0022", 1),
    ("OLM RadialBlur-0023", 0), ("OLM RadialBlur-0024", 10),
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
    return sorted(set(
        line[1:] for line in result.stdout.splitlines()
        if line.startswith("n/") and line.endswith("/Contents/MacOS/OLMRadialBlur")
    ))


def manifest_case0010() -> dict[str, Any]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = [case for case in payload.get("cases", []) if case.get("id") == "case_0010"]
    if len(cases) != 1:
        raise ValueError(f"expected one manifest case_0010, found {len(cases)}")
    case = cases[0]
    effects = case.get("effects", [])
    if len(effects) != 1:
        raise ValueError(f"expected one manifest effect, found {len(effects)}")
    effect = effects[0]
    recorded = [
        (item["match_name"], item["value"])
        for item in effect.get("params", []) if item.get("value_read_method")
    ]
    if effect.get("name") != "OLM RadialBlur" or effect.get("match_name") != "OLM RadialBlur":
        raise ValueError("manifest effect identity drifted")
    if not effect.get("enabled") or not effect.get("active"):
        raise ValueError("manifest effect is not enabled and active")
    if recorded != PARAMS:
        raise ValueError(f"manifest parameter contract drifted: {recorded!r}")
    expected_case = {
        "frame": "case_0010.png", "before_effects_frame": "case_0010_before_effects.png",
        "before_effects_scope": "selected_layer_all_effects_disabled",
        "render_resolution_factor": [1, 1], "time": 0,
    }
    for key, value in expected_case.items():
        if case.get(key) != value:
            raise ValueError(f"manifest case0010 {key} drifted")
    comp = payload.get("comp", {})
    if (comp.get("width"), comp.get("height"), comp.get("frame_rate"), comp.get("bpc")) != (1920, 1080, 24, 8):
        raise ValueError("manifest comp contract drifted")
    return case


def png_rgba(path: Path) -> tuple[bytes, int, int]:
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError("Pillow is required for lossless RGBA comparison") from error
    with Image.open(path) as image:
        if image.format != "PNG":
            raise ValueError(f"not a PNG: {path}")
        rgba = image.convert("RGBA")
        width, height = rgba.size
        return rgba.tobytes(), width, height


def compare_png(
    actual: Path, expected: Path, witness_pins: dict[tuple[int, int], list[int]] | None = None
) -> dict[str, Any]:
    actual_rgba, width, height = png_rgba(actual)
    expected_rgba, ew, eh = png_rgba(expected)
    if (width, height) != (1920, 1080) or (ew, eh) != (1920, 1080):
        raise ValueError(f"unexpected PNG dimensions actual={width}x{height} expected={ew}x{eh}")
    differing_pixels = 0
    max_abs = [0, 0, 0, 0]
    first_difference = None
    for offset in range(0, len(actual_rgba), 4):
        av = actual_rgba[offset:offset + 4]
        ev = expected_rgba[offset:offset + 4]
        if av != ev:
            differing_pixels += 1
            if first_difference is None:
                pixel = offset // 4
                first_difference = {"xy": [pixel % width, pixel // width], "actual": list(av), "expected": list(ev)}
            for channel in range(4):
                max_abs[channel] = max(max_abs[channel], abs(av[channel] - ev[channel]))
    witnesses = {}
    for (x, y), pinned in (witness_pins or {}).items():
        offset = (y * width + x) * 4
        actual_pixel = list(actual_rgba[offset:offset + 4])
        expected_pixel = list(expected_rgba[offset:offset + 4])
        witnesses[f"{x},{y}"] = {
            "actual_rgba8": actual_pixel, "reference_rgba8": expected_pixel,
            "pinned_rgba8": pinned, "exact": actual_pixel == expected_pixel == pinned,
        }
    return {
        "width": width, "height": height, "rgba8_sha256": hashlib.sha256(actual_rgba).hexdigest(),
        "expected_rgba8_sha256": hashlib.sha256(expected_rgba).hexdigest(),
        "differing_pixels": differing_pixels, "max_abs_rgba8": max_abs,
        "first_difference": first_difference, "witnesses": witnesses,
        "exact": differing_pixels == 0 and all(item["exact"] for item in witnesses.values()),
    }


def png_header(path: Path) -> dict[str, int]:
    data = path.read_bytes()[:33]
    if len(data) != 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"invalid PNG header: {path}")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", data[16:29])
    return {"width": width, "height": height, "bit_depth": depth, "color_type": color,
            "compression": compression, "filter_method": filtering, "interlace": interlace}


def jsx(output_dir: Path, result_path: Path) -> str:
    params = json.dumps(PARAMS, separators=(",", ":"))
    return r'''(function(){
function F(m){throw new Error("FAIL_CLOSED: "+m)}
function W(p,o){var f=new File(p);f.encoding="UTF-8";if(!f.open("w"))F("write "+p);f.write(JSON.stringify(o));f.close()}
function H(p){var q="'"+String(p).replace(/'/g,"'\\''")+"'",m=system.callSystem("/usr/bin/shasum -a 256 "+q).match(/^([0-9a-f]{64})/i);if(!m)F("hash "+p);return m[1].toLowerCase()}
function Find(g,n){for(var i=1;i<=g.numProperties;i++){var p=g.property(i);if(p.matchName===n)return p;if(p.numProperties){var q=Find(p,n);if(q)return q}}return null}
function Stable(v){if(v===null||typeof v!=="object")return JSON.stringify(v);if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(Stable(v[i]));return "["+a.join(",")+"]"}var k=[],z=[];for(var q in v)if(v.hasOwnProperty(q))k.push(q);k.sort();for(var j=0;j<k.length;j++)z.push(JSON.stringify(k[j])+":"+Stable(v[k[j]]));return "{"+z.join(",")+"}"}
function ResolvePng(dir,stem,before){var files=dir.getFiles(function(f){return f instanceof File&&f.name.toLowerCase().indexOf(stem.toLowerCase())===0&&/\.png$/i.test(f.name)}),fresh=[];for(var i=0;i<files.length;i++)if(!before[files[i].fsName])fresh.push(files[i]);if(fresh.length!==1)F("expected one fresh PNG for "+stem+", found "+fresh.length);return fresh[0]}
function WaitFile(path){for(var i=0;i<200;i++){var f=new File(path);if(f.exists)return f;$.sleep(25)}F("timed out waiting for "+path)}
var input=new File(INPUT),outDir=new Folder(OUTPUT),result=RESULT,params=PARAMS;
if(!input.exists)F("input missing");if(!outDir.exists)F("output directory missing");
app.newProject();var project=app.project;if(!project)F("new project");project.bitsPerChannel=8;project.linearBlending=false;project.workingSpace="";project.gpuAccelType=GpuAccelType.SOFTWARE;
if(project.bitsPerChannel!==8||project.gpuAccelType!==GpuAccelType.SOFTWARE||project.linearBlending||(project.workingSpace!==""&&project.workingSpace!=="None"))F("project contract");
var footage=project.importFile(new ImportOptions(input)),comp=project.items.addComp("OLMRadialBlur_case0010_pf8",1920,1080,1,1,24),layer=comp.layers.add(footage);
comp.resolutionFactor=[1,1];comp.time=0;
var effect=layer.property("ADBE Effect Parade").addProperty("OLM RadialBlur");if(!effect||effect.matchName!=="OLM RadialBlur"||effect.name!=="OLM RadialBlur")F("effect identity");
var readback=[];for(var i=0;i<params.length;i++){var p=Find(effect,params[i][0]);if(!p)F("missing "+params[i][0]);p.setValue(params[i][1]);if(JSON.stringify(p.value)!==JSON.stringify(params[i][1]))F("readback "+params[i][0]);readback.push([p.matchName,p.value])}
if(JSON.stringify(readback)!==JSON.stringify(params))F("aggregate parameter readback");
function Render(enabled,stem){effect.enabled=enabled;var rendered=new File(outDir.fsName+"/"+stem+".png");if(rendered.exists)F("stale output "+rendered.fsName);comp.saveFrameToPng(comp.time,rendered);rendered=WaitFile(rendered.fsName);return {path:rendered.fsName,sha256:H(rendered.fsName),template:"saveFrameToPng",settings:{method:"saveFrameToPng",time:comp.time},settings_serialized:"saveFrameToPng@0"}}
var control=Render(false,"control"),effectOn=Render(true,"effect_on");if(control.settings_serialized!==effectOn.settings_serialized)F("Output Module settings differ");
W(result,{kind:"olmradialblur_case0010_pf8_mac_return",ae_version:app.version,os:$.os,project:{bits_per_channel:project.bitsPerChannel,renderer:"SOFTWARE",working_space:project.workingSpace,linear_blending:project.linearBlending,resolution_factor:comp.resolutionFactor,time:comp.time},plugin:{effect_name:effect.name,effect_match_name:effect.matchName,path:PLUGIN,sha256:PLUGIN_SHA},input:{path:INPUT,sha256:H(INPUT)},manifest:{path:MANIFEST,sha256:H(MANIFEST),case_id:"case_0010"},reference:{path:REFERENCE,sha256:H(REFERENCE)},params:params,param_readback:readback,outputs:{control:control,effect_on:effectOn}});
try{project.close(CloseOptions.DO_NOT_SAVE_CHANGES)}catch(e){}
}());'''.replace("INPUT", json.dumps(str(INPUT))).replace("OUTPUT", json.dumps(str(output_dir))).replace("RESULT", json.dumps(str(result_path))).replace("PARAMS", params).replace("TEMPLATE", json.dumps(OUTPUT_TEMPLATE)).replace("PLUGIN_SHA", json.dumps(EXPECTED_BINARY_SHA256)).replace("PLUGIN", json.dumps(str(INSTALLED_BINARY))).replace("MANIFEST", json.dumps(str(MANIFEST))).replace("REFERENCE", json.dumps(str(REFERENCE)))


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
    parser.add_argument("--run", action="store_true", help="render only after every provenance preflight passes")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()

    def file_hash(path: Path) -> str | None:
        return sha256(path) if path.is_file() else None

    manifest_error = None
    try:
        manifest_case0010()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        manifest_error = str(error)
    pids = ae_pids()
    modules = {str(pid): loaded_radialblur(pid) for pid in pids}
    expected_path = str(INSTALLED_BINARY.resolve()) if INSTALLED_BINARY.exists() else None
    exact_mapping = len(pids) == 1 and expected_path is not None and modules.get(str(pids[0])) == [expected_path]
    checks = {
        "input_hash": file_hash(INPUT), "input_hash_matches": file_hash(INPUT) == EXPECTED_INPUT_SHA256,
        "reference_hash": file_hash(REFERENCE), "reference_hash_matches": file_hash(REFERENCE) == EXPECTED_REFERENCE_SHA256,
        "manifest_hash": file_hash(MANIFEST), "manifest_hash_matches": file_hash(MANIFEST) == EXPECTED_MANIFEST_SHA256,
        "manifest_case0010_exact": manifest_error is None, "manifest_error": manifest_error,
        "installed_binary_hash": file_hash(INSTALLED_BINARY),
        "installed_binary_hash_matches": file_hash(INSTALLED_BINARY) == EXPECTED_BINARY_SHA256,
        "single_ae_process": len(pids) == 1, "ae_pids": pids,
        "loaded_module_paths": modules, "loaded_module_is_sole_exact_installed_binary": exact_mapping,
    }
    ready = all(checks[key] for key in (
        "input_hash_matches", "reference_hash_matches", "manifest_hash_matches",
        "manifest_case0010_exact", "installed_binary_hash_matches", "single_ae_process",
        "loaded_module_is_sole_exact_installed_binary",
    ))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = (args.output_root or ROOT / f"refs/reports/olmradialblur_case0010_pf8_mac_{timestamp}").resolve()
    root.mkdir(parents=True, exist_ok=True)
    report_path, result_path = root / "runner_report.json", root / "ae_return.json"
    report: dict[str, Any] = {
        "kind": "olmradialblur_case0010_pf8_mac_runner_20260805", "schema": 1,
        "status": "ready" if ready else "restart_required", "checks": checks,
        "contract": {"case_id": "case_0010", "bit_depth": 8, "renderer": "Software",
                     "effect_name": "OLM RadialBlur", "effect_match_name": "OLM RadialBlur",
                     "output": "lossless RGBA PNG", "params": PARAMS,
                     "witnesses": {f"{x},{y}": rgba for (x, y), rgba in WITNESSES.items()}},
        "run_requested": args.run, "run_executed": False,
        "claim_boundary": {
            "scope": "AE 2026; Software; PF8; canonical 1920x1080 case0010 input and exact manifest parameters only",
            "retained_windows_png_exact": False, "mac_ae_rendered": False,
            "other_rotation_inputs_or_parameters": False, "other_bit_depths": False,
        },
    }
    if not ready or not args.run:
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "report": str(report_path), "checks": checks}))
        return 2 if not ready else 0

    with tempfile.TemporaryDirectory(prefix="olmradialblur_case0010_pf8_") as temp:
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
        try:
            returned = json.loads(result_path.read_text(encoding="utf-8"))
            if returned.get("params") != [list(item) for item in PARAMS] or returned.get("param_readback") != [list(item) for item in PARAMS]:
                raise ValueError("returned parameter contract/readback drifted")
            if returned.get("plugin") != {"effect_name": "OLM RadialBlur", "effect_match_name": "OLM RadialBlur", "path": str(INSTALLED_BINARY), "sha256": EXPECTED_BINARY_SHA256}:
                raise ValueError("returned effect/plugin identity drifted")
            project = returned.get("project", {})
            if project.get("bits_per_channel") != 8 or project.get("renderer") != "SOFTWARE" or project.get("resolution_factor") != [1, 1] or project.get("time") != 0:
                raise ValueError("returned project contract drifted")
            control_path = Path(returned["outputs"]["control"]["path"]).resolve()
            effect_path = Path(returned["outputs"]["effect_on"]["path"]).resolve()
            if control_path.parent != root or effect_path.parent != root or control_path == effect_path:
                raise ValueError("returned output paths escaped or aliased")
            for path in (control_path, effect_path):
                header = png_header(path)
                if header != {"width": 1920, "height": 1080, "bit_depth": 8, "color_type": 6,
                              "compression": 0, "filter_method": 0, "interlace": 0}:
                    raise ValueError(f"lossless RGBA8 PNG contract mismatch: {header}")
            control_comparison = compare_png(control_path, INPUT)
            effect_comparison = compare_png(effect_path, REFERENCE, WITNESSES)
            report["outputs"] = {
                "control": {"path": str(control_path), "file_sha256": sha256(control_path), "comparison_to_input": control_comparison},
                "effect_on": {"path": str(effect_path), "file_sha256": sha256(effect_path), "comparison_to_retained_windows_reference": effect_comparison},
            }
            report["output_module_settings_identical"] = returned["outputs"]["control"]["settings_serialized"] == returned["outputs"]["effect_on"]["settings_serialized"]
            exact = control_comparison["exact"] and effect_comparison["exact"] and report["output_module_settings_identical"]
            report["status"] = "mac_windows_png_exact" if exact else "mac_mismatch"
            report["claim_boundary"]["mac_ae_rendered"] = True
            report["claim_boundary"]["retained_windows_png_exact"] = exact
        except (KeyError, OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
            report["status"] = "validation_failed"
            report["validation_error"] = str(error)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(report_path)}))
    return 0 if report["status"] == "mac_windows_png_exact" else 1


if __name__ == "__main__":
    raise SystemExit(main())
