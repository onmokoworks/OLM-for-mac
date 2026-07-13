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
        if "short bitdepth = PF_WORLD_IS_DEEP(output) ? 16 : 8;" not in text:
            raise SystemExit(f"{path}: legacy render depth boundary changed")

    print("32bpc host/path smoke: PASS (smart depth dispatch and float contract present)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
