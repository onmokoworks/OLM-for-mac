#!/usr/bin/env python3
"""Independent PF32 Zoom small-frame actual-AEX/production fixture."""

import hashlib, json, struct, subprocess
import test_olmradialblur_zoom_pf8_small_actual_aex_20260805 as fixture

fixture.FIXTURE = fixture.ROOT / "refs/fixtures/olmradialblur_zoom_pf32_small_20260805"
fixture.REPORT = fixture.ROOT / "refs/conformance/olmradialblur_zoom_pf32_small_actual_aex_20260805.json"
fixture.W, fixture.H, fixture.ROWBYTES, fixture.VISIBLE = 9, 7, 160, 144
fixture.SOURCE_KEY = "source_pf32"
fixture.BITDEPTH = 32
fixture.PIXEL_CPP = "PF_PixelFloat"
fixture.PIXEL_BYTES = 16
fixture.OWNER = 0x180007D30
fixture.ZOOM_RETURN = 0x180008322
fixture.USE_RENDER_WORLD_FINAL = True
fixture.KIND = "olmradialblur_zoom_pf32_small_actual_aex_20260805"
fixture.SCOPE = "independent PF32 Zoom outer-only Strength4/mode1/offset0, padded 9x7; no PF8/PF16 source or quantization reuse and no AE-host claim"
fixture.TYPED_CONTRACT = {"source": "independent PF_PixelFloat ARGB words", "writer": "FUN_180017490 direct float stores", "radius_neighbor": "deep unclamped", "integer_quantization_reused": False}
fixture.EXPECTED = {
    "source_pf32": ("edc1a4f6c03f8b0e05bef4d9ae7a2a8a1b0b217c214e747076bfeda8fea60f04", "e1baf8a5b51586b3808e914d5a227deb1fb9293c3a7bc609414c1036a894d4f7"),
    "pre_blur": ("65468046f663d30ac544be430c965ee2c305193561e09d4bf9753747e4cb24ff", "1bc876bcc635af129c2c587ee2bbaf52dcb6eb15f08bc0fb145861357d7e4fd0"),
    "post_blur": ("a946ef09d52d4c498de2e532f8654405461e73c7524d3af99883afb0c2e3b65a", "d72223cc413589c3a2f14ed285613e1951a54b0c03d482580eb4955fd08785b6"),
    "output": ("17889d6d9d5f0f74c39c72a847eeefe51638e3fc6b4c4403cc300e46ccb55d01", "47d9d1939ff45eacd34e0d7521a5500237155437ed6048c9cd3b5c75bf2372c5"),
}


def source_frame(output_seed: bool = False) -> bytes:
    raw = bytearray(fixture.ROWBYTES * fixture.H)
    for y in range(fixture.H):
        for x in range(fixture.W):
            if output_seed:
                argb = (0.7, 0.6, 0.5, 0.4)
            else:
                argb = (
                    1.0 if (x + y) % 5 else 0.5,
                    ((x * 31 + y * 7) % 257) / 256.0,
                    ((x * 11 + y * 29) % 257) / 256.0,
                    ((x * 47 + y * 13) % 257) / 256.0,
                )
            struct.pack_into("<4f", raw, y * fixture.ROWBYTES + x * 16, *argb)
        raw[y * fixture.ROWBYTES + fixture.VISIBLE:(y + 1) * fixture.ROWBYTES] = bytes([0xA0 + y]) * (fixture.ROWBYTES - fixture.VISIBLE)
    return bytes(raw)


fixture.source_frame = source_frame


def main():
    code = fixture.main()
    report = json.loads(fixture.REPORT.read_text())
    binary = fixture.Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur"
    installed_hash = hashlib.sha256(binary.read_bytes()).hexdigest() if binary.is_file() else None
    arch = subprocess.run(["lipo", "-archs", str(binary)], capture_output=True, text=True).stdout.split() if binary.is_file() else []
    report["installed_connection"] = {
        "binary": str(binary),
        "sha256": installed_hash,
        "expected_current_sha256": "2e079e3c168666c2f3509f8d4c90ab107301880bce43f538cf4e16bcb8047732",
        "identity_exact": installed_hash == "2e079e3c168666c2f3509f8d4c90ab107301880bce43f538cf4e16bcb8047732",
        "architectures": arch,
        "source_to_installed_connection": "same current OLMRadialBlur.cpp built, signed, and installed in the preceding PF8 boundary; no production source change in this PF32 pass",
    }
    report["full_path"] = ["PF32 owner 0x180007d30", "Zoom core 0x1800056f0", "pre-blur plane", "post-blur plane", "FUN_180017490 direct-float writer", "current installed Universal bundle"]
    report["production_dispatch"] = "final compared output is emitted by OLMRadialBlurTestRenderWorld(bitdepth=32), not a direct RenderZoomTyped call"
    fixture.REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return code if report["installed_connection"]["identity_exact"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
