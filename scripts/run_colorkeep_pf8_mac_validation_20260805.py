#!/usr/bin/env python3
"""Fail-closed ColorKeep PF8 Mac AE runner; preflight-only unless --execute is explicit."""

from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import shutil
import subprocess
import tempfile
import datetime as dt
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
APP = Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app")
PLUGIN = Path("/Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin")
BINARY = PLUGIN / "Contents/MacOS/ColorKeep"
EXPECTED_PLUGIN_SHA = "ccc89781fa547450acc3053cb77bff8d6983cd8c6835866c87449e7a64117cce"
EXPECTED_AE_VERSION = "26.3.0"
EXPECTED_AE_APP_VERSION = "26.3x87"
FIXTURE_REPORT = ROOT / "refs/conformance/colorkeep_pf8_mac_ae_fixture_actual_aex_20260805.json"
REQUEST = ROOT / "refs/mac_validation_requests/colorkeep_pf8_mac_ae_validation_20260805.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_process_clear() -> bool:
    return all(subprocess.run(["pgrep", "-x", name], capture_output=True).returncode != 0 for name in ("After Effects", "aerender"))


def loaded_module_proof(expected_pid: int | None = None, require_mapping: bool = True) -> dict:
    if expected_pid is not None:
        command = subprocess.run(["ps", "-p", str(expected_pid), "-o", "command="], capture_output=True, text=True, check=True).stdout.strip()
        expected_executable = str(APP / "Contents/MacOS/After Effects")
        if command != expected_executable:
            raise RuntimeError(f"PID {expected_pid} is not exact AE executable: {command!r}")
        pids = [expected_pid]
    else:
        found = subprocess.run(["pgrep", "-f", "^/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects$"], capture_output=True, text=True, check=True)
        pids = [int(v) for v in found.stdout.split() if v.isdigit()]
    if len(pids) != 1:
        raise RuntimeError(f"expected one AE process after launch, found {pids}")
    if expected_pid is not None and pids[0] != expected_pid:
        raise RuntimeError(f"AE PID changed: expected {expected_pid}, found {pids[0]}")
    started = subprocess.run(["ps", "-p", str(pids[0]), "-o", "lstart="], capture_output=True, text=True, check=True)
    started_at = dt.datetime.strptime(" ".join(started.stdout.split()), "%a %b %d %H:%M:%S %Y").timestamp()
    if BINARY.stat().st_mtime > started_at:
        raise RuntimeError("ColorKeep binary does not predate the mapped AE process")
    resolved = str(BINARY.resolve())
    mapped_exact = False
    if require_mapping:
        mapped = subprocess.run(["vmmap", str(pids[0])], capture_output=True, text=True, timeout=120)
        mapped_exact = not mapped.returncode and any(resolved in line for line in mapped.stdout.splitlines())
        if not mapped_exact:
            raise RuntimeError("exact ColorKeep binary path is absent from AE vmmap")
    if sha256(BINARY) != EXPECTED_PLUGIN_SHA:
        raise RuntimeError("ColorKeep binary changed during AE execution")
    return {"method": "vmmap_exact_path" if require_mapping else "pre_lazy_load_process_identity",
            "pid": pids[0], "process_started_local": " ".join(started.stdout.split()),
            "binary_predates_process_start": True, "mapped_exact": mapped_exact,
            "path": resolved, "sha256": EXPECTED_PLUGIN_SHA}


def require_sole_bundle() -> None:
    roots = [Path("/Library/Application Support/Adobe/Common/Plug-ins"),
             Path.home() / "Library/Application Support/Adobe/Common/Plug-ins"]
    matches = []
    for root in roots:
        if root.is_dir():
            matches.extend(path.resolve() for path in root.rglob("ColorKeep.plugin") if path.is_dir())
    unique = sorted(set(matches), key=str)
    if unique != [PLUGIN.resolve()]:
        raise RuntimeError(f"ColorKeep bundle is not sole in Adobe plug-in roots: {[str(p) for p in unique]}")


