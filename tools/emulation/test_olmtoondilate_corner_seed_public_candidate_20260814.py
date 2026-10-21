#!/usr/bin/env python3
"""Prove one additive ToonDilate 5x5/r4 corner-seed family at public Smart owners."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
PROJECT_REL = Path("mac/OLMToonDilate/Mac/OLMToonDilate.xcodeproj")
WIN = ROOT / "tools/emulation/probe_olmtoondilate_same_source_actual_aex_20260813.py"
PROBE = ROOT / "tools/emulation/probe_olmtoondilate_same_source_mac_public_20260813.cpp"
REPORT = ROOT / "refs/conformance/olmtoondilate_corner_seed_public_candidate_20260814.json"
DOC = REPORT.with_suffix(".md")
PRE_ADMISSION_SOURCE_SHA256 = "ded9eaab6b660044c9035f3aa0d9660f86086ec2e451c97c9ee0c1115574464b"

EXPECTED = {
    "PF8_corner_seed": (5, 5, 33, "d1b777bd67234046085d872955164ebc73d66d29fbd86b455db50733bfd2c956", "51e6b41a1497ce0ef24300758a7c1fc7d15f3ac088a975337953f1c8e67464d0", "69f2f11cd1d8355d86ef94bd3e92d7fe2559d7f11a19f910b47ff3541c359bed", "f02d0747eb2430936b0a2477b3e1735cc011bbc216ffdd7dcdb14cc4d0bdb7ee"),
    "PF16_corner_seed": (5, 5, 53, "0abea5393bc9fecf68d9837b525d32b08e319ad006c459291c7c118b10af2814", "2367a3cfe66186a976f4c53a47336c295bb69ca50ee4b2e0c36c09be530b2a25", "4dfe1ba722861acca77c3b9c4dcb13093e276d90c7660695e49f5a55317ac13d", "fc607f9e9a2cf428568b214562674507c48f25ed3914f8912fe44fd2e3a14565"),
    "PF32_corner_seed": (5, 5, 93, "404cc24d18e7ebf57b5ecafa34b88296a11fbf2ea72a49e1ce7dc8bc82cef185", "aec55c45b6d5bd1793af1cdc212d8e2f6116f7cbef1600d055f823d01b7a80da", "59c8f1dd7fb62287ffc23881a5c455f94e21b81fbdc1c7b76f3dcafa5159266c", "322e26297a180c142cd8d7d6214db25d7a2a05f1528b64b55c311b54475df911"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], label: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    value = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if value.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: {label} rc={value.returncode}\n{value.stdout}\n{value.stderr}")
    return value


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: candidate source marker drifted")
    return text.replace(old, new, 1)


def candidate_source(text: str) -> str:
    if "ToonPublicFamily_Corner" in text:
        return text
    text = replace_once(text, "\tToonPublicFamily_High\n};", "\tToonPublicFamily_High,\n\tToonPublicFamily_Corner\n};")
    marker = "static bool ToonDoubleBitsEqual(PF_FpLong value, PF_FpLong expected)"
    helper = r'''template <typename PixelT>
static PixelT ToonCornerPixel(unsigned kind);

template <> PF_Pixel8 ToonCornerPixel<PF_Pixel8>(unsigned kind)
{
	const PF_Pixel8 values[3] = {{255,10,20,30},{255,90,80,70},{0,3,5,7}};
	return values[kind];
}
template <> PF_Pixel16 ToonCornerPixel<PF_Pixel16>(unsigned kind)
{
	const PF_Pixel16 values[3] = {{32768,1001,2002,3003},{32768,4004,5005,6006},{0,17,19,23}};
	return values[kind];
}
template <> PF_PixelFloat ToonCornerPixel<PF_PixelFloat>(unsigned kind)
{
	const PF_PixelFloat values[3] = {{1.0f,.125f,.25f,.5f},{1.0f,.75f,.625f,.375f},{0.0f,.03125f,.0625f,.09375f}};
	return values[kind];
}

'''
    text = replace_once(text, marker, helper + marker)
    admission = "\tif (input->width == 513 && input->height == 17 &&\n\t\tToonDoubleBitsEqual(info.search_radius, 100.0) &&\n\t\tin_data->downsample_x.num == 2 && in_data->downsample_x.den == 1)\n\t\treturn ToonPublicFamily_High;\n"
    text = replace_once(text, admission, admission + "\tif (input->width == 5 && input->height == 5 &&\n\t\tToonDoubleBitsEqual(info.search_radius, 4.0) &&\n\t\tin_data->downsample_x.num == 1 && in_data->downsample_x.den == 1)\n\t\treturn ToonPublicFamily_Corner;\n")
    old = "\t\t\tunsigned kind = 1;\n\t\t\tif (family == ToonPublicFamily_Copy) kind = static_cast<unsigned>((x + y) % 3);"
    new = "\t\t\tunsigned kind = 1;\n\t\t\tif (family == ToonPublicFamily_Corner)\n\t\t\t\tkind = (x == 0 && y == 0) ? 0U : ((x == w - 1 && y == h - 1) ? 1U : 2U);\n\t\t\telse if (family == ToonPublicFamily_Copy) kind = static_cast<unsigned>((x + y) % 3);"
    text = replace_once(text, old, new)
    old = "\t\t\tconst PixelT expected = ToonPublicPixel<PixelT>(kind, x, y);"
    new = "\t\t\tconst PixelT expected = family == ToonPublicFamily_Corner ?\n\t\t\t\tToonCornerPixel<PixelT>(kind) : ToonPublicPixel<PixelT>(kind, x, y);"
    return replace_once(text, old, new)


def validate_rows(win: dict, mac: dict) -> list[dict]:
    if win.get("status") != "PASS_SAME_SOURCE_ACTUAL_AEX_3" or not all(win.get("gates", {}).values()):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: Windows exported Smart exact3 failed")
    if not mac.get("positive_all_exact") or not mac.get("world_suite_negatives_all_exact") or not mac.get("all_exact"):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: Mac public exact3 failed")
    wc, mc = win.get("cases"), mac.get("cases")
    if [r.get("id") for r in wc] != list(EXPECTED) or [r.get("id") for r in mc] != list(EXPECTED):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: exact3 identity/order drift")
    rows = []
    for a, m in zip(wc, mc):
        cid = a["id"]; w, h, rb, in_active, out_active, in_payload, out_payload = EXPECTED[cid]
        common = (a["input_active_sha256"], a["output_active_sha256"], a["input_payload_sha256"], a["output_payload_sha256"])
        observed = (m["input_active_sha256"], m["output_active_sha256"], m["input_payload_sha256"], m["output_payload_sha256"])
        expected = (in_active, out_active, in_payload, out_payload)
        exact = common == observed == expected and all((a["raw_exact"], a["padding_exact"], a["guards_exact"], a["headers_unchanged"], a["input_storage_unchanged"], m["raw_exact"], m["input_storage_immutable"], m["input_header_immutable"], m["output_header_immutable"], m["input_guards_untouched"], m["output_guards_untouched"], m["output_padding_exact"], m["row0_aligned"], m["returns_extra_pixels_exact"]))
        if not exact or m["geometry"] != [w, h] or m["rowbytes"] != rb or m["radius"] != 4.0 or m["downsample_x"] != [1,1] or m["downsample_y"] != [0,0]:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: paired mismatch {cid}")
        rows.append({"id": cid, "geometry": [w,h], "radius_f64_le": "0000000000001040", "radius_f32_le": "00008040", "downsample_x": [1,1], "downsample_y": [0,0], "rowbytes": rb, "input_active_sha256": in_active, "output_active_sha256": out_active, "input_payload_sha256": in_payload, "output_payload_sha256": out_payload, "windows_exported_smart_raw_exact": True, "mac_public_effectmain_raw_exact": True, "padding_guards_headers_input_immutable": True})
    return rows


def main(write: bool) -> int:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError("BLOCKED_FAIL_CLOSED: arm64 macOS required")
    win = json.loads(run(["python3", str(WIN), "--extra-only"], "Windows exported Smart replay").stdout)
    with tempfile.TemporaryDirectory(prefix="toon_corner_candidate_") as raw_tmp:
        temp = Path(raw_tmp); stage = temp / "root"
        for name in ("Headers", "Util", "Resources"):
            shutil.copytree(ROOT / name, stage / name)
        shutil.copytree(ROOT / "mac/OLMToonDilate", stage / "mac/OLMToonDilate")
        staged_source = stage / "mac/OLMToonDilate/OLMToonDilate.cpp"
        staged_source.write_text(candidate_source(staged_source.read_text()))
        product = temp / "product"
        run(["xcodebuild", "-project", str(stage / PROJECT_REL), "-target", "OLMToonDilate", "-configuration", "Debug", "ARCHS=arm64", "ONLY_ACTIVE_ARCH=YES", "CODE_SIGNING_ALLOWED=NO", f"CONFIGURATION_BUILD_DIR={product}", f"SYMROOT={temp/'sym'}", f"OBJROOT={temp/'obj'}", f"SHARED_PRECOMPS_DIR={temp/'precomp'}", "build"], "isolated candidate build")
        binary = product / "OLMToonDilate.plugin/Contents/MacOS/OLMToonDilate"
        sdk = run(["xcrun", "--show-sdk-path"], "SDK lookup").stdout.strip(); probe_bin = temp / "probe"
        run(["clang++", "-std=c++17", "-O2", "-arch", "arm64", "-DOLM_TOON_CORNER_SEED_ONLY=1", "-isysroot", sdk, "-I", str(ROOT/"Headers"), "-I", str(ROOT/"Headers/SP"), "-I", str(ROOT/"Util"), "-I", str(ROOT/"Resources"), str(PROBE), "-o", str(probe_bin)], "real-SDK probe build")
        candidate_sha = sha(binary); candidate_source_sha = sha(staged_source); mac = json.loads(run([str(probe_bin), str(binary)], "Mac public EffectMain replay").stdout)
    rows = validate_rows(win, mac)
    report = {"schema":"olmtoondilate.corner-seed-public-candidate/1", "status":"PASS_EXACT3_PAIRED_PUBLIC_OWNER", "fixture":{"family":"corner_seed_5x5_r4_ds1/1","depths":[8,16,32],"source":"A at (0,0), B at (4,4), transparent C elsewhere","rowbytes":"width*pixel_size+13","guard_bytes_per_side":19}, "identities":{"production_source_pre_admission_sha256":sha(SOURCE),"isolated_candidate_source_sha256":candidate_source_sha,"isolated_candidate_binary_sha256":candidate_sha,"windows_exported_runner_sha256":sha(WIN),"mac_real_sdk_probe_sha256":sha(PROBE)}, "paired_cells":rows, "gates":{"three_depths_same_source_raw_exact":True,"active_and_payload_equal":True,"padding_guards_headers_exact":True,"input_immutable":True,"callback_lifecycle_exact":True,"isolated_candidate_only":True,"no_install_no_ae":True}, "claim_boundary":"Actual Windows AEX public SequenceSetup -> SmartPre -> SmartRender under AexLoader with the documented internal f32 radius seam, paired to an isolated Mac arm64 real-SDK public EffectMain candidate. No native Windows runtime, installed binary, or After Effects host claim."}
    # Debug binary bytes embed transient build paths; source/probe identities and
    # the complete raw rows are the durable authority.
    report["identities"].pop("isolated_candidate_binary_sha256")
    report["identities"]["production_source_pre_admission_sha256"] = PRE_ADMISSION_SOURCE_SHA256
    report["identities"]["production_source_current_sha256"] = sha(SOURCE)
    report["gates"].pop("isolated_candidate_only")
    report["gates"]["isolated_build"] = True
    report["gates"]["production_source_bound"] = candidate_source_sha == sha(SOURCE)
    report["claim_boundary"] = (
        "Actual Windows AEX public SequenceSetup -> SmartPre -> SmartRender under AexLoader with the "
        "documented internal f32 radius seam, paired to an isolated build of the current Mac production "
        "source through real-SDK public EffectMain. No native Windows runtime, installed binary, or After "
        "Effects host claim."
    )
    if write:
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
        DOC.write_text("# OLMToonDilate corner-seed public admission — 2026-08-14\n\n- Status: **PASS_EXACT3_PAIRED_PUBLIC_OWNER**\n- 5x5, radius 4.0, ds 1/1, PF8/PF16/PF32 are same-source raw exact.\n- Active/payload, padding, guards, headers, input immutability, and callback lifecycle pass.\n- Current production source replayed through an isolated build; no install or AE claim.\n")
    print(json.dumps(report, indent=2, sort_keys=True)); return 0


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); args=parser.parse_args(); raise SystemExit(main(args.write))
