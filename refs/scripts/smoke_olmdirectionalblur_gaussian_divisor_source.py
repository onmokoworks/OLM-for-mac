#!/usr/bin/env python3
"""Smoke-test the OLMDirectionalBlur Gaussian divisor source contract."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAC_SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
CLI_SOURCE = ROOT / "cli/OLMDirectionalBlur/main.cpp"


def require_contains(path: Path, needle: str) -> None:
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        raise AssertionError(f"{path} is missing expected text: {needle}")


def require_not_contains_near_function(path: Path, function_name: str, forbidden: str) -> None:
    text = path.read_text(encoding="utf-8")
    start = text.find(function_name)
    if start < 0:
        raise AssertionError(f"{path} is missing function marker: {function_name}")
    window = text[start : start + 900]
    if forbidden in window:
        raise AssertionError(f"{path} has forbidden text near {function_name}: {forbidden}")


def main() -> int:
    require_contains(MAC_SOURCE, "const float denom = 2.0f * ((float)length / 3.0f) * ((float)length / 3.0f) + 1.0e-5f;")
    require_not_contains_near_function(MAC_SOURCE, "DirectionalGaussianWeights", "/ 0.5f")
    require_contains(CLI_SOURCE, "const float ratio = static_cast<float>(length) / 3.0f;")
    require_not_contains_near_function(CLI_SOURCE, "gaussian_weights", "/ 0.5f")
    print("[OK] OLMDirectionalBlur Gaussian divisor source smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