def verify_host_export_pixels(observed: Image.Image, expected: Image.Image) -> None:
    observed = observed.convert("RGBA"); expected = expected.convert("RGBA")
    if observed.size != (4, 4) or expected.size != (4, 3):
        raise RuntimeError(f"unexpected AE/fixture dimensions: observed={observed.size}, expected={expected.size}")
    source_footprint = observed.crop((0, 0, 4, 3))
    observed_pixels = list(source_footprint.get_flattened_data()); expected_pixels = list(expected.get_flattened_data())
    for index, (actual_pixel, expected_pixel) in enumerate(zip(observed_pixels, expected_pixels)):
        if actual_pixel[3] != expected_pixel[3]:
            raise RuntimeError(f"AE source-footprint alpha differs from actual-AEX at pixel {index}: {actual_pixel} != {expected_pixel}")
        if expected_pixel[3] and actual_pixel != expected_pixel:
            raise RuntimeError(f"AE source-footprint opaque RGBA differs from actual-AEX at pixel {index}: {actual_pixel} != {expected_pixel}")
        if not expected_pixel[3] and actual_pixel != (0, 0, 0, 0):
            raise RuntimeError(f"AE saveFrameToPng transparent-pixel normalization drift at pixel {index}: {actual_pixel}")
    if any(pixel != (0, 0, 0, 0) for pixel in observed.crop((0, 3, 4, 4)).get_flattened_data()):
        raise RuntimeError("AE minimum-comp padding row is not transparent black")


def preflight() -> tuple[dict, dict]:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE_REPORT.read_text(encoding="utf-8"))
    if request["status"] != "prepared_not_executed" or request["installed_plugin"]["sha256"] != EXPECTED_PLUGIN_SHA:
        raise RuntimeError("request identity/status drift")
    if request["ae_contract"] != {"version": EXPECTED_AE_VERSION, "bits_per_channel": 8, "renderer": "SOFTWARE", "working_space": "None", "linear_blending": False}:
        raise RuntimeError("AE contract drift")
    if PLUGIN.name != "ColorKeep.plugin" or not BINARY.is_file() or sha256(BINARY) != EXPECTED_PLUGIN_SHA:
        raise RuntimeError("installed ColorKeep identity mismatch")
    file_out = subprocess.run(["file", str(BINARY)], check=True, capture_output=True, text=True).stdout
    if "x86_64" not in file_out or "arm64" not in file_out:
        raise RuntimeError("installed ColorKeep is not universal x86_64+arm64")
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(PLUGIN)], check=True, capture_output=True)
    with (APP / "Contents/Info.plist").open("rb") as stream:
        version = plistlib.load(stream).get("CFBundleShortVersionString")
    if version != EXPECTED_AE_VERSION:
        raise RuntimeError(f"AE version mismatch: {version!r}")
    if fixture["status"] != "exact_actual_aex_fixture":
        raise RuntimeError("actual-AEX fixture status drift")
    for artifact in fixture["artifacts"].values():
        path = ROOT / artifact["path"]
        if not path.is_file() or sha256(path) != artifact["sha256"]:
            raise RuntimeError(f"fixture artifact mismatch: {path}")
    return request, fixture


