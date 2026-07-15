#!/usr/bin/env python3
"""Local regression for the bounded KiraKira Merge-Mode-2 proof."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from prove_olmkirakira_merge2_address_contract_20260716 import (  # noqa: E402
    model_checks,
    static_checks,
)


def main() -> int:
    static = static_checks()
    model = model_checks()
    assert all(static.values()), static
    assert all(model.values()), model
    print(f"PASS static={sum(static.values())}/{len(static)} model={sum(model.values())}/{len(model)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
