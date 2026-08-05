#!/usr/bin/env python3
"""Capture a complete bounded actual-AEX PF8 frame and compare the Mac seam."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
PRODUCTION = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
WIDTH = HEIGHT = 16
ROWBYTES = 76
EXPECTED_AEX_SHA256 = "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e"
EXPECTED_SOURCE_SHA256 = "cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4"
EXPECTED_CROP_ARGB_SHA256 = "ad840bf75281333fc389ba7083074e10ff82e7538583242e7a91880e6bbe1b83"
EXPECTED_ACTUAL_PF8_SHA256 = "8b8a28887908f089024bc38f69221148b612adfdcf44afc63d282216a0d7d3ae"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require_sha256(path: Path, expected: str, label: str) -> None:
    actual = sha256_bytes(path.read_bytes())
    if actual != expected:
        raise RuntimeError(
            f"BLOCKED_FAIL_CLOSED: {label} identity mismatch: {actual} != {expected}"
        )


def load_fixture():
    sys.path.insert(0, str(FIXTURE_PATH.parent))
    import dblur_fullrender_host_fixture_20260711 as fixture  # noqa: E402
    return fixture


def capture_actual(
    angle_degrees: float = 0.0,
    input_argb: bytes | None = None,
    front_strength: int = 8,
    back_strength: int = 0,
    front_alpha_fade: int = 0,
    front_sharp_tail: float = 0.0,
    size_variation: float = 0.0,
    noise_variation: float = 0.0,
    noise_type: int = 1,
    seed: int = 1,
    noise_offset: int = 0,
    thickness: float = 10.0,
    noise_layer_row_padding: int | None = None,
    noise_layer_origin: tuple[int, int] | None = None,
    noise_layer_dimensions: tuple[int, int] | None = None,
    require_complete: bool = True,
    brightness_gain: float = 1.0,
) -> tuple[bytes, dict]:
    fixture = load_fixture()
    captured = bytearray(WIDTH * HEIGHT * 4)
    original = fixture.model_output
    writer = 0x180006B30

    def natural_writer(ld, params, y, x, out, out_ptr, width):
        del out, width
        ld.call_function(writer, int_args=[params, x, y, 0, out_ptr], max_instructions=1000)
        pixel = ld.read_bytes(out_ptr, 4)
        offset = (y * WIDTH + x) * 4
        captured[offset:offset + 4] = pixel

    fixture.model_output = natural_writer
    try:
        with tempfile.TemporaryDirectory(prefix="olm_dblur_complete_pf8_") as name:
            temp = Path(name)
            source = temp / "source_16x16.png"
            if input_argb is None:
                Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278)).save(source)
            else:
                if len(input_argb) != WIDTH * HEIGHT * 4:
                    raise RuntimeError("BLOCKED_FAIL_CLOSED: custom PF8 input is not 16x16 ARGB")
                rgba = bytes(
                    value
                    for pixel in (input_argb[index:index + 4] for index in range(0, len(input_argb), 4))
                    for value in (pixel[1], pixel[2], pixel[3], pixel[0])
                )
                Image.frombytes("RGBA", (WIDTH, HEIGHT), rgba).save(source)
            output = temp / "fixture.json"
            sys.argv = [str(FIXTURE_PATH), "--source", str(source), "--output", str(output),
                        "--angle", str(angle_degrees), "--brightness-gain", str(brightness_gain),
                        "--downsample-num", "1", "--downsample-den", "1",
                        "--front-strength", str(front_strength), "--size-variation", str(int(size_variation)),
                        "--front-alpha-fade", str(front_alpha_fade),
                        "--front-sharp-tail", str(int(front_sharp_tail)), "--back-strength", str(back_strength),
                        "--back-alpha-fade", "0", "--noise-variation", str(int(noise_variation)),
                        "--noise-type", str(noise_type), "--seed", str(seed),
                        "--noise-offset", str(noise_offset), "--thickness", str(int(thickness)),
                        "--world-area", "0", "0", "16", "16", "--row-padding", "12",
                        "--no-detour-rotate", "--max-instructions", "20000000"]
            if noise_layer_row_padding is not None:
                sys.argv.extend(["--noise-layer-row-padding", str(noise_layer_row_padding)])
            if noise_layer_origin is not None:
                sys.argv.extend(["--noise-layer-origin", str(noise_layer_origin[0]), str(noise_layer_origin[1])])
            if noise_layer_dimensions is not None:
                sys.argv.extend(["--noise-layer-size", str(noise_layer_dimensions[0]), str(noise_layer_dimensions[1])])
            status = fixture.main()
            report = json.loads(output.read_text(encoding="utf-8"))
    finally:
        fixture.model_output = original
    calls = report["execution"]["iterate_calls"]
    complete = (report["output"].get("complete") is True
                and [c["callback"] for c in calls] == ["0x180006980", "0x180006b30"]
                and len(captured) == WIDTH * HEIGHT * 4)
    if not complete and require_complete:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: natural actual-AEX frame incomplete")
    return bytes(captured), {
        "fixture_status": report["status"],
        "iterate_calls": calls,
        "output_complete": report["output"].get("complete"),
        "natural_complete": complete,
        "rotate_call_count": len(report["execution"].get("rotate_entry", [])),
        "writer": hex(writer),
        "angle_degrees": angle_degrees,
        "brightness_gain": brightness_gain,
        "front_strength": front_strength,
        "back_strength": back_strength,
        "front_alpha_fade": front_alpha_fade,
        "front_sharp_tail": front_sharp_tail,
        "size_variation": size_variation,
        "noise_variation": noise_variation,
        "noise_type": noise_type,
        "seed": seed,
        "noise_offset": noise_offset,
        "thickness": thickness,
        "input_rowbytes": report["world_layout"]["input_rowbytes"],
        "noise_layer_rowbytes": report["world_layout"]["noise_layer_rowbytes"],
        "input_extent_hint": report["world_layout"]["input_extent_hint"],
        "noise_layer_extent_hint": report["world_layout"]["noise_layer_extent_hint"],
        "input_dimensions": report["world_layout"]["input_dimensions"],
        "noise_layer_dimensions": report["world_layout"]["noise_layer_dimensions"],
    }


def capture_mac(
    argb: bytes,
    temp: Path,
    angle_degrees: float = 0.0,
    front_strength: int = 8,
    back_strength: int = 0,
    front_alpha_fade: int = 0,
    front_sharp_tail: float = 0.0,
    size_variation: float = 0.0,
    noise_variation: float = 0.0,
    noise_type: int = 1,
    seed: int = 1,
    noise_offset: int = 0,
    thickness: float = 10.0,
    noise_layer_argb: bytes | None = None,
    noise_layer_row_padding: int = 12,
    noise_layer_origin: tuple[int, int] = (0, 0),
    noise_layer_dimensions: tuple[int, int] = (16, 16),
    brightness_gain: float = 1.0,
) -> tuple[bytes, dict]:
    compiler = os.environ.get("CXX", "clang++")
    source_array = ",".join(str(value) for value in argb)
    noise_width, noise_height = noise_layer_dimensions
    if noise_width <= 0 or noise_height <= 0:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: invalid noise Layer dimensions")
    if noise_layer_argb is not None and len(noise_layer_argb) != noise_width * noise_height * 4:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: custom noise Layer byte count does not match dimensions")
    if noise_layer_row_padding < 0:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: negative noise Layer row padding")
    noise_array = ",".join(str(value) for value in (noise_layer_argb or argb))
    render_call = (
        "OLMDirectionalBlurTestRenderWorldWithNoise(&in,&out,&noise,&info,8,&exact)"
        if noise_layer_argb is not None
        else "OLMDirectionalBlurTestRenderWorld(&in,&out,&info,8,&exact)"
    )
    production = str(PRODUCTION).replace("\\", "\\\\").replace('"', '\\"')
    probe = temp / "complete_pf8_mac_probe.cpp"
    executable = temp / "complete_pf8_mac_probe"
    probe.write_text(f'''#define OLM_DBLUR_TEST_SEAM 1
#include "{production}"
#include <array>
#include <cstdio>
#include <cstdint>
int main() {{
  constexpr int W=16, H=16, NW={noise_width}, NH={noise_height}, RB=76, NRB=NW*4+{noise_layer_row_padding};
  const std::uint8_t input_bytes[] = {{{source_array}}};
  const std::uint8_t noise_bytes_packed[] = {{{noise_array}}};
  std::array<std::uint8_t, RB*H> in_bytes{{}}, out_bytes{{}};
  std::array<std::uint8_t, NRB*NH> noise_bytes{{}};
  for (int y=0; y<H; ++y) for (int x=0; x<W*4; ++x) in_bytes[y*RB+x]=input_bytes[y*W*4+x];
  for (int y=0; y<NH; ++y) for (int x=0; x<NW*4; ++x) noise_bytes[y*NRB+x]=noise_bytes_packed[y*NW*4+x];
  PF_EffectWorld in{{}}, noise{{}}, out{{}};
  in.data=(PF_PixelPtr)in_bytes.data(); in.rowbytes=RB; in.width=W; in.height=H;
  in.extent_hint={{0,0,W,H}}; noise.data=(PF_PixelPtr)noise_bytes.data(); noise.rowbytes=NRB;
  noise.width=NW; noise.height=NH; noise.extent_hint={{{noise_layer_origin[0]},{noise_layer_origin[1]},{noise_layer_origin[0]}+NW,{noise_layer_origin[1]}+NH}}; out.data=(PF_PixelPtr)out_bytes.data(); out.rowbytes=RB;
  out.width=W; out.height=H; out.extent_hint={{0,0,W,H}};
  OLMDirectionalBlurInfo info{{}}; info.angle_deg={angle_degrees!r}; info.brightness_gain={brightness_gain!r};
  info.front_strength={front_strength}; info.front_alpha_fade={front_alpha_fade}; info.front_sharp_tail={front_sharp_tail!r}; info.back_strength={back_strength}; info.size_variation={size_variation!r}; info.noise_variation={noise_variation!r}; info.noise_type={noise_type}; info.seed={seed}; info.noise_offset={noise_offset}; info.thickness={thickness!r}; info.render_scale_x=1; info.render_scale_y=1;
  int exact=0; if ({render_call}!=PF_Err_NONE || !exact) return 2;
  std::printf("HEX="); for (int y=0; y<H; ++y) for (int x=0; x<W*4; ++x) std::printf("%02x", out_bytes[y*RB+x]);
  std::printf("\\nEXACT=%d\\n", exact); return 0;
}}
''', encoding="utf-8")
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
    command = [compiler, "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off",
               "-Wno-unused-function", "-Wno-unused-parameter", "-isysroot", sdk,
               "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
               "-I", str(ROOT / "Resources"), "-ffunction-sections", "-fdata-sections",
               str(probe), str(ROOT / "core/dblur_frontonly.cpp"),
               str(ROOT / "core/dblur_rotate.cpp"), str(ROOT / "core/dblur_rowdriver.cpp"),
               str(ROOT / "core/dblur_field.cpp"),
               "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(executable)]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if build.returncode:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: Mac adapter probe did not compile\n" + build.stderr)
    run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: Mac adapter probe failed\n" + run.stderr)
    lines = dict(line.split("=", 1) for line in run.stdout.splitlines() if "=" in line)
    raw = bytes.fromhex(lines.get("HEX", ""))
    if len(raw) != WIDTH * HEIGHT * 4:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: Mac adapter frame length is not complete 16x16")
    return raw, {"exact": int(lines.get("EXACT", "0")), "rowbytes": ROWBYTES,
                    "noise_layer_rowbytes": noise_width * 4 + noise_layer_row_padding,
                    "input_extent_hint": [0, 0, WIDTH, HEIGHT],
                    "noise_layer_extent_hint": [noise_layer_origin[0], noise_layer_origin[1],
                                                noise_layer_origin[0] + noise_width, noise_layer_origin[1] + noise_height],
                    "input_dimensions": [WIDTH, HEIGHT],
                    "noise_layer_dimensions": [noise_width, noise_height],
                    "production_source": str(PRODUCTION.relative_to(ROOT))}


def main() -> int:
    if sys.platform != "darwin":
        raise SystemExit("BLOCKED_FAIL_CLOSED: Mac-only adapter path")
    require_sha256(AEX, EXPECTED_AEX_SHA256, "OLMDirectionalBlur.aex")
    require_sha256(SOURCE, EXPECTED_SOURCE_SHA256, "case_0001 source")
    with tempfile.TemporaryDirectory(prefix="olm_dblur_complete_compare_") as name:
        actual, actual_meta = capture_actual()
        image = Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278))
        rgba = image.tobytes()
        argb = bytes(v for pixel in (rgba[i:i+4] for i in range(0, len(rgba), 4)) for v in (pixel[3], pixel[0], pixel[1], pixel[2]))
        if sha256_bytes(argb) != EXPECTED_CROP_ARGB_SHA256:
            raise RuntimeError("BLOCKED_FAIL_CLOSED: case_0001 crop identity mismatch")
        if sha256_bytes(actual) != EXPECTED_ACTUAL_PF8_SHA256:
            raise RuntimeError("BLOCKED_FAIL_CLOSED: actual-AEX PF8 fixture identity mismatch")
        mac, mac_meta = capture_mac(argb, Path(name))
    mismatches = [i for i, (a, b) in enumerate(zip(actual, mac)) if a != b]
    status = "pass" if not mismatches and len(actual) == WIDTH * HEIGHT * 4 and mac_meta["exact"] == 1 else "blocked"
    stamp = "20260718"
    raw_actual = ROOT / f"refs/conformance/olmdirectionalblur_actual_aex_pf8_frame_{stamp}.argb8"
    raw_mac = ROOT / f"refs/conformance/olmdirectionalblur_mac_adapter_pf8_frame_{stamp}.argb8"
    report = ROOT / f"refs/conformance/olmdirectionalblur_complete_pf8_compare_{stamp}.json"
    note = ROOT / f"refs/conformance/olmdirectionalblur_complete_pf8_compare_{stamp}.md"
    raw_actual.write_bytes(actual); raw_mac.write_bytes(mac)
    result = {"schema": 1, "kind": "olmdirectionalblur_complete_pf8_compare_20260718",
              "status": status, "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "scope": "hash-bound 16x16 PF8, angle=0, brightness=1, front-strength=8, all variation/back/noise controls zero; actual-AEX natural output versus production Mac dispatcher",
              "dimensions": [WIDTH, HEIGHT], "packed_layout": "A/R/G/B", "byte_count": len(actual),
              "actual_aex": {**actual_meta, "sha256": sha256_bytes(actual), "raw": str(raw_actual.relative_to(ROOT))},
              "mac_adapter": {**mac_meta, "sha256": sha256_bytes(mac), "raw": str(raw_mac.relative_to(ROOT))},
              "comparison": {"byte_for_byte": not mismatches, "mismatch_count": len(mismatches),
                             "first_mismatch_byte": mismatches[0] if mismatches else None},
              "identity": {"aex_sha256": EXPECTED_AEX_SHA256,
                           "source_sha256": EXPECTED_SOURCE_SHA256,
                           "crop_argb_sha256": EXPECTED_CROP_ARGB_SHA256,
                           "actual_pf8_sha256": EXPECTED_ACTUAL_PF8_SHA256},
              "parameters": {"angle_degrees": 0, "brightness_gain": 1,
                             "front_strength": 8, "front_alpha_fade": 0,
                             "front_sharp_tail": 0, "back_strength": 0,
                             "back_alpha_fade": 0, "back_sharp_tail": 0,
                             "size_variation": 0, "noise_variation": 0,
                             "render_scale": [1, 1]},
              "fail_closed": {"production_dispatch_exercised": True,
                               "pinned_aex_input_and_output": True,
                               "windows_values_fabricated": False,
                               "ae_exact_claim": False, "complete_frame_required": True}}
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    note.write_text(f"# OLMDirectionalBlur Complete PF8 Compare {stamp}\n\n- Status: `{status}`.\n- Bounded case: `16x16 PF8`, angle `0`, brightness `1`, front strength `8`; alpha fade, sharp tail, back, size variation, and noise are all zero; render scale `1/1`.\n- AEX, source image, source crop, and actual-AEX PF8 output identities are SHA-256 pinned.\n- Same-run natural actual-AEX frame: `{actual_meta['output_complete']}`; callbacks: `{[c['callback'] for c in actual_meta['iterate_calls']]}`.\n- Production Mac dispatcher exact seam: `{mac_meta['exact']}`.\n- Byte count: `{len(actual)}`; mismatch count: `{len(mismatches)}`.\n- AE exact claim: `False`. This proves the fixture/core/production-dispatch boundary only.\n\nArtifacts: `{raw_actual.relative_to(ROOT)}`, `{raw_mac.relative_to(ROOT)}`, `{report.relative_to(ROOT)}`.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_complete_pf8_compare_20260718.py`\n", encoding="utf-8")
    print(json.dumps({"status": status, "byte_for_byte": not mismatches, "mismatch_count": len(mismatches),
                      "report": str(report.relative_to(ROOT)), "raw_actual": str(raw_actual.relative_to(ROOT)),
                      "raw_mac": str(raw_mac.relative_to(ROOT))}))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