def jsx_source(request: dict) -> str:
    return r'''(function(){
function E(n){return $.getenv(n)||"";} function F(m){throw new Error("FAIL_CLOSED: "+m);} function Q(v){return '"'+String(v).replace(/\\/g,"\\\\").replace(/"/g,'\\"')+'"';}
function SQ(v){var q=String.fromCharCode(39),s=String.fromCharCode(92);return q+String(v).split(q).join(q+s+q+q)+q;}
function H(p){var s=system.callSystem("/usr/bin/shasum -a 256 "+SQ(p));var m=s.match(/^([0-9a-f]{64})/i);if(!m)F("hash "+p);return m[1].toLowerCase();}
function W(p,t){var f=new File(p);f.encoding="UTF-8";if(!f.open("w"))F("write "+p);f.write(t);f.close();}
function L(t){var f=new File(E("CK_TRACE"));f.encoding="UTF-8";if(f.open("a")){f.write(String(t)+"\n");f.close();}}
try{
var spec=SPEC, input=new File(E("CK_INPUT")), out=new File(E("CK_OUTPUT")), result=E("CK_RESULT"), binary=new File(E("CK_BINARY"));
if(!input.exists||H(input.fsName)!==spec.input.sha256||!binary.exists||H(binary.fsName)!==spec.installed_plugin.sha256)F("identity");
L("payload entered");if(app.project){try{app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);}catch(closeError){F("close previous project "+closeError);}}
var p=app.newProject();if(!p)F("new project returned null");p.bitsPerChannel=8;p.linearBlending=false;p.workingSpace="";p.gpuAccelType=GpuAccelType.SOFTWARE;
var workingSpaceText=String(p.workingSpace);if(String(app.version)!==spec.runtime_ae_version||p.bitsPerChannel!==8||Number(p.gpuAccelType)!==Number(GpuAccelType.SOFTWARE)||p.linearBlending||(workingSpaceText!==""&&workingSpaceText!=="None"))F("AE contract app.version="+String(app.version)+" bpc="+String(p.bitsPerChannel)+" renderer="+String(p.gpuAccelType)+" linear="+String(p.linearBlending)+" workingSpace="+workingSpaceText);
L("project exact");
var footage=p.importFile(new ImportOptions(input)),comp=p.items.addComp(spec.case.id,4,4,1,1,1),layer=comp.layers.add(footage),position=layer.property("ADBE Transform Group").property("ADBE Position");position.setValue([2,1.5]);var positionReadback=position.value;if(positionReadback[0]!==2||positionReadback[1]!==1.5)F("source footprint position readback");var fx=layer.property("ADBE Effect Parade").addProperty("OLM Color Keep");
if(!fx||fx.matchName!=="OLM Color Keep"||fx.name!=="Color Keep"||fx.numProperties!==102){var surface=[];if(fx)for(var si=1;si<=Math.min(5,fx.numProperties);si++){var sp=fx.property(si);surface.push(String(si)+":"+sp.name+":"+sp.matchName);}F("effect surface matchName="+(fx?fx.matchName:"missing")+" name="+(fx?fx.name:"")+" count="+(fx?String(fx.numProperties):"")+" first="+surface.join("|"));}
fx.property(1).setValue(5);if(Number(fx.property(1).value)!==5)F("count readback");
for(var i=0;i<spec.case.keys_rgba8.length;i++){var c=spec.case.keys_rgba8[i],v=[c[0]/255,c[1]/255,c[2]/255,1];fx.property(i+2).setValue(v);var r=fx.property(i+2).value;if(Math.abs(r[0]-v[0])>1e-6||Math.abs(r[1]-v[1])>1e-6||Math.abs(r[2]-v[2])>1e-6)F("color readback "+i);}
L("params exact");
if(out.exists&&!out.remove())F("stale output");comp.saveFrameToPng(0,out);for(var w=0;w<1800&&!out.exists;w++)$.sleep(100);if(!out.exists)F("render missing");
W(result,'{"status":"candidate_return_only","ae_exact_claim":false,"ae_version":'+Q(app.version)+',"bits_per_channel":8,"renderer":"SOFTWARE","working_space":"None","source_footprint":[4,3],"host_comp":[4,4],"plugin_sha256":'+Q(H(binary.fsName))+',"output_path":'+Q(out.fsName)+',"output_sha256":'+Q(H(out.fsName))+'}\n');
L("return written");
try{p.close(CloseOptions.DO_NOT_SAVE_CHANGES);}catch(e){}
}catch(runError){L("ERROR "+runError.toString()+" line="+String(runError.line));}
}());'''.replace("SPEC", json.dumps({**request, "runtime_ae_version": EXPECTED_AE_APP_VERSION}, separators=(",", ":")))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-dir", type=Path)
    parser.add_argument("--dump-js", type=Path)
    parser.add_argument("--execute", action="store_true", help="explicitly permit AE launch")
    parser.add_argument("--existing-pid", type=int, help="reuse this already-running, exact-mapped AE process; never launches/restarts it")
    args = parser.parse_args()
    try:
        request, fixture = preflight()
    except Exception as exc:
        print(f"[FAIL_CLOSED] {exc}"); return 1
    support = (args.support_dir or Path(tempfile.mkdtemp(prefix="colorkeep_pf8_mac_ae_"))).resolve()
    support.mkdir(parents=True, exist_ok=True)
    source = ROOT / request["input"]["path"]
    input_path = support / source.name; shutil.copy2(source, input_path)
    jsx = support / "run_colorkeep_pf8.jsx"; jsx.write_text(jsx_source(request), encoding="utf-8")
    output = support / "colorkeep_pf8_effect_on.png"; result = support / "candidate_return.json"
    wrapper = support / "wrapper.jsx"; trace = support / "host_trace.log"
    env = {"CK_INPUT": str(input_path), "CK_OUTPUT": str(output), "CK_RESULT": str(result), "CK_BINARY": str(BINARY), "CK_TRACE": str(trace)}
    wrapper.write_text("\n".join("$.setenv(%s,%s);" % (json.dumps(k), json.dumps(v)) for k, v in env.items())
                       + "\n(function(){\n"
                       + "var tracePath=%s,payloadPath=%s;\n" % (json.dumps(str(trace)), json.dumps(str(jsx)))
                       + "function L(t){var f=new File(tracePath);f.encoding=\"UTF-8\";if(f.open(\"a\")){f.write(String(t)+\"\\n\");f.close();}}\n"
                       + "L(\"wrapper entered\");\n"
                       + "try{$.evalFile(new File(payloadPath));}\n"
                       + "catch(loaderError){L(\"LOADER ERROR \"+String(loaderError)+\" line=\"+String(loaderError.line||\"\")+\" file=\"+String(loaderError.fileName||loaderError.source||\"\"));}\n"
                       + "}());\n", encoding="utf-8")
    if args.dump_js:
        args.dump_js.write_text(wrapper.read_text(encoding="utf-8"), encoding="utf-8")
    print(json.dumps({"status": "preflight_passed_not_executed" if not args.execute else "preflight_passed_execution_requested", "ae_was_launched": False, "support_dir": str(support), "jsx": str(jsx), "installed_sha256": EXPECTED_PLUGIN_SHA, "ae_version": EXPECTED_AE_VERSION, "process_clear": check_process_clear(), "actual_aex_expected_sha256": fixture["artifacts"]["colorkeep_pf8_expected_actual_aex.argb8"]["sha256"]}, indent=2))
    if not args.execute:
        return 0
    if args.existing_pid is not None:
        try:
            require_sole_bundle()
            loaded_module_proof(args.existing_pid, require_mapping=False)
        except Exception as exc:
            print(f"[FAIL_CLOSED] existing mapped process gate: {exc}"); return 1
    elif not check_process_clear():
        print("[FAIL_CLOSED] AE/aerender already running; use --existing-pid only after exact mapping proof"); return 1
    script = 'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file ' + json.dumps(str(wrapper)) + ' with override\n'
    run = subprocess.run(["osascript"], input=script, text=True, capture_output=True, timeout=7200)
    if run.returncode or not result.is_file():
        print("[FAIL_CLOSED] AE did not return a candidate"); return 1
    try:
        proof = loaded_module_proof(args.existing_pid)
        expected = Image.open(ROOT / request["expected_actual_aex"]["png_path"])
        observed = Image.open(output)
        verify_host_export_pixels(observed, expected)
        returned = json.loads(result.read_text(encoding="utf-8"))
        if returned.get("plugin_sha256") != proof["sha256"] or returned.get("ae_version") != EXPECTED_AE_APP_VERSION:
            raise RuntimeError("JSX return identity disagrees with external proof")
        returned.update({"status": "host_export_exact_hidden_rgb_unobservable", "ae_exact_claim": False, "loaded_plugin_proof": proof,
                         "actual_aex_alpha_exact": True, "actual_aex_opaque_rgba_exact": True,
                         "actual_aex_hidden_rgb_fixture_bound": True, "host_png_hidden_rgb_observable": False,
                         "comparison_scope": "top-left 4x3 source footprint in AE-minimum 4x4 comp",
                         "host_padding_row_transparent_black": True, "expected_png_sha256": request["expected_actual_aex"]["png_sha256"]})
        result.write_text(json.dumps(returned, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"[FAIL_CLOSED] post-render identity/pixel gate: {exc}"); return 1
    print(f"[OK] host-export-observable source footprint exact; hidden RGB excluded from PNG claim: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
