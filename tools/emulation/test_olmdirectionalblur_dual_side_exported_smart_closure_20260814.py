#!/usr/bin/env python3
"""Close 15 DirectionalBlur dual-side cells through exported AEX Smart + Mac public."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "handoffs/olmdirectionalblur_exported_smart_worker_ceil_20260814/bin/aex-guest-worker"
WORKER_IDENTITY = ROOT / "handoffs/olmdirectionalblur_exported_smart_worker_ceil_20260814/build_identity.json"
PATCH = ROOT / "tools/emulation/aexcompat_olmdirectionalblur_double_ceil_import_20260814.patch"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE_PNG = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
PRODUCTION = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
FEATURE = ROOT / "tools/emulation/test_olmdirectionalblur_public_effectmain_feature_matrix_20260811.py"
PUBLIC32 = ROOT / "refs/conformance/olmdirectionalblur_public_effectmain_feature_matrix_20260811.json"
PUBLIC64 = ROOT / "refs/conformance/olmdirectionalblur_public_effectmain_dual_side_64x36_20260812.json"
FAIL_CLOSED = ROOT / "refs/conformance/olmdirectionalblur_dual_side_public_owner_boundary_20260814.json"
NATIVE_UCRT = ROOT / "refs/conformance/olmdirectionalblur_remaining6_native_ucrt_replay_20260815.json"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_dual_side_exported_smart_closure_20260814.json"
NOTE = REPORT.with_suffix(".md")

TUPLES = (
    (50, 50, 100, 100, 0, 25, 1),
    (50, 100, 50, 50, 50, 100, 2),
    (100, 50, 50, 100, 0, 100, 2),
    (100, 100, 100, 50, 50, 25, 1),
)
CONFIGS = ((32, 18, 1),) + tuple((64, 36, index) for index in range(4))
PUBLIC_ARCHES = ("arm64", "x86_64")
PROMOTED_ARM64 = {
    (width, tuple_index, depth)
    for width, _height, tuple_index in CONFIGS
    for depth in (8, 16, 32)
}
PROMOTED_X86_64 = PROMOTED_ARM64
PROMOTED_BY_ARCH = {"arm64": PROMOTED_ARM64, "x86_64": PROMOTED_X86_64}
EXPECTED_EXPORTED = {
    (32, 1, 8): "9834db6f461bdb35d6efdffd9e84515d8f56a16e9214dc7cbce98650829ddc1e",
    (32, 1, 16): "b632375e576257c251f6c01d535eab2cbf981f78edec9e5b2d5084b5f97d954c",
    (32, 1, 32): "0094576105d9cabecce0dea71c5b7352a2dcd2990b8eb4ff29b4a295a2e470d4",
    (64, 0, 8): "1697b835063aa0fb975a1785e9a374a2c4658ff6f9d79952f167b993144b2926",
    (64, 0, 16): "7393895df5581f2baa31aca43376c31c55755ee67e20b0f43d6664953a5e8311",
    (64, 0, 32): "05989b2976a2056c738a2c41cf6c9ac39a3fcf8caa35eba4ca1d828fecb9fe19",
    (64, 1, 8): "2f5c9ef8f69ccab111d2d230a542293fd8dd7377a5fd83be50940f5d053cc31a",
    (64, 1, 16): "eeea58c8cc7bc7a68f396e69b0e3d4446e7ee2c23387c17e320462222916188c",
    (64, 1, 32): "814ae4ec073d6e6ad4c83dea25227de5362d0ae6b8346d155c6aafe086149ac7",
    (64, 2, 8): "636e649414ff0ad3968aabb97733dbb67f92900898829361b3f44c58758cfdb3",
    (64, 2, 16): "4846a56aea99d2db6be3e56930a8ef1143394e89ca97e316d84a8ec165b4179d",
    (64, 2, 32): "453bbdf19955a3c6b91f2ca9b756e0d0aa9f2949b5855050636170a117039fc1",
    (64, 3, 8): "39e05b0f1b5bfbc8923cc11f7c43caa2eab6ca5de8c07111601a2e2d3418bfe7",
    (64, 3, 16): "d0b367cb47a3937b68159f02401d585b785ac063c6b8893afe8b03a5c93af592",
    (64, 3, 32): "3424989500b9b05791c1ce9e33e99fb810b5e3c63ad6b4e8c3897c6a2d832c09",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def historical_public_hashes() -> dict[tuple[int, int, int], str]:
    result: dict[tuple[int, int, int], str] = {}
    public64 = json.loads(PUBLIC64.read_text())
    for row in public64["cases"]:
        result[(64, row["tuple_index"], row["depth"])] = row["raw_sha256"]
    public32 = json.loads(PUBLIC32.read_text())
    for row in public32["cases"]:
        if row["kind"] == 0:
            result[(32, 1, row["depth"])] = row["raw_sha256"]
    return result


def native_ucrt_x86_hashes() -> dict[tuple[int, int, int], str]:
    report = json.loads(NATIVE_UCRT.read_text())
    if report.get("status") != "PASS_DIRECTIONAL_REMAINING6_NATIVE_UCRT_EXPORTED_AEX_MAC_DIRECT_RAW_EXACT":
        raise RuntimeError("native UCRT Directional authority")
    result = {(64, row["tuple_index"], row["depth"]): row["aex_raw_sha256"]
              for row in report["rows"]}
    if len(result) != 6 or not all(row["native_matches_preexisting_x86_raw"] for row in report["rows"]):
        raise RuntimeError("native UCRT Directional row closure")
    return result


def parameters(index: int) -> list[str]:
    ff, fs, bf, bs, size, variation, noise_type = TUPLES[index]
    return [
        "Angle@1=45", "Brightness Gain@2=1", f"Size Variation@3={size}",
        "Blur Strength@5=8", f"Alpha Fade@6={ff}", f"Sharp Tail@7={fs}",
        "Blur Strength@10=8", f"Alpha Fade@11={bf}", f"Sharp Tail@12={bs}",
        f"Noise Variation@15={variation}", f"Noise Type@16={noise_type}",
        "Seed@18=1", "Offset@19=0", "Thickness@20=3",
    ]


def run_exported(root: Path) -> list[dict[str, object]]:
    source = Image.open(SOURCE_PNG).convert("RGBA")
    historical = historical_public_hashes()
    rows: list[dict[str, object]] = []
    formats = ((8, "argb8"), (16, "argb16"), (32, "argb32f"))
    for width, height, tuple_index in CONFIGS:
        input_png = root / f"input-{width}x{height}-t{tuple_index}.png"
        source.crop((472, 262, 472 + width, 262 + height)).save(input_png)
        for depth, pixel_format in formats:
            output_png = root / f"output-{width}x{height}-t{tuple_index}-pf{depth}.png"
            run = subprocess.run(
                [str(WORKER), "render-png", str(AEX), str(input_png), str(output_png),
                 "--pixel-format", pixel_format, *parameters(tuple_index)],
                cwd=ROOT, capture_output=True, text=True,
            )
            if run.returncode:
                raise RuntimeError(run.stderr)
            observed = json.loads(run.stdout)
            key = (width, tuple_index, depth)
            expected_request = [[0, 0, width, height]]
            if (observed.get("render_error"), observed.get("render_mode"),
                observed.get("guards_intact"), observed.get("input_requests"),
                observed.get("output_request")) != (0, "smart-cpu", True, expected_request,
                                                     [0, 0, width, height]):
                raise RuntimeError(f"exported lifecycle drift {key}")
            got = observed["raw_pixel_sha256"]
            if got != EXPECTED_EXPORTED[key]:
                raise RuntimeError(f"exported raw drift {key}: {got}")
            old = historical[key]
            rows.append({
                "geometry": [width, height], "tuple_index": tuple_index, "depth": depth,
                "raw_bytes": observed["raw_pixel_bytes"], "exported_raw_sha256": got,
                "historical_mac_public_raw_sha256": old,
                "exported_matches_historical_mac_public": got == old,
                "promoted_on_mac_arches": [
                    arch for arch in PUBLIC_ARCHES if key in PROMOTED_BY_ARCH[arch]
                ], "render_mode": "smart-cpu",
                "guards_intact": True, "input_request": [0, 0, width, height],
                "output_request": [0, 0, width, height],
                "unsupported_suite_calls": observed.get("unsupported_suite_calls"),
            })
    if set(EXPECTED_EXPORTED) != {
        (width, tuple_index, depth)
        for width, _height, tuple_index in CONFIGS for depth in (8, 16, 32)
    }:
        raise RuntimeError("exported cell set drift")
    return rows


def load_feature():
    spec = importlib.util.spec_from_file_location("dblur_exported_public", FEATURE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compile_public(cpp: Path, executable: Path, arch: str) -> None:
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    command = [
        "clang++", "-std=c++17", "-arch", arch, "-O2", "-fno-fast-math",
        "-ffp-contract=off", "-isysroot", sdk, "-I", str(ROOT / "Headers"),
        "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
        "-I", str(ROOT / "Resources"), str(cpp), str(ROOT / "core/dblur_frontonly.cpp"),
        str(ROOT / "core/dblur_rotate.cpp"), str(ROOT / "core/dblur_rowdriver.cpp"),
        str(ROOT / "core/dblur_field.cpp"), "-framework", "Cocoa", "-o", str(executable),
    ]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(run.stderr)


def run_public(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    native_x86 = native_ucrt_x86_hashes()
    for arch in PUBLIC_ARCHES:
      for ordinal, (width, tuple_index, depth) in enumerate(sorted(PROMOTED_BY_ARCH[arch])):
        height = 18 if width == 32 else 36
        directory = root / f"public-{arch}-{ordinal}"
        directory.mkdir()
        feature = load_feature()
        feature.DUAL_W, feature.DUAL_H = width, height
        feature.DUAL_TUPLE = TUPLES[tuple_index]
        feature.build_probe(directory)
        cpp = directory / "olmdirectionalblur_mac_smartrender_adapter_probe.cpp"
        text = cpp.read_text()
        loop = "for(short d:{8,16,32})for(int kind=0;kind<2;++kind)"
        replacement = f"for(short d:{{{depth}}})for(int kind=0;kind<1;++kind)"
        if text.count(loop) != 1:
            raise RuntimeError("public loop marker drift")
        text = text.replace(loop, replacement, 1)
        state = "State st{&in,kind?&noise:nullptr,&out};"
        if text.count(state) != 1:
            raise RuntimeError("public state marker drift")
        text = text.replace(state, state + "const auto input_before=ib;const PF_EffectWorld input_header=in,output_header=out;", 1)
        assertion = "if(err||!pads||!st.preserve||st.pre!=2||st.layer!=2||st.out!=1||st.checkin_input!=1||st.checkin_noise!=(kind?1:0)||g_param_checkout!=21||g_param_checkin!=21)return 40+d+kind;"
        hardened = "if(err||ib!=input_before||std::memcmp(&in,&input_header,sizeof(in))||std::memcmp(&out,&output_header,sizeof(out))||!pads||!st.preserve||st.pre!=2||st.layer!=2||st.out!=1||st.checkin_input!=1||st.checkin_noise!=(kind?1:0)||g_param_checkout!=21||g_param_checkin!=21)return 40+d+kind;"
        if text.count(assertion) != 1:
            raise RuntimeError("public assertion marker drift")
        cpp.write_text(text.replace(assertion, hardened, 1))
        executable = directory / "public-selected"
        compile_public(cpp, executable, arch)
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"public {width}/t{tuple_index}/PF{depth}: {run.stdout} {run.stderr}")
        cases = json.loads(run.stdout)["cases"]
        if len(cases) != 1:
            raise RuntimeError("public case count")
        case = cases[0]
        raw = bytes.fromhex(case.pop("hex"))
        got = hashlib.sha256(raw).hexdigest()
        key = (width, tuple_index, depth)
        expected = native_x86.get(key, EXPECTED_EXPORTED[key]) if arch == "x86_64" else EXPECTED_EXPORTED[key]
        if got != expected:
            raise RuntimeError(f"public raw mismatch {arch} {key}: {got}")
        rows.append({
            "geometry": [width, height], "tuple_index": tuple_index, "depth": depth,
            "arch": arch,
            "raw_sha256": got, "oracle_raw_sha256": expected,
            "oracle": "native_windows_ucrt_injected_exported_smart" if arch == "x86_64" and key in native_x86
                      else "pinned_exported_smart",
            "raw_bytes": len(raw), "input_storage_unchanged": True,
            "input_output_headers_unchanged": True, "output_padding_unchanged": True,
            "callbacks": {"pre_checkout": 2, "pixel_checkout": 2, "output_checkout": 1,
                          "input_checkin": 1, "noise_checkin": 0,
                          "param_checkout": 21, "param_checkin": 21},
        })
    return rows


def identities() -> dict[str, str]:
    return {
        "worker_sha256": sha256(WORKER), "worker_identity_sha256": sha256(WORKER_IDENTITY),
        "worker_patch_sha256": sha256(PATCH), "aex_sha256": sha256(AEX),
        "source_png_sha256": sha256(SOURCE_PNG), "production_source_sha256": sha256(PRODUCTION),
        "feature_tool_sha256": sha256(FEATURE), "historical_public32_sha256": sha256(PUBLIC32),
        "historical_public64_sha256": sha256(PUBLIC64), "fail_closed_report_sha256": sha256(FAIL_CLOSED),
        "native_ucrt_remaining6_sha256": sha256(NATIVE_UCRT),
    }


def generate() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="dblur-exported-smart-nine.") as raw:
        root = Path(raw)
        exported = run_exported(root)
        public = run_public(root)
    return {
        "schema": "olmdirectionalblur.dual-side-exported-smart-closure/2",
        "status": "PASS_DUAL_SIDE_PUBLIC_ARM64_15_X86_64_15_NATIVE_UCRT_SIX",
        "identities": identities(), "tuples": [list(row) for row in TUPLES],
        "exported_aex_rows": exported, "exported_aex_rows_sha256": digest(exported),
        "mac_public_exact_rows": public, "mac_public_exact_rows_sha256": digest(public),
        "summary": {"exported_rows_observed": 15, "mac_public_rows_observed": 30,
                    "arm64_promoted_raw_exact": 15, "x86_64_promoted_raw_exact": 15,
                    "x86_64_native_ucrt_promoted": 6, "x86_64_remaining_fail_closed": 0},
        "scope": {"aex_exported_smart": True, "mac_public_effectmain": True,
                  "input_headers_padding_lifecycle_checked": True,
                  "mac_public_arches": ["arm64", "x86_64"],
                  "native_windows_ucrt_capture": True, "native_after_effects": False,
                  "arbitrary_source_tuple_geometry": False},
    }


def validate(report: dict[str, object], live: bool = True) -> bool:
    if set(report) != {"schema", "status", "identities", "tuples", "exported_aex_rows",
                      "exported_aex_rows_sha256", "mac_public_exact_rows",
                      "mac_public_exact_rows_sha256", "summary", "scope"}:
        return False
    if report["schema"] != "olmdirectionalblur.dual-side-exported-smart-closure/2" or report["status"] != "PASS_DUAL_SIDE_PUBLIC_ARM64_15_X86_64_15_NATIVE_UCRT_SIX":
        return False
    if report["identities"] != identities():
        return False
    exported = report["exported_aex_rows"]
    public = report["mac_public_exact_rows"]
    if not isinstance(exported, list) or len(exported) != 15 or digest(exported) != report["exported_aex_rows_sha256"]:
        return False
    if not isinstance(public, list) or len(public) != 30 or digest(public) != report["mac_public_exact_rows_sha256"]:
        return False
    if {(row["geometry"][0], row["tuple_index"], row["depth"])
        for row in exported} != PROMOTED_ARM64:
        return False
    for row in exported:
        key = (row["geometry"][0], row["tuple_index"], row["depth"])
        if row.get("promoted_on_mac_arches") != [
            arch for arch in PUBLIC_ARCHES if key in PROMOTED_BY_ARCH[arch]
        ]:
            return False
    if {(row["geometry"][0], row["tuple_index"], row["depth"], row["arch"]) for row in public} != {
        (*key, arch) for arch in PUBLIC_ARCHES for key in PROMOTED_BY_ARCH[arch]
    }:
        return False
    if any(row["raw_sha256"] != row["oracle_raw_sha256"] for row in public):
        return False
    if report["summary"] != {"exported_rows_observed": 15, "mac_public_rows_observed": 30,
                            "arm64_promoted_raw_exact": 15,
                            "x86_64_promoted_raw_exact": 15,
                            "x86_64_native_ucrt_promoted": 6,
                            "x86_64_remaining_fail_closed": 0}:
        return False
    return report["scope"] == {"aex_exported_smart": True, "mac_public_effectmain": True,
                               "input_headers_padding_lifecycle_checked": True,
                               "mac_public_arches": ["arm64", "x86_64"],
                               "native_windows_ucrt_capture": True, "native_after_effects": False,
                               "arbitrary_source_tuple_geometry": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    report = json.loads(REPORT.read_text()) if args.validate_only else generate()
    if args.write:
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        NOTE.write_text(
            "# OLMDirectionalBlur dual-side exported Smart closure\n\n"
            "The pinned Windows AEX exported Smart route was replayed for all 15 retained "
            "32x18/64x36 cells. All 15 are same-source raw-exact to the live arm64 Mac public "
            "EffectMain path (five each at PF8/PF16/PF32). For Rosetta x86_64, the prior nine "
            "remain exact to that exported owner. Native System32 UCRT expf/pow results injected "
            "into the exported owner prove that the former six rejected cells exactly equal the "
            "pre-existing x86_64 public arithmetic, so their production change is admission-only. "
            "The PF16 source uses the SDK "
            "0..32768 conversion, correcting the "
            "older hostless fixture's byte*128 transport. "
            "Input storage, world headers, padding and public callback lifecycle are preserved. "
            "The worker is AEXCompat/Unicorn with one separately bound finite `ceil` import; "
            "the six-cell math leaf is native Windows UCRT capture, but this is not native After Effects evidence.\n"
        )
    if not validate(report):
        raise SystemExit("FAIL_DUAL_SIDE_EXPORTED_SMART_CLOSURE")
    print(report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
