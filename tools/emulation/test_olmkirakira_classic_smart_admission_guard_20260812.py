#!/usr/bin/env python3
"""Verify Kira's bounded Classic admission and linked Smart closure."""
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
STRINGS = ROOT / "mac/OLMKiraKira/OLMKiraKira_Strings.cpp"
OUT = ROOT / "refs/conformance/olmkirakira_classic_smart_admission_guard_20260812.json"
DOC = OUT.with_suffix(".md")
SMART_REPORT = ROOT / "refs/conformance/olmkirakira_public_smart_bounded_closure_20260812.json"
MODE3_32X18_REPORT = ROOT / "refs/conformance/olmkirakira_mode3_32x18_public_closure_20260814.json"

EVIDENCE = {
    "olmkirakira_mode1_exported_effectmain_all_depths_20260812.json": "8464aa75ac75e71fd9151b881a858c650b7447ba2f56d3decf68d24d688c1122",
    "olmkirakira_mode1_rotation1_20260812.json": "0ec60ae12a79ed48518b652ca24d45fb4c92a8dea5e4f4cabc11bd9723dff4d8",
    "olmkirakira_mode2_ramp_merge2_exported_effectmain_all_depths_20260812.json": "7d73caa283d321ab1b08051543f3b472562868218ddca35142352b6a330f736a",
    "olmkirakira_mode2_ramp_merge2_rotation1_20260812.json": "3590cebcb7339285c898a3198a903b47fb0a94846f248a9ce190ee476e6d6d4c",
    "olmkirakira_mode2_rotation22_closure_20260812.json": "d88b3aa163330216fba22848abfdb1f25dbb562c8cf10d4284d9254c43cdd433",
    "olmkirakira_mode3_gaussian_length50_exported_effectmain_all_depths_20260812.json": "ec9f170e9472bfceda99af8e545dc90bd69a0a87811d37077e53003b4b54a08b",
    "olmkirakira_mode3_gaussian_length50_rotation1_20260812.json": "fae26f1a974f40ec1d49429acd70fed633b9863b5f97aeef6fe203755764fe9b",
    "olmkirakira_mode4_diagonal2_owner_angle_closure_20260812.json": "402ec3c99adf7cb5b951359bffc01361a449a7935197d2e84d4c2d440e9c7fad",
    "olmkirakira_mode4_highlight_gradient_closure_20260812.json": "f36249eac1e5d71454c75a2b4ba01b2697f4bc49cfddb343a0c2130035edde24",
    "olmkirakira_mode4_horizontal_solo_exported_effectmain_all_depths_20260812.json": "6433ae1745813107f765509464b157891beb55266944f63f24af1b2fcc072633",
    "olmkirakira_mode4_highlight_solo_exported_effectmain_all_depths_20260812.json": "455f89f1355e39ed751a7deb5f254e1d993adce11785a555c245ccb27032e702",
    "olmkirakira_mode4_multiray_exported_effectmain_all_depths_20260812.json": "fda9a9f42c59ca9992745e4d58e060bf4d8d4fd42908023aa4df726cba4a1f5c",
}

