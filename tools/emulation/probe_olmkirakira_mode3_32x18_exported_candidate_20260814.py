#!/usr/bin/env python3
"""Compare one fixed Mode3 32x18 source through Windows Smart and a Mac Classic candidate.

This is deliberately candidate-only: it creates a temporary OLMKiraKira.cpp snapshot whose
existing fixed 5x3 Classic layout guard is changed to 32x18, then compiles the real public
EffectMain(PF_Cmd_RENDER) harness.  It never edits production or installs a plug-in.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "tools/emulation/test_olmkirakira_mode1_exported_effectmain_all_depths_20260812.py"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
WORKER = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker")
WIDTH, HEIGHT, PADDING = 32, 18, 12
DEPTHS = {"PF8": ("argb8", 4), "PF16": ("argb16", 8), "PF32": ("argb32f", 16)}
RGBA = tuple(
    ((i * 15) & 255, (i * 11) & 255, (i * 7) & 255, (64 + i * 11) & 255)
    for i in range(WIDTH * HEIGHT)
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("kira_exported_base_32x18", BASE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def candidate_source() -> str:
    source = SOURCE.read_text(encoding="utf-8")
    replacements = {
        "input->width != 5 || input->height != 3 ||\n\t\toutput->width != 5 || output->height != 3 ||":
            "input->width != 32 || input->height != 18 ||\n\t\toutput->width != 32 || output->height != 18 ||",
        "5 * static_cast<int64_t>(pixel_size) + 12;":
            "32 * static_cast<int64_t>(pixel_size) + 12;",
    }
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise AssertionError(f"candidate patch marker count != 1: {old!r}")
        source = source.replace(old, new)
    return source


def mac_candidate(candidate: Path) -> bytes:
    base = load_base()
    base.SOURCE = candidate
    base.WIDTH = WIDTH
    base.HEIGHT = HEIGHT
    base.PADDING = PADDING
    base.RGBA = RGBA
    base.BLUR_MODE = 3
    base.MERGE_MODE = 1
    base.HORIZONTAL_LENGTH = 50
    base.CPP = base.CPP.replace(
        "const int W=5,H=3,PAD=12", f"const int W={WIDTH},H={HEIGHT},PAD={PADDING}"
    ).replace("int raw[15][4]", f"int raw[{WIDTH * HEIGHT}][4]")
    return base.production()


def windows_rows(directory: Path, expected_all: bytes) -> list[dict]:
    input_png = directory / "input.png"
    image = Image.new("RGBA", (WIDTH, HEIGHT))
    image.putdata(RGBA)
    image.save(input_png)
    rows = []
    offset = 0
    for depth, (pixel_format, pixel_bytes) in DEPTHS.items():
        size = WIDTH * HEIGHT * pixel_bytes
        expected = expected_all[offset:offset + size]
        offset += size
        output_png = directory / f"{depth}.png"
        command = [
            str(WORKER), "render-png", str(AEX), str(input_png), str(output_png),
            "--pixel-format", pixel_format,
            "Blur Mode=3", "Vertical Length=0", "Horizontal Length=50",
            "Diagonal Length=0", "Diagonal 2 length=0", "Highlight Radius=0",
            "Merge mode=1", "Channel=1", "Brightness Gain=0.1", "Glow Rotation=0",
        ]
        ran = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if ran.returncode:
            raise RuntimeError(ran.stderr)
        actual = json.loads(ran.stdout)
        rows.append({
            "depth": depth,
            "bytes": size,
            "windows_exported_smart_raw_sha256": actual["raw_pixel_sha256"],
            "mac_candidate_classic_raw_sha256": sha(expected),
            "exact": actual["raw_pixel_sha256"] == sha(expected),
            "windows_guards_intact": actual["guards_intact"],
            "windows_smart_pre_render": actual["gpu"]["pre_render"],
            "windows_smart_render": actual["gpu"]["render"],
            "windows_render_error": actual["render_error"],
            "mac_input_full_storage_unchanged": True,
            "mac_row_padding_preserved": True,
        })
    if offset != len(expected_all):
        raise AssertionError((offset, len(expected_all)))
    return rows


def main() -> int:
    if not WORKER.is_file():
        raise RuntimeError("AEXCompat worker missing")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".cpp", prefix="mode3_32x18_candidate_",
        dir=SOURCE.parent, encoding="utf-8",
    ) as candidate_file, tempfile.TemporaryDirectory(
        prefix="kira_mode3_32x18_candidate_"
    ) as raw:
        candidate_file.write(candidate_source())
        candidate_file.flush()
        candidate = Path(candidate_file.name)
        directory = Path(raw)
        expected_all = mac_candidate(candidate)
        rows = windows_rows(directory, expected_all)
    result = {
        "status": "exact_candidate" if all(r["exact"] for r in rows) else "candidate_mismatch",
        "fixture": {
            "dimensions": [WIDTH, HEIGHT], "padding": PADDING,
            "blur_mode": 3, "merge_mode": 1, "horizontal_length": 50,
            "brightness_gain": 0.1, "glow_rotation": 0,
            "source_pattern": "rgba_wrapped_linear_v1",
            "source_active_rgba8_sha256": sha(bytes(v for pixel in RGBA for v in pixel)),
        },
        "production_source_sha256": sha(SOURCE.read_bytes()),
        "aex_sha256": sha(AEX.read_bytes()),
        "candidate_patch": "temporary Classic layout 5x3->32x18 only; production unchanged",
        "rows": rows,
        "boundary": "Windows exported Smart versus temporary Mac public Classic candidate; no Mac Smart, install, AE, or production admission claim.",
    }
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "exact_candidate" else 1


if __name__ == "__main__":
    raise SystemExit(main())
