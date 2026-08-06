#!/usr/bin/env python3
"""Fail-closed AE runner for ColorKeep's observable PF16 extended-range leg."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import plistlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app")
PLUGIN = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin"
BINARY = PLUGIN / "Contents/MacOS/ColorKeep"
EXPECTED_SHA = "ccc89781fa547450acc3053cb77bff8d6983cd8c6835866c87449e7a64117cce"
FIXTURE = ROOT / "refs/conformance/colorkeep_pf16_extended_host_fixture_actual_aex_20260806.json"
INSTALLED_LEG = ROOT / "refs/conformance/colorkeep_installed_public_pf16_render_20260805.json"
TEMPLATE = "OLM EXR 32 Float"
PRESERVE_TEMPLATE = ROOT / "refs/fixtures/olmsmoother2_32bpc_preserve_rgb_input_template_20260726.aep"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one_ae_pid() -> int:
    result = subprocess.run(["pgrep", "-f", "^/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects$"], capture_output=True, text=True)
    pids = [int(v) for v in result.stdout.split() if v.isdigit()]
    if len(pids) != 1:
        raise RuntimeError(f"expected exactly one existing AE process, found {pids}")
    return pids[0]


def mapping(pid: int, require_loaded: bool) -> dict:
    started = subprocess.run(["ps", "-p", str(pid), "-o", "lstart="], check=True, capture_output=True, text=True).stdout
    started_ts = dt.datetime.strptime(" ".join(started.split()), "%a %b %d %H:%M:%S %Y").timestamp()
    if BINARY.stat().st_mtime > started_ts or sha(BINARY) != EXPECTED_SHA:
        raise RuntimeError("installed binary does not predate AE or changed")
    vm = subprocess.run(["vmmap", str(pid)], capture_output=True, text=True, timeout=120)
    mapped = vm.returncode == 0 and any(str(BINARY.resolve()) in line for line in vm.stdout.splitlines())
    if require_loaded and not mapped:
        raise RuntimeError("exact ColorKeep image is not mapped")
    return {"pid": pid, "path": str(BINARY.resolve()), "sha256": EXPECTED_SHA, "binary_predates_process": True, "vmmap_exact_path": mapped}


def preflight() -> tuple[dict, dict]:
    fixture = json.loads(FIXTURE.read_text())
    installed = json.loads(INSTALLED_LEG.read_text())
    if fixture["status"] != "prepared_actual_aex_active_pixels" or fixture["keys_alpha"] != [1.0, 1.0, 1.0]:
        raise RuntimeError("fixture is not public-RGB/alpha-one bounded")
    if installed["installed_binary_sha256"] != EXPECTED_SHA or not installed["raw_exact"] or not installed["padding_exact"]:
        raise RuntimeError("separate installed 120-byte leg is not exact")
    if sha(BINARY) != EXPECTED_SHA:
        raise RuntimeError("installed ColorKeep identity mismatch")
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(PLUGIN)], check=True, capture_output=True)
    with (APP / "Contents/Info.plist").open("rb") as stream:
        if plistlib.load(stream).get("CFBundleShortVersionString") != "26.3.0":
            raise RuntimeError("AE version mismatch")
    for artifact in fixture["artifacts"].values():
        path = ROOT / artifact["path"]
        if sha(path) != artifact["sha256"]:
            raise RuntimeError(f"fixture drift: {path}")
    if not PRESERVE_TEMPLATE.is_file():
        raise RuntimeError("Preserve RGB input template is missing")
    return fixture, installed


def jsx(fixture: dict) -> str:
    spec = {"keys": fixture["keys_public_rgb"], "input_sha": fixture["artifacts"]["input_pf16_units_as_float.exr"]["sha256"]}
    return r'''(function(){
function E(n){return $.getenv(n)||"";}function F(m){throw new Error("FAIL_CLOSED: "+m);}function Q(v){return '"'+String(v).replace(/\\/g,"\\\\").replace(/"/g,'\\"')+'"';}
function SQ(v){var q=String.fromCharCode(39),s=String.fromCharCode(92);return q+String(v).split(q).join(q+s+q+q)+q;}function H(p){var x=system.callSystem("/usr/bin/shasum -a 256 "+SQ(p)),m=x.match(/^([0-9a-f]{64})/i);if(!m)F("hash "+p);return m[1].toLowerCase();}
function W(p,t){var f=new File(p);f.encoding="UTF-8";if(!f.open("w"))F("write "+p);f.write(t);f.close();}
function R(comp,e,on,name){e.enabled=on;var q=app.project.renderQueue.items.add(comp),om=q.outputModule(1),p=E("CK_OUT")+"/"+name;om.applyTemplate("OLM EXR 32 Float");om.file=new File(p);var settings=om.getSettings(GetSettingsFormat.STRING);app.project.renderQueue.render();var f=new File(p);if(!f.exists){var a=f.parent.getFiles(f.name+"*");if(a.length!==1)F("render cardinality "+a.length);f=a[0];}q.remove();return {path:f.fsName,sha256:H(f.fsName),settings:settings};}
try{var S=SPEC,input=new File(E("CK_INPUT")),result=E("CK_RESULT"),binary=new File(E("CK_BINARY")),template=new File(E("CK_TEMPLATE"));if(!input.exists||H(input.fsName)!==S.input_sha||H(binary.fsName)!==EXPECTED||!template.exists)F("identity");if(app.project)try{app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);}catch(_e){}
var p=app.open(template);p.bitsPerChannel=16;p.workingSpace="";p.linearBlending=false;p.gpuAccelType=GpuAccelType.SOFTWARE;if(p.bitsPerChannel!==16||Number(p.gpuAccelType)!==Number(GpuAccelType.SOFTWARE))F("project contract");var ft=null,c=null;for(var ii=1;ii<=p.numItems;ii++){var it=p.item(ii);if(it.name==="OLM_COLOR_PROBE_INPUT")ft=it;if(it.name==="OLM_COLOR_PROBE_COMP")c=it;}if(!ft||!c)F("Preserve RGB template items");ft.replace(input);c.width=4;c.height=4;c.duration=1;c.frameRate=1;var l=c.layer(1);l.property("ADBE Transform Group").property("ADBE Position").setValue([2,2]);while(p.renderQueue.numItems)p.renderQueue.item(p.renderQueue.numItems).remove();var parade=l.property("ADBE Effect Parade");while(parade.numProperties)parade.property(parade.numProperties).remove();var fx=parade.addProperty("OLM Color Keep");if(!fx||fx.matchName!=="OLM Color Keep"||fx.numProperties!==102)F("effect surface");fx.property(1).setValue(S.keys.length);var read=[];for(var i=0;i<S.keys.length;i++){var k=S.keys[i];fx.property(i+2).setValue([k[0],k[1],k[2],1]);var v=fx.property(i+2).value;if(Math.abs(v[0]-k[0])>1e-7||Math.abs(v[1]-k[1])>1e-7||Math.abs(v[2]-k[2])>1e-7)F("RGB readback "+i);read.push([v[0],v[1],v[2]]);}var no=R(c,fx,false,"control.exr"),yes=R(c,fx,true,"effect_on.exr");W(result,JSON.stringify({status:"candidate_return_only",ae_exact_claim:false,ae_version:app.version,bits_per_channel:p.bitsPerChannel,renderer:"SOFTWARE",working_space:"None",linear_blending:p.linearBlending,plugin_sha256:H(binary.fsName),input_interpretation:"hash_bound_preserve_rgb_template",template_sha256:H(template.fsName),public_rgb_readback:read,outputs:{control:no,effect_on:yes}}));try{p.close(CloseOptions.DO_NOT_SAVE_CHANGES);}catch(_c){}
}catch(e){W(E("CK_ERROR"),String(e)+" line="+String(e.line||""));}}());'''.replace("SPEC", json.dumps(spec, separators=(",", ":"))).replace("EXPECTED", json.dumps(EXPECTED_SHA))


def compare(left: Path, right: Path) -> dict:
    spec = importlib.util.spec_from_file_location("ck_compare_exr", ROOT / "scripts/compare_float_exr.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module.compare(left, right)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--existing-pid", type=int)
    parser.add_argument("--support-dir", type=Path)
    args = parser.parse_args()
    try:
        fixture, installed = preflight()
    except Exception as exc:
        print(f"[FAIL_CLOSED] {exc}"); return 1
    support = (args.support_dir or Path(tempfile.mkdtemp(prefix="colorkeep_pf16_extended_"))).resolve(); support.mkdir(parents=True, exist_ok=True)
    script = support / "run.jsx"; result = support / "candidate_return.json"; error = support / "error.log"; out = support / "output"; out.mkdir(exist_ok=True)
    script.write_text("\n".join([f'$.setenv("CK_INPUT",{json.dumps(str(ROOT / fixture["artifacts"]["input_pf16_units_as_float.exr"]["path"]))});', f'$.setenv("CK_OUT",{json.dumps(str(out))});', f'$.setenv("CK_RESULT",{json.dumps(str(result))});', f'$.setenv("CK_ERROR",{json.dumps(str(error))});', f'$.setenv("CK_BINARY",{json.dumps(str(BINARY))});', f'$.setenv("CK_TEMPLATE",{json.dumps(str(PRESERVE_TEMPLATE))});', jsx(fixture)]), encoding="utf-8")
    print(json.dumps({"status": "prepared_not_executed" if not args.execute else "execution_requested", "support_dir": str(support), "installed_sha256": EXPECTED_SHA, "separate_padding_leg_sha256": installed["installed_output_sha256"]}, indent=2))
    if not args.execute:
        return 0
    try:
        pid = one_ae_pid()
        if args.existing_pid != pid:
            raise RuntimeError("--existing-pid must explicitly name the released AE process")
        mapping(pid, False)
        command = 'with timeout of 7200 seconds\ntell application "Adobe After Effects 2026" to DoScriptFile POSIX file ' + json.dumps(str(script)) + ' with override\nend timeout\n'
        run = subprocess.run(["osascript"], input=command, text=True, capture_output=True, timeout=7200)
        if run.returncode or not result.is_file():
            raise RuntimeError(error.read_text() if error.is_file() else run.stderr or "AE return missing")
        loaded = mapping(pid, True); returned = json.loads(result.read_text())
        control = compare(ROOT / fixture["artifacts"]["input_pf16_units_as_float.exr"]["path"], Path(returned["outputs"]["control"]["path"]))
        effect = compare(ROOT / fixture["artifacts"]["expected_actual_aex_pf16_units_as_float.exr"]["path"], Path(returned["outputs"]["effect_on"]["path"]))
        exact = control["mismatched_values"] == effect["mismatched_values"] == 0
        returned.update({"status": "host_active_pixels_exact" if exact else "host_conversion_or_effect_mismatch", "ae_exact_claim": False, "loaded_plugin_proof": loaded, "comparisons": {"input_control": control, "actual_aex_effect": effect}, "separate_installed_padding_leg": str(INSTALLED_LEG.relative_to(ROOT)), "padding_observed_by_ae": False})
        result.write_text(json.dumps(returned, indent=2, sort_keys=True) + "\n")
        if not exact:
            raise RuntimeError("raw FLOAT32 comparison mismatch")
    except Exception as exc:
        print(f"[FAIL_CLOSED] {exc}"); return 1
    print(f"[OK] AE-observable PF16 active pixels exact: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
