#!/usr/bin/env python3
"""Source-level proof for the two owned classic render dispatch paths."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNED_SOURCES = (
    ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp",
    ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp",
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
            assert "kPFWorldSuiteVersion2" in body, path
            assert "world_suite->PF_GetPixelFormat(input, &format)" in body, path
            assert "PF_WORLD_IS_DEEP" not in body, path

            mappings = (
                ("PF_PixelFormat_ARGB32", ("RenderBits<PF_Pixel8>", "bitdepth = 8;")),
                ("PF_PixelFormat_ARGB64", ("RenderBits<PF_Pixel16>", "bitdepth = 16;")),
                ("PF_PixelFormat_ARGB128", ("RenderBits<PF_PixelFloat>", "bitdepth = 32;")),
            )
            for pixel_format, dispatch_tokens in mappings:
                case = body.index(f"case {pixel_format}:")
                next_case_positions = [
                    pos for pos in (
                        body.find("\n\tcase ", case + 1),
                        body.find("\n\tdefault:", case + 1),
                    ) if pos >= 0
                ]
                next_case = min(next_case_positions, default=len(body))
                dispatch = body[case:next_case]
                assert any(token in dispatch for token in dispatch_tokens), (path, pixel_format)

            assert "default:\n\t\treturn PF_Err_BAD_CALLBACK_PARAM;" in body, path
            smart_render = source[source.index("SmartRender(PF_InData"):]
            assert "extra->input->bitdepth" in smart_render, path

        print("PASS classic render dispatch: ARGB32->8 ARGB64->16 ARGB128->32; unknown->PF_Err_BAD_CALLBACK_PARAM")
        print("PASS SmartRender dispatch remains driven by extra->input->bitdepth")


if __name__ == "__main__":
    unittest.main()
