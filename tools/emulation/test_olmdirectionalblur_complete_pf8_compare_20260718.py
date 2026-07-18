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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_fixture():
    sys.path.insert(0, str(FIXTURE_PATH.parent))
    import dblur_fullrender_host_fixture_20260711 as fixture  # noqa: E402
    return fixture


def capture_actual() -> tuple[bytes, dict]:
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
            Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278)).save(source)
            output = temp / "fixture.json"
            sys.argv = [str(FIXTURE_PATH), "--source", str(source), "--output", str(output),
                        "--angle", "0", "--downsample-num", "1", "--downsample-den", "1",
                        "--front-strength", "8", "--size-variation", "0",
                        "--front-sharp-tail", "0", "--back-strength", "0",
                        "--back-alpha-fade", "0", "--noise-variation", "0",
                        "--world-area", "0", "0", "16", "16", "--row-padding", "12",
                        "--no-detour-rotate", "--max-instructions", "20000000"]
            status = fixture.main()
            report = json.loads(output.read_text(encoding="utf-8"))
    finally:
        fixture.model_output = original
    calls = report["execution"]["iterate_calls"]
    complete = (report["output"].get("complete") is True
                and [c["callback"] for c in calls] == ["0x180006980", "0x180006b30"]
                and len(captured) == WIDTH * HEIGHT * 4)
    if not complete:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: natural actual-AEX frame incomplete")
    return bytes(captured), {
        "fixture_status": report["status"],
        "iterate_calls": calls,
        "output_complete": report["output"].get("complete"),
        "writer": hex(writer),
    }


def capture_mac(argb: bytes, temp: Path) -> tuple[bytes, dict]:
    compiler = os.environ.get("CXX", "clang++")
    source_array = ",".join(str(value) for value in argb)
    production = str(PRODUCTION).replace("\\", "\\\\").replace('"', '\\"')
    probe = temp / "complete_pf8_mac_probe.cpp"
    executable = temp / "complete_pf8_mac_probe"
    probe.write_text(f'''#define OLM_DBLUR_TEST_SEAM 1
#include "{production}"
#include <array>
#include <cstdio>
#include <cstdint>
int main() {{
  constexpr int W=16, H=16, RB=76;
  const std::uint8_t input_bytes[] = {{{source_array}}};
  std::array<std::uint8_t, RB*H> in_bytes{{}}, out_bytes{{}};
  for (int y=0; y<H; ++y) for (int x=0; x<W*4; ++x) in_bytes[y*RB+x]=input_bytes[y*W*4+x];
  PF_EffectWorld in{{}}, out{{}};
  in.data=(PF_PixelPtr)in_bytes.data(); in.rowbytes=RB; in.width=W; in.height=H;
  in.extent_hint={{0,0,W,H}}; out.data=(PF_PixelPtr)out_bytes.data(); out.rowbytes=RB;
  out.width=W; out.height=H; out.extent_hint={{0,0,W,H}};
  OLMDirectionalBlurInfo info{{}}; info.angle_deg=0; info.brightness_gain=1;
  info.front_strength=8; info.render_scale_x=1; info.render_scale_y=1;
  int exact=0; if (OLMDirectionalBlurTestRenderWorld(&in,&out,&info,8,&exact)!=PF_Err_NONE || !exact) return 2;
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
                    "production_source": str(PRODUCTION.relative_to(ROOT))}


def main() -> int:
    if sys.platform != "darwin":
        raise SystemExit("BLOCKED_FAIL_CLOSED: Mac-only adapter path")
    with tempfile.TemporaryDirectory(prefix="olm_dblur_complete_compare_") as name:
        actual, actual_meta = capture_actual()
        image = Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278))
        rgba = image.tobytes()
        argb = bytes(v for pixel in (rgba[i:i+4] for i in range(0, len(rgba), 4)) for v in (pixel[3], pixel[0], pixel[1], pixel[2]))
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
              "scope": "same-run bounded actual-AEX natural PF8 output versus current Mac adapter",
              "dimensions": [WIDTH, HEIGHT], "packed_layout": "A/R/G/B", "byte_count": len(actual),
              "actual_aex": {**actual_meta, "sha256": sha256_bytes(actual), "raw": str(raw_actual.relative_to(ROOT))},
              "mac_adapter": {**mac_meta, "sha256": sha256_bytes(mac), "raw": str(raw_mac.relative_to(ROOT))},
              "comparison": {"byte_for_byte": not mismatches, "mismatch_count": len(mismatches),
                             "first_mismatch_byte": mismatches[0] if mismatches else None},
              "fail_closed": {"production_source_edited": False, "windows_values_fabricated": False,
                               "ae_exact_claim": False, "complete_frame_required": True}}
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    note.write_text(f"# OLMDirectionalBlur Complete PF8 Compare {stamp}\n\n- Status: `{status}`.\n- Same-run natural actual-AEX frame: `{actual_meta['output_complete']}`; callbacks: `{[c['callback'] for c in actual_meta['iterate_calls']]}`.\n- Mac adapter exact seam: `{mac_meta['exact']}`.\n- Byte count: `{len(actual)}`; mismatch count: `{len(mismatches)}`.\n- AE exact claim: `False`; production source edited: `False`.\n\nArtifacts: `{raw_actual.relative_to(ROOT)}`, `{raw_mac.relative_to(ROOT)}`, `{report.relative_to(ROOT)}`.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_complete_pf8_compare_20260718.py`\n", encoding="utf-8")
    print(json.dumps({"status": status, "byte_for_byte": not mismatches, "mismatch_count": len(mismatches),
                      "report": str(report.relative_to(ROOT)), "raw_actual": str(raw_actual.relative_to(ROOT)),
                      "raw_mac": str(raw_mac.relative_to(ROOT))}))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
