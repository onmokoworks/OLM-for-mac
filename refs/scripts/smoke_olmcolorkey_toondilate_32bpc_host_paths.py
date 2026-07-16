#!/usr/bin/env python3
"""Guard the bounded 32bpc Mac host/path contract for two OLM modules."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    checks = {
        ROOT / "mac/OLMColorKey/OLMColorKey.cpp": [
            "RenderTyped<PF_PixelFloat>",
            "extra->input->bitdepth",
            "PF_OutFlag2_FLOAT_COLOR_AWARE",
        ],
        ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp": [
            "RenderTyped<PF_PixelFloat>",
            "extra->input->bitdepth",
            "PF_OutFlag2_FLOAT_COLOR_AWARE",
        ],
    }
    for path, needles in checks.items():
        text = path.read_text()
        missing = [needle for needle in needles if needle not in text]
        if missing:
            raise SystemExit(f"{path}: missing {missing}")
        format_dispatch = [
            "PF_GetPixelFormat(input, &format)",
            "case PF_PixelFormat_ARGB32:",
            "case PF_PixelFormat_ARGB64:",
            "case PF_PixelFormat_ARGB128:",
        ]
        missing_dispatch = [needle for needle in format_dispatch if needle not in text]
        if missing_dispatch:
            raise SystemExit(f"{path}: incomplete legacy-render pixel-format dispatch: {missing_dispatch}")
        if "PF_WORLD_IS_DEEP(output) ? 16 : 8" in text:
            raise SystemExit(f"{path}: legacy render still collapses 32bpc into the 16bpc path")

    print("32bpc host/path smoke: PASS (legacy pixel-format and smart depth dispatch present)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
