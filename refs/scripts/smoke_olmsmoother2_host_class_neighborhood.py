#!/usr/bin/env python3
"""Guard the env-gated Smoother2 host class-neighborhood trace."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    source = (ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp").read_text()
    assert 'std::getenv("OLM_SMOOTHER2_HOST_TRACE")' in source
    assert "for (int dy = -2; dy <= 2; ++dy)" in source
    assert "for (int dx = -2; dx <= 2; ++dx)" in source
    assert "class_neighbor xy=%d,%d offset=%d,%d class=%u,%u,%u,%u" in source
    print("[OK] OLMSmoother2 host trace includes a fail-local 5x5 class neighborhood")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