CPP = r'''
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <vector>
#include "__SOURCE__"
#include "__STRINGS__"

static PF_EffectWorld *g_input_world = nullptr;
static PF_EffectWorld *g_output_world = nullptr;
static PF_PixelFormat g_input_format = PF_PixelFormat_INVALID;
static PF_PixelFormat g_output_format = PF_PixelFormat_INVALID;
static PF_Err getfmt(const PF_EffectWorld *world, PF_PixelFormat *format) {
    if (!format) return PF_Err_BAD_CALLBACK_PARAM;
    if (world == g_input_world) *format = g_input_format;
    else if (world == g_output_world) *format = g_output_format;
    else return PF_Err_BAD_CALLBACK_PARAM;
    return PF_Err_NONE;
}
static PF_WorldSuite2 world_suite = {nullptr, nullptr, getfmt};
static SPErr acquire(const char *name, int32 version, const void **suite) {
    if (std::strcmp(name,kPFWorldSuite)==0 && version==kPFWorldSuiteVersion2) {
        *suite=&world_suite; return 0;
    }
    *suite=nullptr; return 1;
}
static SPErr release(const char*, int32) { return 0; }
static SPBasicSuite basic = {acquire, release};

static OLMKiraKiraInfo fixture() {
    OLMKiraKiraInfo i{};
    i.glow_rotation = 0.0; i.brightness_gain = 0.1; i.fade_out = 0.0;
    i.horizontal_length = 7; i.glow_opacity = 1.0; i.channel = 1;
    i.blur_mode = 1; i.merge_mode = 1; i.strength_multiplier = 1.0;
    i.source_opacity = 1.0;
    i.vertical_color = i.horizontal_color = i.diagonal_color =
        i.diagonal2_color = i.highlight_color = PF_PixelFloat{1,1,1,1};
    i.vertical_ramp = i.horizontal_ramp = i.diagonal_ramp =
        i.diagonal2_ramp = i.highlight_ramp = DefaultRampData();
    return i;
}
static bool admitted(const OLMKiraKiraInfo &i) { return IsClassicClosureTuple(i); }

template<class Pixel> static void set_pixel(Pixel&, int, int, int, int);
template<> void set_pixel(PF_Pixel8 &p,int r,int g,int b,int a) {
    p={(A_u_char)a,(A_u_char)r,(A_u_char)g,(A_u_char)b};
}
template<> void set_pixel(PF_Pixel16 &p,int r,int g,int b,int a) {
    p={(A_u_short)std::lround(a*32768.0/255.0),
       (A_u_short)std::lround(r*32768.0/255.0),
       (A_u_short)std::lround(g*32768.0/255.0),
       (A_u_short)std::lround(b*32768.0/255.0)};
}
template<> void set_pixel(PF_PixelFloat &p,int r,int g,int b,int a) {
    p={a/255.0f,r/255.0f,g/255.0f,b/255.0f};
}
template<class Pixel> static void mutate_pixel(Pixel &p) {
    p.alpha=p.alpha==0?1:0;
}
template<class Pixel> static void fill_source(std::vector<unsigned char> &bytes,
                                              int rowbytes,
                                              ClassicClosureSourceFamily family) {
    for (int y=0;y<3;y++) for (int x=0;x<5;x++) {
        const int i=y*5+x;
        const int r=family==ClassicClosureSource_AlphaGradient?0:i*15;
        const int g=family==ClassicClosureSource_AlphaGradient?0:i*11;
        const int b=family==ClassicClosureSource_AlphaGradient?0:i*7;
        const int a=family==ClassicClosureSource_AlphaGradient?i*15:64+i*11;
        set_pixel(*reinterpret_cast<Pixel*>(bytes.data()+y*rowbytes+x*sizeof(Pixel)),r,g,b,a);
    }
}

static int source_mutations = 0;
static int layout_mutations = 0;
template<class Pixel> static int test_depth(PF_PixelFormat format, short depth) {
    const int rowbytes=5*(int)sizeof(Pixel)+12;
    std::vector<unsigned char> input((size_t)rowbytes*3,0xA7), output(input.size(),0xD3);
    PF_EffectWorld iw{},ow{};
    iw.data=reinterpret_cast<PF_PixelPtr>(input.data());
    ow.data=reinterpret_cast<PF_PixelPtr>(output.data());
    iw.width=ow.width=5;iw.height=ow.height=3;
    iw.rowbytes=ow.rowbytes=rowbytes;
    g_input_world=&iw;g_output_world=&ow;g_input_format=g_output_format=format;
    PF_InData in{};in.pica_basicP=&basic;PF_OutData out{};PF_PixelFormat actual=PF_PixelFormat_INVALID;

    for (auto family : {ClassicClosureSource_SemiTransparentColor,
                        ClassicClosureSource_AlphaGradient}) {
        std::fill(input.begin(),input.end(),0xA7);fill_source<Pixel>(input,rowbytes,family);
        if (!ClassicClosureSourceMatches(&iw,format,family)) return 40+depth;
        if (ClassicClosureSourceMatches(&iw,format,
                family==ClassicClosureSource_AlphaGradient?
                ClassicClosureSource_SemiTransparentColor:ClassicClosureSource_AlphaGradient)) return 41+depth;
        ++source_mutations;
        for (int index : {0,7,14}) {
            Pixel *pixel=reinterpret_cast<Pixel*>(
                input.data()+(index/5)*rowbytes+(index%5)*sizeof(Pixel));
            const Pixel saved=*pixel;mutate_pixel(*pixel);
            if (ClassicClosureSourceMatches(&iw,format,family)) return 42+depth;
            *pixel=saved;++source_mutations;
        }
        if constexpr (sizeof(Pixel)==sizeof(PF_PixelFloat)) {
            if (family==ClassicClosureSource_AlphaGradient) {
                Pixel *first=reinterpret_cast<Pixel*>(input.data());
                const Pixel saved=*first;const uint32_t negative_zero=0x80000000u;
                std::memcpy(&first->red,&negative_zero,sizeof(negative_zero));
                if (ClassicClosureSourceMatches(&iw,format,family)) return 43+depth;
                *first=saved;++source_mutations;
            }
        }
    }

    if (!WorldLayoutIsSafe(&iw,sizeof(Pixel)) ||
        !IsClassicClosureLayout(&iw,&ow,format) ||
        ValidateWorldPair(&in,&out,&iw,&ow,depth,&actual)!=PF_Err_NONE || actual!=format) return 50+depth;

    const int good_rowbytes=iw.rowbytes;
    iw.rowbytes=5*(int)sizeof(Pixel)-1;
    if (WorldLayoutIsSafe(&iw,sizeof(Pixel))) return 51+depth;
    ++layout_mutations;iw.rowbytes=-good_rowbytes;
    if (WorldLayoutIsSafe(&iw,sizeof(Pixel))) return 52+depth;
    ++layout_mutations;iw.rowbytes=good_rowbytes;iw.origin_x=1;
    if (IsClassicClosureLayout(&iw,&ow,format)) return 53+depth;
    ++layout_mutations;iw.origin_x=0;ow.width=4;
    if (ValidateWorldPair(&in,&out,&iw,&ow,depth,&actual)!=PF_Err_BAD_CALLBACK_PARAM) return 54+depth;
    ++layout_mutations;ow.width=5;g_output_format=PF_PixelFormat_ARGB32==format?
        PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB32;
    if (ValidateWorldPair(&in,&out,&iw,&ow,depth,&actual)!=PF_Err_BAD_CALLBACK_PARAM) return 55+depth;
    ++layout_mutations;g_output_format=format;
    const short wrong_depth=depth==8?16:8;
    if (ValidateWorldPair(&in,&out,&iw,&ow,wrong_depth,&actual)!=PF_Err_BAD_CALLBACK_PARAM) return 56+depth;
    ++layout_mutations;
    if constexpr (alignof(Pixel)>1) {
        iw.data=reinterpret_cast<PF_PixelPtr>(input.data()+1);
        if (WorldLayoutIsSafe(&iw,sizeof(Pixel))) return 57+depth;
        ++layout_mutations;iw.data=reinterpret_cast<PF_PixelPtr>(input.data());
        iw.rowbytes=good_rowbytes+1;
        if (WorldLayoutIsSafe(&iw,sizeof(Pixel))) return 58+depth;
        ++layout_mutations;iw.rowbytes=good_rowbytes;
    }
    return 0;
}

int main() {
    int admitted_count = 0;
    int rejected_count = 0;
    auto yes = [&](OLMKiraKiraInfo i) { if (!admitted(i)) std::exit(10); ++admitted_count; };
    auto no = [&](OLMKiraKiraInfo i) { if (admitted(i)) std::exit(20); ++rejected_count; };

    auto i = fixture(); yes(i); i.glow_rotation=1; yes(i);
    i=fixture(); i.horizontal_length=0; i.highlight_radius=3;
    i.brightness_gain=1; yes(i);
    i=fixture(); i.blur_mode=2; i.merge_mode=2; i.horizontal_use_ramp=1; yes(i);
    i.glow_rotation=1; yes(i); i.glow_rotation=22; i.brightness_gain=.73; yes(i);
    i=fixture(); i.blur_mode=2; i.horizontal_length=0; i.highlight_radius=3;
    i.brightness_gain=1; yes(i);
    i=fixture(); i.blur_mode=3; i.horizontal_length=50; yes(i); i.glow_rotation=1; yes(i);
    i=fixture(); i.blur_mode=4; i.horizontal_length=0; i.highlight_radius=3;
    i.brightness_gain=1; yes(i);
    i=fixture(); i.blur_mode=4; i.merge_mode=2; i.brightness_gain=.73; i.glow_rotation=1;
    i.horizontal_length=5; i.horizontal_use_ramp=1; yes(i);
    i.horizontal_length=0; i.horizontal_use_ramp=0; i.diagonal2_length=7; yes(i);
    i.diagonal2_length=0; i.highlight_radius=3; i.highlight_use_ramp=1; yes(i);
    i.horizontal_length=5; i.horizontal_use_ramp=1; i.diagonal2_length=7; yes(i);

    i=fixture(); i.horizontal_length=8; no(i);
    i=fixture(); i.channel=2; no(i);
    i=fixture(); i.approximated_input=1; no(i);
    i=fixture(); i.vertical_length=1; no(i);
    i=fixture(); i.horizontal_color.red=.5f; no(i);
    i=fixture(); i.horizontal_ramp.stops[1].red=.5f; no(i);
    i=fixture(); i.blur_mode=4; i.merge_mode=2; i.brightness_gain=.73;
    i.glow_rotation=1; i.horizontal_length=5; i.horizontal_use_ramp=1;
    i.diagonal2_length=7; no(i);

    if (int e=test_depth<PF_Pixel8>(PF_PixelFormat_ARGB32,8)) { std::cerr<<"pf8 "<<e<<"\n";return e; }
    if (int e=test_depth<PF_Pixel16>(PF_PixelFormat_ARGB64,16)) { std::cerr<<"pf16 "<<e<<"\n";return e; }
    if (int e=test_depth<PF_PixelFloat>(PF_PixelFormat_ARGB128,32)) { std::cerr<<"pf32 "<<e<<"\n";return e; }
    std::cout << admitted_count << " " << rejected_count << " "
              << source_mutations << " " << layout_mutations << "\n";
}
'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_smart_cells(cells: list[dict]) -> str:
    # Bind lifecycle and immutability fields as well as numerical hashes. The
    # authoritative Smart closure deliberately canonicalizes each complete row.
    encoded = json.dumps(cells, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def canonical_smart_negatives(rows: list[dict]) -> str:
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate_saved_report() -> None:
    """Read-only validation used by dependency runners and handoff checks."""
    report = json.loads(OUT.read_text(encoding="utf-8"))
    smart = json.loads(SMART_REPORT.read_text(encoding="utf-8"))
    mode3_32x18 = json.loads(MODE3_32X18_REPORT.read_text(encoding="utf-8"))
    source = SOURCE.read_text(encoding="utf-8")
    smart_start = source.index("static PF_Err SmartRender(")
    smart_end = source.index("\n}\n\n}  // namespace", smart_start)
    smart_body = source[smart_start:smart_end]
    assert report["kind"] == "olmkirakira_classic_smart_admission_guard"
    assert report["status"] == "exact_bounded_admission"
    assert report["source_sha256"] == sha(SOURCE)
    assert report["classic"]["admitted_declared_tuples"] == 14
    assert report["classic"]["rejected_mutations"] == 7
    assert report["classic"]["source_content_mutations_rejected"] == 25
    assert report["classic"]["layout_format_depth_mutations_rejected"] == 22
    assert smart["status"] == "raw_exact_bounded_public_smart"
    assert smart["identities"]["production_source_sha256"] == sha(SOURCE)
    assert report["smart"]["evidence_sha256"] == sha(SMART_REPORT)
    assert report["smart"]["positive_cell_count"] == len(smart["positive_cells"]) == 42
    assert report["smart"]["canonical_cells_sha256"] == canonical_smart_cells(
        smart["positive_cells"]
    ) == smart["canonical_cells_sha256"]
    assert report["smart"]["canonical_negative_rows_sha256"] == canonical_smart_negatives(
        smart["negative_rows"]
    ) == smart["canonical_negative_rows_sha256"]
    assert report["smart"]["optional_pixel_checkin"] is True
    assert report["smart"]["all_negative_outputs_untouched"] is True
    assert report["mode3_32x18"]["evidence_sha256"] == sha(MODE3_32X18_REPORT)
    assert report["mode3_32x18"]["positive_cell_count"] == 3
    assert mode3_32x18["status"] == "raw_exact_bounded_public_classic_and_smart"
    assert mode3_32x18["identities"]["production_source_sha256"] == sha(SOURCE)
    assert all(c["oracle_sha256"] == c["mac_smart_sha256"] == c["mac_classic_sha256"]
               for c in mode3_32x18["positive_cells"])
    expected_evidence = {f"refs/conformance/{name}": digest for name, digest in EVIDENCE.items()}
    saved_evidence = {row["path"]: row["sha256"] for row in report["evidence"]}
    assert saved_evidence == expected_evidence
    for relative, digest in expected_evidence.items():
        assert sha(ROOT / relative) == digest
    checks = report["static_checks"]
    assert checks["smart_calls_checked_parameter_decoder"]
    assert checks["smart_calls_numeric_owner"]
    assert checks["smart_has_no_unconditional_bad_callback"]
    assert checks["smart_format_matches_declared_depth"]
    assert checks["smart_pixel_checkin_is_optional"]
    assert "CheckoutSmartInfo(in_data, &info)" in smart_body
    assert "RenderWorld(" in smart_body
    assert "if (!err) err = PF_Err_BAD_CALLBACK_PARAM;" not in smart_body
    assert "extra->cb->checkin_layer_pixels(" not in smart_body
    build = report["universal_isolated_build"]
    assert set(build["architectures"]) == {"arm64", "x86_64"}
    assert build["codesign_verify_strict"] is True
    assert build["installed"] is False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--validate-only", action="store_true",
        help="validate the saved report and live dependencies without writing or building",
    )
    args = parser.parse_args()
    if args.validate_only:
        validate_saved_report()
        print(json.dumps({"status": "validated", "report_sha256": sha(OUT)}))
        return 0
    source = SOURCE.read_text(encoding="utf-8")
    smart_start = source.index("static PF_Err SmartRender(")
    smart_end = source.index("\n}\n\n}  // namespace", smart_start)
    smart_body = source[smart_start:smart_end]
    static_checks = {
        "world_pair_validates_both_formats":
            "if (input_format != output_format) return PF_Err_BAD_CALLBACK_PARAM;" in source,
        "layout_checks_active_rowbytes":
            "active_rowbytes > static_cast<int64_t>(world->rowbytes)" in source,
        "classic_fixed_layout": "IsClassicClosureLayout(input, output, format)" in source,
        "classic_tuple_map": "ClassicClosureSourceFamilyForTuple(info)" in source,
        "classic_source_content_gate":
            "ClassicClosureSourceMatches(input, format, source_family)" in source,
        "smart_calls_checked_parameter_decoder": "CheckoutSmartInfo(in_data, &info)" in smart_body,
        "smart_calls_numeric_owner": "RenderWorld(" in smart_body,
        "smart_has_no_unconditional_bad_callback":
            "if (!err) err = PF_Err_BAD_CALLBACK_PARAM;" not in smart_body,
        "smart_format_matches_declared_depth":
            "extra->input->bitdepth, &format" in smart_body,
        "smart_pixel_checkin_is_optional":
            "!extra->cb->checkin_layer_pixels" not in smart_body and
            "extra->cb->checkin_layer_pixels(" not in smart_body,
    }
    if not all(static_checks.values()):
        raise AssertionError(static_checks)

    reports = []
    for name, expected_sha in EVIDENCE.items():
        path = ROOT / "refs/conformance" / name
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("status") not in {"exact", "raw_exact"}:
            raise AssertionError(f"non-exact admission evidence: {name}")
        actual_sha = sha(path)
        if actual_sha != expected_sha:
            raise AssertionError(f"changed admission evidence: {name} {actual_sha}")
        reports.append({"path": f"refs/conformance/{name}", "sha256": actual_sha,
                        "status": data["status"]})

    with tempfile.TemporaryDirectory(prefix="kira_admission_guard_") as raw:
        directory = Path(raw)
        cpp = directory / "admission.cpp"
        cpp.write_text(CPP.replace("__SOURCE__", str(SOURCE)).replace(
            "__STRINGS__", str(STRINGS)), encoding="utf-8")
        executable = directory / "admission"
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        command = [_UCRT_CXX, "-std=c++20", "-O2", "-fno-fast-math",
                   "-ffp-contract=off", "-isysroot", sdk,
                   "-I", str(resolve_asset(ROOT / "Headers")), "-I", str(resolve_asset(ROOT / "Headers/SP")),
                   "-I", str(resolve_asset(ROOT / "Util")), "-I", str(resolve_asset(ROOT / "Resources")),
                   str(cpp), str(resolve_asset(ROOT / str(resolve_asset("Util/AEGP_SuiteHandler.cpp")))),
                   str(resolve_asset(ROOT / str(resolve_asset("Util/MissingSuiteError.cpp")))),
                   "-framework", "Cocoa", "-o", str(executable)]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True,
                             text=True)
        if run.returncode:
            raise RuntimeError(f"admission harness exit {run.returncode}: {run.stderr}")
        (admitted_count, rejected_count, source_mutations,
         layout_mutations) = map(int, run.stdout.split())

    smart_report = json.loads(SMART_REPORT.read_text(encoding="utf-8"))
    if smart_report.get("kind") != "olmkirakira_public_smart_bounded_closure":
        raise AssertionError("unexpected Smart closure kind")
    if smart_report.get("status") != "raw_exact_bounded_public_smart":
        raise AssertionError("Smart closure is not exact")
    identities = smart_report["identities"]
    if identities["production_source_sha256"] != sha(SOURCE):
        raise AssertionError("Smart closure production identity is stale")
    if identities["aex_sha256"] != "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7":
        raise AssertionError("Smart closure Windows AEX identity changed")
    if identities["aexcompat_worker_sha256"] != "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61":
        raise AssertionError("Smart closure AEXCompat worker identity changed")
    if identities["aexcompat_commit"] != "28d535469f84f67236ef3425afe4291ea2fb0991":
        raise AssertionError("Smart closure AEXCompat commit changed")
    smart_cells = smart_report["positive_cells"]
    smart_negatives = smart_report["negative_rows"]
    if len(smart_cells) != 42 or smart_report["contract"]["admitted_tuple_count"] != 14:
        raise AssertionError("Smart closure positive matrix changed")
    if not all(cell["smart_sha256"] == cell["classic_sha256"] == cell["oracle_sha256"]
               for cell in smart_cells):
        raise AssertionError("Smart/Classic/oracle cell mismatch")
    if smart_report["canonical_cells_sha256"] != canonical_smart_cells(smart_cells):
        raise AssertionError("Smart closure canonical cell digest mismatch")
    if smart_report["canonical_negative_rows_sha256"] != canonical_smart_negatives(smart_negatives):
        raise AssertionError("Smart closure canonical negative digest mismatch")
    if not smart_report["negative_matrix"]["all_output_untouched"]:
        raise AssertionError("Smart closure negatives did not preserve output")

    mode3_32x18_report = json.loads(MODE3_32X18_REPORT.read_text(encoding="utf-8"))
    if mode3_32x18_report.get("status") != "raw_exact_bounded_public_classic_and_smart":
        raise AssertionError("Mode3 32x18 closure is not exact")
    if mode3_32x18_report["identities"]["production_source_sha256"] != sha(SOURCE):
        raise AssertionError("Mode3 32x18 closure production identity is stale")
    mode3_cells = mode3_32x18_report["positive_cells"]
    if len(mode3_cells) != 3 or not all(
        cell["oracle_sha256"] == cell["mac_smart_sha256"] == cell["mac_classic_sha256"]
        for cell in mode3_cells
    ):
        raise AssertionError("Mode3 32x18 public cells changed")

    with tempfile.TemporaryDirectory(prefix="kira_universal_isolated_") as raw:
        build_dir = Path(raw) / "Product"
        build_command = [
            "xcodebuild", "-project", str(ROOT / "mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj"),
            "-scheme", "OLMKiraKira", "-configuration", "Debug",
            f"CONFIGURATION_BUILD_DIR={build_dir}", "ARCHS=arm64 x86_64",
            "ONLY_ACTIVE_ARCH=NO", "CODE_SIGNING_ALLOWED=NO", "build",
        ]
        built = subprocess.run(build_command, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise RuntimeError(built.stdout[-4000:] + built.stderr[-4000:])
        bundle = build_dir / "OLMKiraKira.plugin"
        binary = bundle / "Contents/MacOS/OLMKiraKira"
        subprocess.run(["codesign", "--force", "--sign", "-", str(bundle)],
                       check=True, capture_output=True, text=True)
        subprocess.run(["codesign", "--verify", "--strict", "--verbose=2", str(bundle)],
                       check=True, capture_output=True, text=True)
        architectures = subprocess.check_output(["lipo", "-archs", str(binary)],
                                                text=True).split()
        if set(architectures) != {"arm64", "x86_64"}:
            raise AssertionError(architectures)
        universal_build = {
            "configuration": "Debug",
            "architectures": architectures,
            "codesign_verify_strict": True,
            "binary_sha256": sha(binary),
            "isolated_temp_product": True,
            "installed": False,
        }

    valid = (admitted_count == 14 and rejected_count == 7 and
             source_mutations == 25 and layout_mutations == 22)
    report = {
        "kind": "olmkirakira_classic_smart_admission_guard",
        "date": "2026-08-12",
        "status": "exact_bounded_admission" if valid else "unexpected",
        "classic": {
            "dimensions": [5, 3],
            "row_padding_bytes": 12,
            "pixel_formats": ["PF8/ARGB32", "PF16/ARGB64", "PF32/ARGB128"],
            "admitted_declared_tuples": admitted_count,
            "rejected_mutations": rejected_count,
            "source_content_mutations_rejected": source_mutations,
            "layout_format_depth_mutations_rejected": layout_mutations,
            "source_function": "ClassicClosureSourceFamilyForTuple + ClassicClosureSourceMatches",
            "source_families": {
                "semi_transparent_color": "RGBA=(15*i,11*i,7*i,64+11*i)",
                "alpha_gradient": "RGBA=(0,0,0,15*i)",
            },
        },
        "smart": {
            "status": "linked_raw_exact_bounded_public_smart",
            "evidence_path": "refs/conformance/olmkirakira_public_smart_bounded_closure_20260812.json",
            "evidence_sha256": sha(SMART_REPORT),
            "positive_cell_count": len(smart_cells),
            "canonical_cells_sha256": smart_report["canonical_cells_sha256"],
            "canonical_negative_rows_sha256": smart_report["canonical_negative_rows_sha256"],
            "optional_pixel_checkin": True,
            "all_negative_outputs_untouched": True,
        },
        "mode3_32x18": {
            "status": "linked_raw_exact_bounded_public_classic_and_smart",
            "evidence_path": "refs/conformance/olmkirakira_mode3_32x18_public_closure_20260814.json",
            "evidence_sha256": sha(MODE3_32X18_REPORT),
            "positive_cell_count": len(mode3_cells),
            "tuple": "Mode3/Merge1/Horizontal50/Rotation0/Gain0.1",
            "source": "wrapped-linear RGBA fixture",
            "dimensions": [32, 18],
            "row_padding_bytes": 12,
        },
        "static_checks": static_checks,
        "universal_isolated_build": universal_build,
        "evidence": reports,
        "source_sha256": sha(SOURCE),
        "claim_boundary": "The named 5x3 closures remain unchanged. One additional Mode3/Merge1/Horizontal50/Rotation0/Gain0.1 wrapped-linear source at exactly 32x18 and row padding 12 is admitted by Classic and full-request Smart at PF8/PF16/PF32. Other tuple/source/layout/request combinations remain fail-closed; no install or AE-host numerical claim is made.",
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    DOC.write_text(
        "# OLMKiraKira Classic/Smart admission guard（2026-08-12）\n\n"
        f"Status: **{report['status']}**\n\n"
        "Classicは宣言済み5×3・row padding 12の14 tupleと対応する2種のsource fixtureだけを"
        "PF8/PF16/PF32でadmitする。format/depth不一致、短い・負の・unaligned rowbytes、"
        "geometry/origin差分、tuple変異、sourceの先頭・中央・末尾pixel変異は"
        "BAD_CALLBACK_PARAMでfail-closeする。\n\n"
        "Smartは別証跡 `olmkirakira_public_smart_bounded_closure_20260812.json` に接続済みで、"
        "同じ14 tuple×PF8/PF16/PF32の42セルがClassicおよび固定Windows oracle hashとraw exactである。"
        "canonical positive/negative digestとproduction/AEX/AEXCompat identityを本guardから再検証する。"
        "pixel checkin callbackはWindows ownerと同じく任意で、要求も呼出しもしない。\n\n"
        "追加でMode3 / Merge1 / Horizontal 50 / Rotation 0 / Gain 0.1のwrapped-linear sourceを"
        "32×18・padding 12・full Smart requestに限って3深度でadmitする。Windows exported Smart、"
        "Mac Classic、Mac Smartのactive bytesは3/3 raw exactで、1条件違いはfail-closeする。\n\n"
        "Universal isolated Debug buildはarm64/x86_64とstrict codesign verifyを確認した。"
        "installとAE host実行は実施していない。未列挙tuple/source/layoutは引き続きfail-closeする。\n\n"
        "Verification: `python3 tools/emulation/test_olmkirakira_classic_smart_admission_guard_20260812.py`\n",
        encoding="utf-8")
    print(json.dumps({"status": report["status"], "classic": report["classic"],
                      "smart": report["smart"]}))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
