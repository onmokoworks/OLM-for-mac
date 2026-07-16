#!/usr/bin/env python3
"""Source-level proof for directional/radial classic render dispatch."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNED_SOURCES = (
    ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
    ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp",
)


def render_body(source: str) -> str:
    start = source.index("Render(PF_InData")
    end = source.index("SmartPreRender(PF_InData", start)
    return source[start:end]


class ClassicRenderBitdepthDispatchTests(unittest.TestCase):
    def test_classic_render_dispatch(self):
        for path in OWNED_SOURCES:
            source = path.read_text()
            body = render_body(source)
            assert "AEFX_SuiteScoper<PF_WorldSuite2>" in body, path
            assert "world_suite->PF_GetPixelFormat(input, &format)" in body, path
            assert "PF_WORLD_IS_DEEP" not in body, path
            for pixel_format, bitdepth in (
                ("PF_PixelFormat_ARGB32", "8"),
                ("PF_PixelFormat_ARGB64", "16"),
                ("PF_PixelFormat_ARGB128", "32"),
            ):
                case = body.index(f"case {pixel_format}:")
                assignment = body.index(f"= {bitdepth};", case)
                assert assignment < body.index("break;", case), (path, pixel_format)
            assert "default:\n\t\treturn PF_Err_BAD_CALLBACK_PARAM;" in body, path

            smart_render = source[source.index("SmartRender(PF_InData"):]
            assert "extra->input->bitdepth" in smart_render, path
            assert "CopyWorld<PF_Pixel16>" in source, path
            assert "CopyWorld<PF_PixelFloat>" in source, path

        print("PASS classic render dispatch: ARGB32->8 ARGB64->16 ARGB128->32; unknown->PF_Err_BAD_CALLBACK_PARAM")
        print("PASS SmartRender deep paths remain copy-only and use extra->input->bitdepth")


if __name__ == "__main__":
    unittest.main()
