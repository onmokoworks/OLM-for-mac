#!/usr/bin/env python3
"""Actual-AEX vs production HSV/YUV parameter-family matrix."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
import probe_olmcolorkey_pf16_full_worker_20260805 as actual_probe  # noqa: E402
import test_olmcolorkey_mac_smartrender_adapter_20260717 as mac_adapter  # noqa: E402

WIDTH, HEIGHT, PADDING = 11, 7, 8
FORMATS = {"PF8": 4, "PF16": 8, "PF32": 16}
KEYS = ((0.80, 0.15, 0.10), (0.10, 0.75, 0.80))
COLORS = (
    (0.80, 0.15, 0.10), (0.76, 0.22, 0.09), (0.88, 0.09, 0.17),
    (0.10, 0.75, 0.80), (0.16, 0.69, 0.86), (0.04, 0.83, 0.70),
    (0.70, 0.24, 0.18), (0.58, 0.34, 0.14), (0.20, 0.62, 0.88),
    (0.30, 0.56, 0.72), (0.46, 0.42, 0.16), (0.26, 0.68, 0.54),
    (0.92, 0.28, 0.04), (0.04, 0.58, 0.92), (0.48, 0.18, 0.70),
)
CONFIGS = (
    {"name": "global_scalar_native", "per_color": 0, "per_component": 0, "force": 1},
    {"name": "global_component_16", "per_color": 0, "per_component": 1, "force": 2},
    {"name": "global_component_8", "per_color": 0, "per_component": 1, "force": 3},
    {"name": "perkey_scalar_native", "per_color": 1, "per_component": 0, "force": 1},
    {"name": "perkey_scalar_8", "per_color": 1, "per_component": 0, "force": 3},
    {"name": "perkey_component_16", "per_color": 1, "per_component": 1, "force": 2},
)
REPORT = ROOT / "refs/conformance/olmcolorkey_colorspace_2_5_matrix_actual_aex_20260810.json"
MD = REPORT.with_suffix(".md")

CURRENT_SPACE = 2
CURRENT_CONFIG = CONFIGS[0]
_original_parameter_record = actual_probe.parameter_record


def quantized(v: float) -> float | int:
    if actual_probe.PIXEL_FORMAT == "PF32":
        return v
    if actual_probe.PIXEL_FORMAT == "PF16":
        return max(0, min(32768, int(v * 32768.0)))
    return max(0, min(255, int(v * 255.0)))


def fixture(enabled_key: bool = False, key_shape: str = "single") -> tuple[bytes, int]:
    pixel_bytes = FORMATS[actual_probe.PIXEL_FORMAT]
    rowbytes = WIDTH * pixel_bytes + PADDING
    raw = bytearray([0xA5] * (rowbytes * HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            rgb = COLORS[(y * WIDTH + x) % len(COLORS)]
            values = (quantized(1.0), *(quantized(v) for v in rgb))
            struct.pack_into("<4f" if actual_probe.PIXEL_FORMAT == "PF32" else
                             "<4H" if actual_probe.PIXEL_FORMAT == "PF16" else "<4B",
                             raw, y * rowbytes + x * pixel_bytes, *values)
    return bytes(raw), rowbytes


def epsilon(depth: str, force: int) -> float:
    native = 0.5 / 255.0 if depth == "PF8" else 1.0 / 65536.0 if depth == "PF16" else 1.0e-6
    if force == 3:
        return 0.5 / 255.0
    if force == 2 and native < 1.0 / 65536.0:
        return 1.0 / 65536.0
    return native


def thresholds(config: dict[str, object]) -> tuple[float, tuple[float, float, float], tuple[float, float], tuple[tuple[float, float, float], ...]]:
    # Deliberately asymmetric values ensure Per Color and Per Component select
    # different record fields rather than coincidentally sharing one scalar.
    return (0.085, (0.055, 0.095, 0.125), (0.060, 0.115),
            ((0.045, 0.080, 0.120), (0.105, 0.055, 0.090)))


def parameter_record(enabled_key: bool = False, edge_blur: float = 0.0,
                     edge_blur_direction: int = 2, key_count: int = 1,
                     edge_blur_distance_type: int = 2) -> bytes:
    payload = bytearray(_original_parameter_record(True, 0.0, 2, 2, 2))
    cfg = CURRENT_CONFIG
    # Native packed order is Per Component then Per Color, unlike the UI and
    # production struct order.
    payload[0x34] = int(cfg["per_component"])
    payload[0x35] = int(cfg["per_color"])
    struct.pack_into("<i", payload, 0x30, CURRENT_SPACE)
    struct.pack_into("<i", payload, 0x3C, int(cfg["force"]))
    struct.pack_into("<f", payload, 0x54, epsilon(actual_probe.PIXEL_FORMAT, int(cfg["force"])))
    global_t, global_components, perkey_t, perkey_components = thresholds(cfg)
    struct.pack_into("<f", payload, 0x50, global_t)
    struct.pack_into("<3f", payload, 0x58, *global_components)
    for i, key in enumerate(KEYS):
        # The packed color is ARGB at +0x74+i*0x10; RGB begins at +0x78.
        struct.pack_into("<3f", payload, 0x78 + i * 0x10, *key)
        struct.pack_into("<f", payload, 0x394 + i * 4, perkey_t[i])
        struct.pack_into("<f", payload, 0x3F8 + i * 4, perkey_components[i][0])
        struct.pack_into("<f", payload, 0x45C + i * 4, perkey_components[i][1])
        struct.pack_into("<f", payload, 0x4C0 + i * 4, perkey_components[i][2])
    return bytes(payload)


CUSTOM_MAIN = r'''
int main(){g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;
constexpr int W=11,H=7,P=8;
const float colors[][3]={{.80f,.15f,.10f},{.76f,.22f,.09f},{.88f,.09f,.17f},{.10f,.75f,.80f},{.16f,.69f,.86f},{.04f,.83f,.70f},{.70f,.24f,.18f},{.58f,.34f,.14f},{.20f,.62f,.88f},{.30f,.56f,.72f},{.46f,.42f,.16f},{.26f,.68f,.54f},{.92f,.28f,.04f},{.04f,.58f,.92f},{.48f,.18f,.70f}};
struct Cfg{int pc,comp,force;};const Cfg cfgs[]={{0,0,1},{0,1,2},{0,1,3},{1,0,1},{1,0,3},{1,1,2}};
for(int space: {2,5})for(Cfg cfg:cfgs)for(int depth: {8,16,32}){
 int ps=depth==8?4:depth==16?8:16,rb=W*ps+P;std::vector<std::uint8_t>inb(rb*H,0xA5),outb(rb*H,0xCC);
 for(int y=0;y<H;y++)for(int x=0;x<W;x++){const float*r=colors[(y*W+x)%15];auto*q=inb.data()+y*rb+x*ps;
  if(depth==8){auto*v=reinterpret_cast<PF_Pixel8*>(q);*v={255,(A_u_char)(r[0]*255),(A_u_char)(r[1]*255),(A_u_char)(r[2]*255)};}
  else if(depth==16){auto*v=reinterpret_cast<PF_Pixel16*>(q);*v={32768,(A_u_short)(r[0]*32768),(A_u_short)(r[1]*32768),(A_u_short)(r[2]*32768)};}
  else{auto*v=reinterpret_cast<PF_PixelFloat*>(q);*v={1,r[0],r[1],r[2]};}}
 PF_EffectWorld in{inb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0},out{outb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0};
 OLMColorKeyInfo info{};info.number_of_colors=2;info.use_color[0]=info.use_color[1]=true;info.color_space=space;info.force_lower_precision=cfg.force;info.per_color=cfg.pc;info.per_component=cfg.comp;
 info.colors[0]={1,.80f,.15f,.10f};info.colors[1]={1,.10f,.75f,.80f};info.threshold=.085;info.threshold_r=.055;info.threshold_g=.095;info.threshold_b=.125;info.thresholds[0]=.060;info.thresholds[1]=.115;info.thresholds_r[0]=.045;info.thresholds_g[0]=.080;info.thresholds_b[0]=.120;info.thresholds_r[1]=.105;info.thresholds_g[1]=.055;info.thresholds_b[1]=.090;
 if(RenderWorld(&in,&out,info,(short)depth))return depth;std::fwrite(outb.data(),1,outb.size(),stdout);}
return 0;}
'''


def production() -> bytes:
    with tempfile.TemporaryDirectory(prefix="olmck_colorspace25_") as raw:
        directory = Path(raw); mac_adapter.compile_probe(directory)
        source = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
        source.write_text(source.read_text().replace("int main(){", "int legacy_main(){", 1) + CUSTOM_MAIN)
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
        executable = directory / "colorspace25"
        build = subprocess.run(["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk, "-I", str(directory), str(source), "-framework", "Cocoa", "-o", str(executable)], cwd=ROOT, capture_output=True, text=True)
        if build.returncode: raise RuntimeError(build.stderr)
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True)
        if run.returncode: raise RuntimeError(run.stderr.decode(errors="replace"))
        return run.stdout


def main() -> int:
    global CURRENT_SPACE, CURRENT_CONFIG
    actual_probe.WIDTH, actual_probe.HEIGHT = WIDTH, HEIGHT
    actual_probe.fixture, actual_probe.parameter_record = fixture, parameter_record
    actual = {}
    for space in (2, 5):
        for cfg in CONFIGS:
            CURRENT_SPACE, CURRENT_CONFIG = space, cfg
            for fmt in FORMATS:
                actual_probe.PIXEL_FORMAT = fmt
                actual[(space, cfg["name"], fmt)] = actual_probe.execute_case(actual_probe.AEX, True, 0.0, "single", 2, 2, 2)
    candidate=production();offset=0;rows=[];passed=True;space_alpha={2:set(),5:set()}
    for space in (2,5):
        for cfg in CONFIGS:
            for fmt,pb in FORMATS.items():
                rb=WIDTH*pb+PADDING;size=rb*HEIGHT;prod=candidate[offset:offset+size];offset+=size
                case=actual[(space,cfg["name"],fmt)];act=b"".join(bytes.fromhex(r)+b"\xCC"*PADDING for r in case["captures"]["output_active_rows_hex"])
                exact=act==prod;hits=case["execution"]["hits"];native=hits["smart_worker"]==1 and hits["parameter_materialize"]==1
                active=b"".join(bytes.fromhex(r) for r in case["captures"]["output_active_rows_hex"])
                alphas=tuple(active[y*WIDTH*pb+x*pb:y*WIDTH*pb+x*pb+(4 if fmt=="PF32" else 2 if fmt=="PF16" else 1)] for y in range(HEIGHT) for x in range(WIDTH))
                kept=sum(a != b"\0"*len(a) for a in alphas);space_alpha[space].add(hashlib.sha256(b"".join(alphas)).hexdigest())
                nontrivial=0<kept<WIDTH*HEIGHT;passed &= exact and native and nontrivial
                rows.append({"color_space":space,"config":cfg["name"],"per_color":cfg["per_color"],"per_component":cfg["per_component"],"force_lower_precision":cfg["force"],"pixel_format":fmt,"status":"exact" if exact else "mismatch","kept_pixels":kept,"bytes":size,"native_full_worker_path":native,"actual_worker_status":case["status"],"actual_sha256":hashlib.sha256(act).hexdigest(),"production_sha256":hashlib.sha256(prod).hexdigest()})
    distinct_spaces=space_alpha[2] != space_alpha[5];passed &= distinct_spaces and offset==len(candidate)
    report={"schema_version":1,"status":"exact" if passed else "mismatch","fixture":{"dimensions":[WIDTH,HEIGHT],"keys":[list(k) for k in KEYS],"palette_size":len(COLORS),"row_padding_bytes":PADDING,"edges":"off"},"matrix":{"color_spaces":[2,5],"configs":list(CONFIGS),"pixel_formats":list(FORMATS)},"actual_aex_sha256":actual_probe.AEX_SHA256,"spaces_observably_distinct":distinct_spaces,"comparison":"actual AEX full worker versus production RenderWorld; full typed ARGB active bytes and every padding byte","cases":rows,"claim_boundary":"Exact for the declared asymmetric 15-color/two-key fixture, HSV/YUV, the six declared Per Color/Per Component/Force Precision branches, and PF8/PF16/PF32; Edge Thin/Blur and Replace are off."}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    MD.write_text("# OLMColorKey HSV/YUV parameter matrix\n\n"+f"Status: **{report['status']}**\n\nThe asymmetric 15-color/two-key fixture makes HSV and YUV observably distinct and compares six threshold/precision branches at all three depths (36 cells). Edge Thin, Edge Blur, and Replace are disabled.\n\n"+f"Boundary: {report['claim_boundary']}\n")
    print(("PASS" if passed else "FAIL")+f"_OLMCOLORKEY_COLORSPACE_2_5_MATRIX_ACTUAL_AEX_20260810 cases={len(rows)} bytes={offset} distinct={distinct_spaces}")
    return 0 if passed else 3


if __name__ == "__main__": raise SystemExit(main())
