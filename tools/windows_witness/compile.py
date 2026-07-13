#!/usr/bin/env python3
"""Command-line entrypoint for the Windows witness compiler."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.windows_witness.compiler import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
