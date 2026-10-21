#!/usr/bin/env python3
"""Close the retained full-HD PF8 legacy-12 Smart/presentation relation."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
DIRECT = ROOT / "tools/emulation/olmsmoother2_case07_pf8_normalized_direct_probe_20260814.cpp"
PUBLIC = ROOT / "tools/emulation/olmsmoother2_pf8_legacy12_public_smart_harness_20260814.cpp"
REF = ROOT / "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/OLMSmootherv2"
MANIFEST = REF / "reference_manifest.json"
INPUT_PNG = REF / "input\\current_olm_cells.png"
REPORT = ROOT / "refs/conformance/olmsmoother2_pf8_legacy12_public_closure_20260814.json"
DOC = REPORT.with_suffix(".md")
SOURCE_SHA = "c710902f5928c67ae72e2e4ba445e801acd4a3f229f04d23ab6a1cd56cf73168"
INPUT_SHA = "1c15f67a9d0818a0a0266971720e855acac70a89e2690ccbedf5e142fc1c64f3"
DIRECT_SHAS = [
    "93f6b8dc4c258adf94f2aada8454394b58f5388128e46c980769490998b8b43b",
    "04a1eb8eed6e5b39b700efe557e4cdc17a6a4f6d7d4814108b20addbc8274988",
    "c9aae14a55d447faaa79d2c28331f5d91cb040eb0ebf5aebf87ba631bcbf0755",
    "cdcf1c120b7e7f59b7d73ae1b46e6f8fe3ffc809a53aa2b0e6a7ffb1d7e38b64",
    "8aedc3f58fb52f6fb374f55af634564ce98978002f9f492895daae87327acbc2",
    "d62bebdf630f08aef989229fb950efe79c038c4cc9efef5cd3d27fdccd19248f",
    "c8e87d45a6d2fed12e57a2e32880048ba70150d7e7337a9936471228c240902c",
    "9406ce4d6c5e50e3be5dc96a6e98a41869976dd797be4fe4b4363ec263230bc0",
    "f06b05eb681d29a18765a51d3469cf82f4a90828dd3e29ccc978544acbabc123",
    "495248cf85e33b6d73cfbe174bfea8279f10d235beca796a5866bb4ab3915b2e",
    "788423e8bf3e1ecdc1032409b9db587cd451285e61a7e2ebe6c1734aa0e22e7d",
    "5680e178cc246dc08d42845568f0c5df581e6f1023c7f2573d4cd9028b93b92f",
]
CASE_IDS = [
    "legacy_case_0001_current_aex", "legacy_case_0002_current_aex",
    "legacy_case_0003_current_aex", "legacy_case_0004_current_aex",
    "legacy_case_0005_current_aex", "legacy_case_0006_current_aex",
    "legacy_case_0007_current_aex", "legacy_case_0008_current_aex",
    "legacy_case_0009_v1mode_current_aex", "legacy_case_0010_gamma3_current_aex",
    "legacy_case_0011_gamma5_blue_current_aex", "legacy_case_0012_gamma5_red_blue_current_aex",
]
PUBLIC_NAMES = ([x for n in range(1, 13) for x in (f"case{n:02d}", f"case{n:02d}_gamma_next")] +
    ["source_first", "source_middle", "source_last", "key_one", "palette_one",
     "width_one", "rowbytes_one", "input_flags_one", "output_flags_one", "origin_one",
     "downsample_one", "extent_one", "format_one", "alias", "overlap", "layer_error",
     "output_error", "param_checkout_error", "param_checkin_error", "world_error",
     "color_error", "color_wrong_success"])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgba_to_argb(path: Path) -> bytes:
    image = Image.open(path).convert("RGBA")
    if image.size != (1920, 1080): raise ValueError("unexpected PNG dimensions")
    return b"".join(bytes((a, r, g, b)) for r, g, b, a in image.getdata())


def premultiply(data: bytes) -> bytes:
    result = bytearray(data)
    for offset in range(0, len(result), 4):
        alpha = result[offset]
        for channel in (1, 2, 3):
            result[offset + channel] = (result[offset + channel] * alpha + 127) // 255
    return bytes(result)


def color_arg(value: list[float]) -> str:
    r, g, b, a = [max(0, min(255, round(float(x) * 255))) for x in value]
    return f"{a:02x}{r:02x}{g:02x}{b:02x}"


def params(case: dict) -> list[str]:
    values: dict[str, object] = {}; gamma: list[list[float]] = []
    for item in case["effects"][0]["params"]:
        if item["name"] == "Gamma Color": gamma.append(item["value"])
        else: values[item["name"]] = item["value"]
    return [str(int(values["Enable Color Key"])), str(int(values["Invert Color Key"])),
        str(int(values["Smoothness"])), str(int(values["Extra Smooth"])),
        str(int(values["Smooth Range"])), str(int(values["Smoother Version"])),
        str(int(values["Gamma Correction"])), repr(float(values["Gamma Value"])),
        str(int(values["Number of Gamma Colors"])), color_arg(values["Color Key"]),
        *[color_arg(x) for x in gamma]]


def generate() -> dict:
    if sha256(SOURCE) != SOURCE_SHA: raise ValueError("source identity drift")
    manifest = json.loads(MANIFEST.read_text())
    cases = manifest["cases"]
    if [case["id"] for case in cases] != CASE_IDS: raise ValueError("case order drift")
    source = rgba_to_argb(INPUT_PNG)
    if hashlib.sha256(source).hexdigest() != INPUT_SHA: raise ValueError("input decode drift")
    with tempfile.TemporaryDirectory(prefix="olmsmoother2-pf8-legacy12.") as td:
        work = Path(td); input_raw = work / "source.argb8"; input_raw.write_bytes(source)
        direct_bin = work / "direct"
        subprocess.run(["clang++","-std=c++17","-O2","-I","cli/OLMSmoother2/shim",str(DIRECT),"-o",str(direct_bin)],cwd=ROOT,check=True,capture_output=True,text=True)
        rows=[]
        for index, case in enumerate(cases):
            output = work / f"case{index+1:02d}.argb8"
            run=subprocess.run([str(direct_bin),str(input_raw),str(output),*params(case)],cwd=ROOT,check=True,capture_output=True,text=True)
            direct=output.read_bytes(); target=rgba_to_argb(REF/case["frame"])
            direct_sha=hashlib.sha256(direct).hexdigest(); target_sha=hashlib.sha256(target).hexdigest()
            if direct_sha != DIRECT_SHAS[index] or premultiply(direct) != target: raise ValueError(f"case {index+1} relation drift")
            rows.append({"case_id":case["id"],"direct_argb8_sha256":direct_sha,
                "windows_effect_png_sha256":sha256(REF/case["frame"]),
                "windows_effect_decoded_argb8_sha256":target_sha,"bytes":len(direct),
                "presentation_mismatches":0,"max_byte_delta":0})
        public_bin=work/"public"
        sdk=subprocess.run(["xcrun","--show-sdk-path"],capture_output=True,text=True,check=True).stdout.strip()
        command=["clang++","-std=c++17","-arch","arm64","-O2","-Wno-pragma-pack","-Wno-deprecated-declarations","-isysroot",sdk,
            "-IHeaders","-IHeaders/SP","-IUtil","-IResources","-Imac/OLMSmoother2",str(PUBLIC),
            "mac/OLMSmoother2/OLMSmoother2_Strings.cpp","Util/AEGP_SuiteHandler.cpp","Util/MissingSuiteError.cpp","-framework","Cocoa","-o",str(public_bin)]
        subprocess.run(command,cwd=ROOT,check=True,capture_output=True,text=True)
        public=subprocess.run([str(public_bin),str(input_raw)],cwd=ROOT,check=True,capture_output=True,text=True)
        public_rows=[]
        for line in public.stdout.splitlines():
            if line.startswith("CASE "):
                fields=line.split();public_rows.append({"name":fields[1],"pass":fields[2]=="pass=1","err":int(fields[3].split("=",1)[1])})
        if [x["name"] for x in public_rows] != PUBLIC_NAMES or not all(x["pass"] for x in public_rows): raise ValueError("public transcript drift")
        return {"schema":"olmsmoother2.pf8-legacy12-public/1","status":"pass_exact12_public_smart_host_presentation",
            "production_source":{"path":str(SOURCE.relative_to(ROOT)),"sha256":SOURCE_SHA},
            "dependencies":{"manifest":{"path":str(MANIFEST.relative_to(ROOT)),"sha256":sha256(MANIFEST)},
                "input_png":{"path":str(INPUT_PNG.relative_to(ROOT)),"sha256":sha256(INPUT_PNG)},
                "direct_harness":{"path":str(DIRECT.relative_to(ROOT)),"sha256":sha256(DIRECT)},
                "public_harness":{"path":str(PUBLIC.relative_to(ROOT)),"sha256":sha256(PUBLIC)}},
            "input":{"dimensions":[1920,1080],"rowbytes":7680,"bytes":8294400,"decoded_argb8_sha256":INPUT_SHA},
            "cases":rows,"case_count":12,"presentation":{"expression":"(rgb * alpha + 127) // 255","compared_bytes":99532800,"mismatches":0,"max_byte_delta":0},
            "public_cases":public_rows,"public_positive_count":12,"public_negative_count":34,
            "public_transcript_sha256":hashlib.sha256(public.stdout.encode()).hexdigest(),
            "claims_not_made":["No native Windows output-world memory capture","No arbitrary source, tuple, geometry, or depth claim","No install, After Effects launch, or release claim"]}


def validate(data: dict) -> bool:
    try:
        if set(data) != {"schema","status","production_source","dependencies","input","cases","case_count","presentation","public_cases","public_positive_count","public_negative_count","public_transcript_sha256","claims_not_made"}: return False
        if data["schema"]!="olmsmoother2.pf8-legacy12-public/1" or data["status"]!="pass_exact12_public_smart_host_presentation": return False
        if data["production_source"]!={"path":str(SOURCE.relative_to(ROOT)),"sha256":SOURCE_SHA} or sha256(SOURCE)!=SOURCE_SHA: return False
        for item in data["dependencies"].values():
            path=ROOT/item["path"]
            if set(item)!={"path","sha256"} or not path.is_file() or sha256(path)!=item["sha256"]: return False
        if data["input"]!={"dimensions":[1920,1080],"rowbytes":7680,"bytes":8294400,"decoded_argb8_sha256":INPUT_SHA}: return False
        if data["case_count"]!=12 or [x.get("case_id") for x in data["cases"]]!=CASE_IDS: return False
        if [x.get("direct_argb8_sha256") for x in data["cases"]]!=DIRECT_SHAS: return False
        if any(set(x)!={"case_id","direct_argb8_sha256","windows_effect_png_sha256","windows_effect_decoded_argb8_sha256","bytes","presentation_mismatches","max_byte_delta"} or x["bytes"]!=8294400 or x["presentation_mismatches"]!=0 or x["max_byte_delta"]!=0 for x in data["cases"]): return False
        for row,case in zip(data["cases"],json.loads(MANIFEST.read_text())["cases"]):
            if row["windows_effect_png_sha256"]!=sha256(REF/case["frame"]): return False
            if row["windows_effect_decoded_argb8_sha256"] != hashlib.sha256(
                    rgba_to_argb(REF / case["frame"])).hexdigest(): return False
        if data["presentation"]!={"expression":"(rgb * alpha + 127) // 255","compared_bytes":99532800,"mismatches":0,"max_byte_delta":0}: return False
        if data["public_positive_count"]!=12 or data["public_negative_count"]!=34 or [x.get("name") for x in data["public_cases"]]!=PUBLIC_NAMES: return False
        if any(set(x)!={"name","pass","err"} or x["pass"] is not True for x in data["public_cases"]): return False
        if data["claims_not_made"]!=["No native Windows output-world memory capture","No arbitrary source, tuple, geometry, or depth claim","No install, After Effects launch, or release claim"]: return False
        return isinstance(data["public_transcript_sha256"],str) and len(data["public_transcript_sha256"])==64
    except (KeyError,TypeError,ValueError,OSError): return False


def markdown(data: dict) -> str:
    return f"""# OLMSmoother2 PF8 retained legacy-12 public closure — 2026-08-14

- Status: `{data['status']}`
- Exact source: `{INPUT_SHA}`; fixed 1920x1080 tight ARGB8.
- Twelve current-source direct outputs map to the twelve retained current-AEX PNGs through nearest-code premultiplication with `99,532,800/99,532,800` bytes exact.
- Real-SDK public Smart closure: 12 positives and 34 fail-closed controls.
- Boundary: this is a full host-presentation relation, not a native Windows output-world capture or arbitrary-input claim. No install or AE launch occurred.
"""


def main() -> int:
    parser=argparse.ArgumentParser();parser.add_argument("--write",action="store_true");args=parser.parse_args()
    if args.write:
        data=generate();REPORT.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n");DOC.write_text(markdown(data));print(data["status"]);return 0
    if not REPORT.is_file(): print("FAIL_CLOSED missing report");return 1
    data=json.loads(REPORT.read_text());ok=validate(data);print("PASS_VALIDATE_ONLY" if ok else "FAIL_CLOSED");return 0 if ok else 1


if __name__=="__main__": raise SystemExit(main())
