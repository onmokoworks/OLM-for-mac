#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import argparse, hashlib, importlib.util, json, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
PROBE = ROOT / "tools/emulation/probe_olmradialblur_type1_dual_strength_source_guard_20260813.cpp"
REPORT = ROOT / "refs/conformance/olmradialblur_type1_dual_strength_source_guard_20260813.json"
DOC = REPORT.with_suffix(".md")
PLAIN_TOOL = ROOT / "tools/emulation/test_olmradialblur_offcenter_brightness_actual_aex_20260811.py"
COMP_TOOL = ROOT / "tools/emulation/probe_olmradialblur_rotation_size_variation_components_actual_aex_20260811.py"
SOURCE_SHA = "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1"
TRANSCRIPT_SHA = "9f4cc9d4391416c68c4d5c6de0a6698c557efc5bb62c075a32e7672bf9ac8404"
EXPECTED = {
    "PF8_plain": "85143eda82a237f32b5c9b1d3cf5f73a121bffa9eaba6e05d4728bda4216f000",
    "PF8_component": "11dcefe50c65d40f9a695b183f9c95de7cdd51d4c85448e87641dccf04468444",
    "PF16_plain": "c9d92745cba73fde78d7ad5868d643ad7a88b1dd481e6caacfc7c945ae153b3c",
    "PF16_component": "1d745a0b5399ed3040b85175c700f8ae403fccede8d115fb1deb99c4d2ac6356",
    "PF32_plain": "4a7af04987dad9d83589e8609698abaff3f3d89547143c8ad44255bbc62c73f7",
    "PF32_component": "187a7caf98537700d3644aed245150467f284b87ef73df56e46dd331ba40cf1f",
}
BOUNDARY = {
    "proven": "18 fixed Type1 dual-strength cells retain their pre-guard outputs and 18 source mutations fail closed on arm64 and x86_64",
    "not_proven": ["arbitrary sources", "native After Effects", "installed candidate", "other Type1 families"],
}

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path: Path, name: str):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec)
    assert spec.loader; spec.loader.exec_module(mod); return mod

def active(raw: bytes, rb: int, n: int) -> str:
    return hashlib.sha256(b"".join(raw[y*rb:y*rb+n] for y in range(18))).hexdigest()

def reconstruct() -> dict[str,str]:
    plain=load(PLAIN_TOOL,"radial_dual_plain"); comp=load(COMP_TOOL,"radial_dual_component")
    out={}
    for depth in (8,16,32):
        pb={8:4,16:8,32:16}[depth]; rb=32*pb+({8:8,16:16,32:16}[depth])
        out[f"PF{depth}_plain"]=active(plain.frame_for(depth,"rotation",32,18,rb)(),rb,32*pb)
        out[f"PF{depth}_component"]=active(comp.component_frame(depth,rb),rb,32*pb)
    return out

def run(arch: str) -> list[str]:
    with tempfile.TemporaryDirectory(prefix=f"radial-dual-guard-{arch}.") as raw:
        exe=Path(raw)/"probe"; sdk=subprocess.check_output(["xcrun","--show-sdk-path"],text=True).strip()
        cmd=[_UCRT_CXX,"-std=c++17","-arch",arch,"-O2","-fno-fast-math","-ffp-contract=off","-isysroot",sdk,
             "-Wno-pragma-pack","-Wno-deprecated-declarations","-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),
             "-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),"-I",str(ROOT/"core"),"-I",str(ROOT/"mac/OLMRadialBlur"),
             str(PROBE),str(ROOT/"mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp"),str(ROOT/"Util/AEGP_SuiteHandler.cpp"),
             str(ROOT/"Util/MissingSuiteError.cpp"),"-framework","Cocoa","-o",str(exe)]
        built=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
        if built.returncode: raise RuntimeError(built.stdout+built.stderr)
        observed=subprocess.run([str(exe)],cwd=ROOT,capture_output=True,text=True)
        if observed.returncode: raise RuntimeError(observed.stdout+observed.stderr)
    if hashlib.sha256(observed.stdout.encode()).hexdigest()!=TRANSCRIPT_SHA: raise RuntimeError("transcript drift")
    lines=observed.stdout.splitlines()
    if len(lines)!=36 or sum(x.startswith("POS ") for x in lines)!=18 or sum(x.startswith("NEG ") for x in lines)!=18:
        raise RuntimeError("row drift")
    return lines

