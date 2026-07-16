#!/usr/bin/env python3
"""Focused source contract for the authorized ToonDilate candidate fix."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "premultiply_semi_alpha",
        "p.red *= p.alpha",
        "p.green *= p.alpha",
        "p.blue *= p.alpha",
        "* (A_long)p.alpha",
    )
    violations = [token for token in forbidden if token in source]
    dispatch = all(token in source for token in (
        "RenderTyped<PF_Pixel8>",
        "RenderTyped<PF_Pixel16>",
        "RenderTyped<PF_PixelFloat>",
    ))
    if violations or not dispatch:
        print({"status": "FAIL", "violations": violations, "typed_dispatch": dispatch})
        return 1
    print({
        "status": "PASS_NO_RGB_ALPHA_POSTPASS",
        "typed_dispatch": dispatch,
        "forbidden_tokens_absent": True,
        "claim_boundary": "Mac source contract only; candidate/CLI/binary-grounded, not AE exact",
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
