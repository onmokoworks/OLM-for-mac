#!/usr/bin/env python3
"""Fresh-AE installed-module smoke for the current OLMBlur Universal build.

This is deliberately a host load/apply/render smoke.  It does not exercise or
promote the separate Lab76 two-key pixel-exact fixture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app")
EXECUTABLE = APP / "Contents/MacOS/After Effects"
PLUGIN_BUNDLE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMBlur.plugin"
PLUGIN_BINARY = PLUGIN_BUNDLE / "Contents/MacOS/OLMBlur"
EXPECTED_BINARY_SHA256 = "b1461f8ee35b3d566a9825e9e04882c8ec28b51ce9e67dbbd83f463d706d943f"
EXPECTED_AE_VERSION = "26.3x87"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout)


def ae_pids() -> list[int]:
    found = run(["pgrep", "-f", f"^{EXECUTABLE}$"])
    return [int(value) for value in found.stdout.split() if value.isdigit()]


def loaded_colorkey(pid: int) -> list[str]:
    found = run(["lsof", "-Fn", "-p", str(pid)])
    return sorted({
        line[1:] for line in found.stdout.splitlines()
        if line.startswith("n/") and line.endswith("/Contents/MacOS/OLMBlur")
    })


def wait_for_fresh_host(timeout: float = 180.0) -> tuple[list[int], dict[str, list[str]]]:
    deadline = time.monotonic() + timeout
    last_pids: list[int] = []
    last_maps: dict[str, list[str]] = {}
    while time.monotonic() < deadline:
        last_pids = ae_pids()
        last_maps = {str(pid): loaded_colorkey(pid) for pid in last_pids}
        # OLMBlur is lazy-loaded by this host.  A fresh process may have no
        # mapping until addProperty(); the post-render mapping is the identity
        # gate, while the on-disk SHA is pinned before launch.
        if len(last_pids) == 1:
            return last_pids, last_maps
        time.sleep(1.0)
    return last_pids, last_maps


def jsx(output_dir: Path, result_path: Path) -> str:
    return r'''(function(){
function F(m){throw new Error("FAIL_CLOSED: "+m)}
function E(s){return String(s).replace(/\\/g,"\\\\").replace(/"/g,'\\"').replace(/\r/g,"\\r").replace(/\n/g,"\\n")}
function J(v){if(v===null||v===undefined)return "null";if(typeof v==="boolean"||typeof v==="number")return String(v);if(typeof v==="string")return '"'+E(v)+'"';if(Object.prototype.toString.call(v)==="[object Array]"){var a=[];for(var i=0;i<v.length;i++)a.push(J(v[i]));return "["+a.join(",")+"]"}var p=[];for(var k in v)if(v.hasOwnProperty(k))p.push('"'+E(k)+'":'+J(v[k]));return "{"+p.join(",")+"}"}
function W(p,o){var text=J(o),f=new File(p);f.encoding="UTF-8";if(!f.open("w"))F("write "+p);f.write(text);f.close()}
function H(p){var q="'"+String(p).replace(/'/g,"'\\''")+"'",m=system.callSystem("/usr/bin/shasum -a 256 "+q).match(/^([0-9a-f]{64})/i);if(!m)F("hash "+p);return m[1].toLowerCase()}
function R(path){var target=new File(path);if(target.exists)return target;var matches=target.parent.getFiles(function(f){return f instanceof File&&f.name.indexOf(target.name)===0});if(matches.length!==1)F("rendered output cardinality "+matches.length);return matches[0]}
function Render(project,comp,effect,enabled,name){effect.enabled=enabled;var q=project.renderQueue.items.add(comp),om=q.outputModule(1),path=OUT+"/"+name+".exr";q.timeSpanStart=0;q.timeSpanDuration=1/comp.frameRate;om.applyTemplate("OLM EXR 32 Float");om.file=new File(path);project.renderQueue.render();var f=R(path);q.remove();return {path:f.fsName,sha256:H(f.fsName)}}
function V(v){if(v===null||v===undefined)return null;if(typeof v==="number"||typeof v==="string"||typeof v==="boolean")return v;if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++)a.push(V(v[i]));return a}return String(v)}
function Snap(effect){var a=[];for(var i=1;i<=effect.numProperties;i++){var p=effect.property(i);if(p.propertyType===PropertyType.PROPERTY){try{a.push({index:i,name:String(p.name),match_name:String(p.matchName),value:V(p.value)})}catch(_){}}}return a}
app.newProject();var project=app.project;if(!project)F("new project");project.bitsPerChannel=32;project.linearBlending=false;project.workingSpace="";project.gpuAccelType=GpuAccelType.SOFTWARE;
if(project.bitsPerChannel!==32||project.gpuAccelType!==GpuAccelType.SOFTWARE||project.linearBlending||(project.workingSpace!==""&&project.workingSpace!=="None"))F("project contract");
var comp=project.items.addComp("OLMBlur_current_install_smoke",64,36,1,1,24),layer=comp.layers.addSolid([0.102,0.749,0.8],"rgba_test_opaque",64,36,1,1),effect=layer.property("ADBE Effect Parade").addProperty("OLM OLM Blur");
if(!effect||effect.matchName!=="OLM OLM Blur")F("effect identity");
var before=Snap(effect),beforeText=J(before);
app.beginSuppressDialogs();var control=Render(project,comp,effect,false,"control"),effectOn=Render(project,comp,effect,true,"effect_on");app.endSuppressDialogs(false);
var after=Snap(effect),afterText=J(after);
W(RESULT,{kind:"olmblur_current_install_ae_return",status:"ok",ae_version:String(app.version),os:String($.os),project:{bits_per_channel:project.bitsPerChannel,renderer_raw:Number(project.gpuAccelType),renderer:"SOFTWARE",working_space:String(project.workingSpace),linear_blending:project.linearBlending,dimensions:[comp.width,comp.height]},effect:{name:String(effect.name),match_name:String(effect.matchName),parameter_count:before.length,parameters_before:before,parameters_after:after,parameters_unchanged:beforeText===afterText},source:{kind:"AE solid",rgba8:[26,191,204,255]},outputs:{control:control,effect_on:effectOn}});
try{project.close(CloseOptions.DO_NOT_SAVE_CHANGES)}catch(e){}
}());'''.replace("OUT", json.dumps(str(output_dir))).replace("RESULT", json.dumps(str(result_path)))


def loader(payload: Path, trace: Path) -> str:
    return (
        "(function(){\n"
        f"var t=new File({json.dumps(str(trace))}),p=new File({json.dumps(str(payload))});\n"
        'function A(s){t.encoding="UTF-8";if(t.open("a")){t.writeln(s);t.close();}}\n'
        'A("LOADER_ENTER");try{$.evalFile(p);A("LOADER_RETURN");}catch(e){A("LOADER_FAIL error="+e.toString()+" line="+(e.line||0)+" file="+(e.fileName||""));}\n'
        "}());\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-report", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    raw_path = args.raw_report.resolve()
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    initial_pids = ae_pids()
    installed_pre = sha256(PLUGIN_BINARY) if PLUGIN_BINARY.is_file() else None
    matching = sorted(str(path) for path in PLUGIN_BUNDLE.parent.glob("OLMBlur.plugin"))
    info = plistlib.loads((APP / "Contents/Info.plist").read_bytes()) if APP.is_dir() else {}
    report: dict = {
        "schema_version": 1,
        "kind": "olmblur_current_install_ae_smoke_raw",
        "status": "blocked",
        "fresh_host": {"initial_ae_pids": initial_pids, "agent_started_ae": False, "agent_quit_ae": False},
        "installed_plugin": {
            "bundle_path": str(PLUGIN_BUNDLE), "binary_path": str(PLUGIN_BINARY),
            "binary_sha256_pre": installed_pre, "expected_binary_sha256": EXPECTED_BINARY_SHA256,
            "matching_bundle_paths": matching,
        },
        "application": {
            "path": str(APP), "plist_short_version": info.get("CFBundleShortVersionString"),
            "plist_build": info.get("CFBundleVersion"),
        },
        "claim_boundary": "Fresh AE installed-path load, effect add, default-parameter PF32 Software render only; no Lab76 two-key live-host pixel-exact claim.",
    }
    if initial_pids or installed_pre != EXPECTED_BINARY_SHA256 or matching != [str(PLUGIN_BUNDLE)] or not APP.is_dir():
        raw_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "report": str(raw_path)}))
        return 2

    opened = run(["open", "-a", "Adobe After Effects 2026"])
    report["fresh_host"]["open"] = {"returncode": opened.returncode, "stdout": opened.stdout, "stderr": opened.stderr}
    report["fresh_host"]["agent_started_ae"] = opened.returncode == 0
    pids, mappings = wait_for_fresh_host()
    report["fresh_host"].update({"ae_pids_pre_render": pids, "loaded_modules_pre_render": mappings})
    expected_path = str(PLUGIN_BINARY.resolve())
    if len(pids) != 1:
        raw_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 2

    with tempfile.TemporaryDirectory(prefix="olmblur-current-install-smoke-") as temporary:
        temp = Path(temporary)
        output = temp / "output"; output.mkdir()
        result = temp / "ae_return.json"
        trace = temp / "host_trace.log"
        payload = temp / "payload.jsx"; payload.write_text(jsx(output, result), encoding="utf-8")
        launch = temp / "launch.jsx"; launch.write_text(loader(payload, trace), encoding="utf-8")
        apple = (
            "with timeout of 900 seconds\n"
            + 'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file '
            + json.dumps(str(launch)) + " with override\nend timeout\n"
        )
        invoked = subprocess.run(["osascript"], input=apple, capture_output=True, text=True, timeout=args.timeout)
        result_text = result.read_text(encoding="utf-8") if result.is_file() else None
        try:
            returned = json.loads(result_text) if result_text else None
        except json.JSONDecodeError:
            returned = None
        report["execution"] = {
            "osascript": {"returncode": invoked.returncode, "stdout": invoked.stdout, "stderr": invoked.stderr},
            "host_trace": trace.read_text(encoding="utf-8", errors="replace") if trace.is_file() else None,
            "ae_return_text": result_text,
            "ae_return": returned,
        }

    post_pids = ae_pids()
    post_maps = {str(pid): loaded_colorkey(pid) for pid in post_pids}
    installed_post = sha256(PLUGIN_BINARY) if PLUGIN_BINARY.is_file() else None
    report["fresh_host"].update({"ae_pids_post_render": post_pids, "loaded_modules_post_render": post_maps})
    report["installed_plugin"]["binary_sha256_post"] = installed_post
    expected_return = (
        returned is not None and returned.get("status") == "ok"
        and returned.get("ae_version") == EXPECTED_AE_VERSION
        and returned.get("project", {}).get("bits_per_channel") == 32
        and returned.get("project", {}).get("renderer_raw") == 1816
        and returned.get("project", {}).get("renderer") == "SOFTWARE"
        and returned.get("project", {}).get("working_space") in ("", "None")
        and returned.get("project", {}).get("linear_blending") is False
        and returned.get("project", {}).get("dimensions") == [64, 36]
        and returned.get("effect", {}).get("match_name") == "OLM OLM Blur"
        and returned.get("effect", {}).get("parameter_count", 0) > 0
        and returned.get("effect", {}).get("parameters_unchanged") is True
        and returned.get("effect", {}).get("parameters_before") == returned.get("effect", {}).get("parameters_after")
        and all(returned.get("outputs", {}).get(name, {}).get("sha256") for name in ("control", "effect_on"))
    )
    identity_exact = (
        post_pids == pids and post_maps.get(str(pids[0])) == [expected_path]
        and installed_post == EXPECTED_BINARY_SHA256
    )
    report["status"] = "installed_host_smoke_pass" if invoked.returncode == 0 and expected_return and identity_exact else "fail_closed"
    report["gates"] = {
        "fresh_process": initial_pids == [] and len(pids) == 1,
        "loaded_module_identity_exact_after_effect_add": identity_exact,
        "effect_add_and_render_completed": expected_return,
        "installed_hash_unchanged": installed_post == installed_pre == EXPECTED_BINARY_SHA256,
        "lab76_live_pixel_exact_claim": False,
    }

    quit_run = run(["osascript", "-e", 'tell application "Adobe After Effects 2026" to quit saving no'])
    deadline = time.monotonic() + 120.0
    while ae_pids() and time.monotonic() < deadline:
        time.sleep(1.0)
    report["fresh_host"]["quit"] = {"returncode": quit_run.returncode, "stdout": quit_run.stdout, "stderr": quit_run.stderr}
    report["fresh_host"]["agent_quit_ae"] = not ae_pids()
    if not report["fresh_host"]["agent_quit_ae"]:
        report["status"] = "fail_closed"
    raw_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(raw_path)}))
    return 0 if report["status"] == "installed_host_smoke_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
