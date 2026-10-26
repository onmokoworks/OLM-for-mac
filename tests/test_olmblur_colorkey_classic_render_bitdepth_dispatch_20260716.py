#!/usr/bin/env python3
"""Source-level contract for classic render pixel-format dispatch."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNED_SOURCES = (
    ROOT / "mac/OLMBlur/OLMBlur.cpp",
    ROOT / "mac/OLMColorKey/Render.inc",
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
            if path.name == "OLMBlur.cpp":
                # The actual classic owner distinguishes only PF8/PF16 from
                # PF_WorldFlag_DEEP. PF32 is owned only by Smart Render.
                assert "world_suite->PF_GetPixelFormat(input, &input_format)" in body
                assert "world_suite->PF_GetPixelFormat(output, &output_format)" in body
                assert "input_format != output_format" in body
                assert "case PF_PixelFormat_ARGB32:" in body
                assert "case PF_PixelFormat_ARGB64:" in body
                pf32 = body.index("case PF_PixelFormat_ARGB128:")
                assert body.index("return PF_Err_BAD_CALLBACK_PARAM;", pf32) < body.index("default:", pf32)
            else:
                assert "world_suite->PF_GetPixelFormat(input, &format)" in body, path
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

        print("PASS classic dispatch: OLMBlur PF8/PF16 + PF32 fail-close; ColorKey all depths; unknown rejected")


if __name__ == "__main__":
    unittest.main()
