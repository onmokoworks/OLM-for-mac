#!/usr/bin/env python3
"""Narrow source contract for classic PF_Cmd_RENDER bit-depth dispatch."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNED_SOURCES = (
    ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp",
    ROOT / "mac/OLMSmoother2/OLMSmoother2.cpp",
)


def render_body(source: str) -> str:
    start = source.index("Render(PF_InData")
    end = source.index("SmartPreRender(PF_InData", start)
    return source[start:end]


def case_body(body: str, pixel_format: str) -> str:
    start = body.index(f"case {pixel_format}:")
    end = body.find("case ", start + 5)
    return body[start:] if end == -1 else body[start:end]


class ClassicRenderBitdepthDispatchTests(unittest.TestCase):
    def test_classic_render_dispatch(self):
        for path in OWNED_SOURCES:
            source = path.read_text()
            body = render_body(source)
            assert (
                "AEFX_SuiteScoper<PF_WorldSuite2>" in body
                or "AEFX_AcquireSuite(in_data, out_data, kPFWorldSuite, kPFWorldSuiteVersion2" in body
            ), path
            assert "world_suite->PF_GetPixelFormat(input, &format)" in body, path
            assert "PF_WORLD_IS_DEEP" not in body, path
            if path.name == "OLMKiraKira.cpp":
                expected_dispatch = (
                    ("PF_PixelFormat_ARGB32", "= 8;"),
                    ("PF_PixelFormat_ARGB64", "= 16;"),
                    ("PF_PixelFormat_ARGB128", "= 32;"),
                )
            else:
                expected_dispatch = (
                    ("PF_PixelFormat_ARGB32", "RenderBits<PF_Pixel8>"),
                    ("PF_PixelFormat_ARGB64", "RenderBits<PF_Pixel16>"),
                    ("PF_PixelFormat_ARGB128", "RenderBits<PF_PixelFloat>"),
                )
            for pixel_format, dispatch in expected_dispatch:
                assert dispatch in case_body(body, pixel_format), (path, pixel_format)
            assert "default:\n\t\treturn PF_Err_BAD_CALLBACK_PARAM;" in body, path

            smart_render = source[source.index("SmartRender(PF_InData"):]
            assert "extra->input->bitdepth" in smart_render, path

        print("PASS classic dispatch: ARGB32->8 ARGB64->16 ARGB128->32; SmartRender preserved")


if __name__ == "__main__":
    unittest.main()
