#!/usr/bin/env python3
"""Summarize available AEX files and Ghidra export artifacts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "plugins_2025"
DECOMP_DIR = ROOT / "decomp"
DISASM_DIR = ROOT / "disasm"


def size(path):
    if not path.exists():
        return "-"
    n = path.stat().st_size
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def main():
    print("Plugin, AEX, Decomp, Disasm")
    for aex in sorted(PLUGIN_DIR.glob("*.aex")):
        stem = aex.name
        decomp = DECOMP_DIR / f"{stem}.c.txt"
        disasm = DISASM_DIR / f"{stem}.asm.txt"
        print(f"{stem}, {size(aex)}, {size(decomp)}, {size(disasm)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

