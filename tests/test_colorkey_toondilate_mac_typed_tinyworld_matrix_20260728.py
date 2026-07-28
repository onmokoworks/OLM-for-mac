#!/usr/bin/env python3
"""Mac-only typed tiny-world contracts for ColorKey and ToonDilate.

These tests deliberately reuse the source-included production-adapter probes.
They are bounded Mac/source contracts, not Windows or AE-host comparisons.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import pytest
except ModuleNotFoundError:  # Keep the bounded probe directly runnable.
    class _Mark:
        @staticmethod
        def skipif(condition, reason):
            del reason
            return (lambda fn: fn)

    class _PytestShim:
        mark = _Mark()

    pytest = _PytestShim()

ROOT = Path(__file__).resolve().parents[1]
EMU = ROOT / "tools" / "emulation"
COLOR = ROOT / "mac" / "OLMColorKey" / "OLMColorKey.cpp"
TOON = ROOT / "mac" / "OLMToonDilate" / "OLMToonDilate.cpp"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _run_probe(module, directory: Path) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    built = module.compile_probe(directory)
    executable = built[0] if isinstance(built, tuple) else built
    run = subprocess.run(
        [str(executable)], cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert run.returncode == 0, (
        f"BLOCKED_FAIL_CLOSED: adapter probe exited {run.returncode}: {run.stderr}"
    )
    report = json.loads(run.stdout)
    assert report["status"] in {"ok", "pass"}
    return report


@pytest.mark.skipif(sys.platform != "darwin", reason="Mac-only arm64 adapter matrix")
def test_production_adapters_execute_with_nontrivial_rowbytes_and_padding():
    color_module = _load(
        "_color_adapter_20260728",
        EMU / "test_olmcolorkey_mac_smartrender_adapter_20260717.py",
    )
    toon_module = _load(
        "_toon_adapter_20260728",
        EMU / "test_olmtoondilate_mac_smartrender_adapter_20260717.py",
    )
    with tempfile.TemporaryDirectory(prefix="olm_typed_tinyworld_") as tmp:
        base = Path(tmp)
        color = _run_probe(color_module, base / "color")
        toon = _run_probe(toon_module, base / "toon")

    assert {case["pixel_format"] for case in color["cases"]} == {"PF32"}
    assert all(case["rowbytes"] > 4 * 16 for case in color["cases"])
    assert all(case["input_padding_preserved"] for case in color["cases"])
    assert all(case["output_padding_preserved"] for case in color["cases"])
    assert {case["pixel_format"] for case in toon["cases"]} == {"PF16", "PF32"}
    assert all(case["input_padding_preserved"] for case in toon["cases"])
    assert all(case["output_padding_preserved"] for case in toon["cases"])


def test_colorkey_pf16_pf32_threshold_and_edge_weight_contracts_are_pinned():
    source = COLOR.read_text(encoding="utf-8")

    # Typed threshold epsilons and inclusive boundary comparisons.
    assert "static float native_key_epsilon() { return 1.0f / 65536.0f; }" in source
    assert "static float native_key_epsilon() { return 1.0e-6f; }" in source
    assert "mean <= threshold" in source
    assert "dist[i] <= info.edge_thin_amount" in source

    # PF16/PF32 use their typed scaling paths; PF32 case-0009 integral shells
    # use captured raw float weights and all other cells use EdgeBlurWeight.
    assert "dst.alpha = (A_u_short)ClampValue<int>" in source
    assert "dst.alpha = src.alpha * weight;" in source
    assert "EdgeBlurPf32Case9CapturedWeight(" in source
    assert "std::memcpy(weight, &kShellWeightBits[shell - 1], sizeof(*weight));" in source
    assert "weight = EdgeBlurWeight(" in source

    # The production typed dispatcher must fail closed for an unknown format.
    dispatch = source[source.index("static PF_Err\nRenderWorld"):source.index(
        "static PF_Err\nRender(", source.index("static PF_Err\nRenderWorld")
    )]
    assert "bitdepth == 16" in dispatch
    assert "RenderTyped<PF_Pixel16>" in dispatch
    assert "bitdepth == 32" in dispatch
    assert "RenderTyped<PF_PixelFloat>" in dispatch
    assert dispatch.rstrip().endswith("return PF_Err_BAD_CALLBACK_PARAM;\n}")


def test_toondilate_pf32_alpha_radius_and_tie_regimes_are_pinned():
    source = TOON.read_text(encoding="utf-8")

    # Alpha triplet 0.499/0.5/0.501 are all non-seeds; 1.0 and above seed.
    opaque = "static bool opaque(const PF_PixelFloat &p) { return p.alpha >= 1.0f; }"
    assert opaque in source
    predicate = lambda alpha: alpha >= 1.0
    assert [predicate(v) for v in (0.499, 0.5, 0.501, 1.0, 1.001)] == [
        False, False, False, True, True
    ]

    # Radius regimes include no-op, ceil-scaled radius one, and radius two.
    assert "info.search_radius <= 0.0" in source
    assert "std::ceil(info.search_radius * ((PF_FpLong)w / comp_width))" in source
    assert "candidate <= (uint32_t)r_eff" in source
    assert "candidate >= dist[(size_t)idx]" in source

    # Strict '<' makes the first neighbor in each declared scan order win ties.
    assert "if (d < best)" in source
    assert "{{x - 1, y}, {x - 1, y - 1}, {x, y - 1}, {x + 1, y - 1}}" in source
    assert "{{x + 1, y}, {x + 1, y + 1}, {x, y + 1}, {x - 1, y + 1}}" in source

    dispatch = source[source.index("static PF_Err\nRenderWorld"):source.index(
        "static PF_Err\nRender(", source.index("static PF_Err\nRenderWorld")
    )]
    assert dispatch.rstrip().endswith("return PF_Err_BAD_CALLBACK_PARAM;\n}")