def generate() -> dict:
    identities=reconstruct()
    if identities!=EXPECTED or sha(SOURCE)!=SOURCE_SHA: raise RuntimeError("source identity drift")
    text=SOURCE.read_text()
    for token in ("MatchesRadial32x18PlainOrComponentFixture<PixelT>(input, info.size_variation != 0.0)",*EXPECTED.values()):
        if token not in text: raise RuntimeError(f"guard token missing: {token}")
    return {"schema":"olmradialblur.type1-dual-strength-source-guard/1","status":"pass_hostless",
            "authorities":{"production_sha256":sha(SOURCE),"probe_sha256":sha(PROBE),
                           "plain_generator_sha256":sha(PLAIN_TOOL),"component_generator_sha256":sha(COMP_TOOL)},
            "active_source_sha256":identities,"runs":[{"arch":a,"lines":run(a),"transcript_sha256":TRANSCRIPT_SHA}
                                                        for a in ("arm64","x86_64")],
            "positive_cells_per_arch":18,"mutation_rejects_per_arch":18,"claim_boundary":BOUNDARY,
            "promotion_state":"hostless_closed_universal_rebuild_and_install_pending"}

def validate(value: dict) -> None:
    if set(value)!={"schema","status","authorities","active_source_sha256","runs",
                   "positive_cells_per_arch","mutation_rejects_per_arch","claim_boundary","promotion_state"}:
        raise RuntimeError("schema drift")
    if value["schema"]!="olmradialblur.type1-dual-strength-source-guard/1" or value["status"]!="pass_hostless":
        raise RuntimeError("status drift")
    if value["authorities"]!={"production_sha256":sha(SOURCE),"probe_sha256":sha(PROBE),
                              "plain_generator_sha256":sha(PLAIN_TOOL),"component_generator_sha256":sha(COMP_TOOL)}:
        raise RuntimeError("authority drift")
    if value["active_source_sha256"]!=EXPECTED or value["claim_boundary"]!=BOUNDARY:
        raise RuntimeError("source or claim drift")
    if value["positive_cells_per_arch"]!=18 or value["mutation_rejects_per_arch"]!=18 or \
       value["promotion_state"]!="hostless_closed_universal_rebuild_and_install_pending":
        raise RuntimeError("count or state drift")
    if [x.get("arch") for x in value["runs"]] != ["arm64","x86_64"]: raise RuntimeError("arch drift")
    for run_row in value["runs"]:
        if set(run_row)!={"arch","lines","transcript_sha256"} or run_row["transcript_sha256"]!=TRANSCRIPT_SHA:
            raise RuntimeError("run schema drift")
        raw=("\n".join(run_row["lines"])+"\n").encode()
        if hashlib.sha256(raw).hexdigest()!=TRANSCRIPT_SHA: raise RuntimeError("run transcript drift")

def markdown(v: dict) -> str:
    return "# RadialBlur Type1 dual-strength source guard\n\nStatus: `pass_hostless`\n\n"+\
        "Six exact PF8/PF16/PF32 plain/component active-row identities retain all 18 bounded outputs on both architectures. " +\
        "First/middle/last mutations of every source reject before output writes. Install and AE remain pending.\n"

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--write",action="store_true"); args=p.parse_args()
    fresh=generate()
    if args.write:
        REPORT.write_text(json.dumps(fresh,indent=2,sort_keys=True)+"\n"); DOC.write_text(markdown(fresh))
    else:
        saved=json.loads(REPORT.read_text()); validate(saved)
        if DOC.read_text()!=markdown(saved): raise RuntimeError("markdown drift")
    print("PASS_OLMRADIALBLUR_TYPE1_DUAL_STRENGTH_SOURCE_GUARD")
    return 0

if __name__=="__main__": raise SystemExit(main())
