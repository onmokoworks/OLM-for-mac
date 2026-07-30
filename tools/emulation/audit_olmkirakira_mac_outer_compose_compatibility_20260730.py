#!/usr/bin/env python3
"""AE-free compatibility audit for OLMKiraKira's Mac outer compose.

The Windows expectations come from the already-grounded scalar oracle.  This
audit does not render, load a plug-in, or mutate a conformance artifact.
"""

from __future__ import annotations

import importlib.util
import json
import re
import struct
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
MAC_SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
ORACLE_PATH = ROOT / "tools/emulation/olmkirakira_outer_compose_oracle_20260728.py"

FIXTURE = {
    "source": (0.20, 0.40, 0.70, 0.35),
    "glow": (0.90, 0.10, 0.50, 0.60),
    "source_opacity": 0.50,
    "glow_opacity": 0.75,
}


def _load_oracle():
    spec = importlib.util.spec_from_file_location("olmkirakira_outer_compose_oracle", ORACLE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load oracle: {ORACLE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ORACLE = _load_oracle()


def _strip_cpp_comments(source: str) -> str:
    """Remove comments while retaining strings and character literals."""

    pattern = re.compile(
        r"""
        //[^\r\n]*              | # line comment
        /\*.*?\*/               | # block comment
        "(?:\\.|[^"\\])*"       | # string literal
        '(?:\\.|[^'\\])*'         # character literal
        """,
        re.DOTALL | re.VERBOSE,
    )

    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        return token if token.startswith(("\"", "'")) else " "

    return pattern.sub(replace, source)


def _active_constant_preprocessor(source: str) -> str | None:
    """Keep active #if 0/#if 1 branches; reject unsupported conditionals."""

    output: list[str] = []
    # Each frame is (parent_active, condition_value, else_seen).
    stack: list[tuple[bool, bool, bool]] = []
    active = True
    directive = re.compile(r"^\s*#\s*(\w+)(?:\s+(.*?))?\s*$")
    for line in source.splitlines(keepends=True):
        match = directive.match(line.rstrip("\r\n"))
        if match is None:
            if active:
                output.append(line)
            continue

        keyword = match.group(1)
        argument = (match.group(2) or "").strip()
        if keyword == "if":
            if argument not in {"0", "1"}:
                return None
            condition = argument == "1"
            stack.append((active, condition, False))
            active = active and condition
        elif keyword == "else":
            if argument or not stack:
                return None
            parent_active, condition, else_seen = stack[-1]
            if else_seen:
                return None
            stack[-1] = (parent_active, condition, True)
            active = parent_active and not condition
        elif keyword == "endif":
            if argument or not stack:
                return None
            parent_active, _, _ = stack.pop()
            active = parent_active
        elif keyword in {"ifdef", "ifndef", "elif"}:
            return None
        elif active:
            # Non-conditional directives do not affect source-shape parsing.
            output.append(line)

    if stack:
        return None
    return "".join(output)


def _render_typed_body(source: str) -> str | None:
    """Return only the brace-balanced RenderTyped function body."""

    clean = _strip_cpp_comments(source)
    signature = re.search(
        r"template\s*<[^>]+>\s*static\s+PF_Err\s+RenderTyped\s*\([^)]*\)",
        clean,
        re.DOTALL,
    )
    if signature is None:
        return None
    opening = clean.find("{", signature.end())
    if opening < 0:
        return None
    depth = 0
    for index in range(opening, len(clean)):
        if clean[index] == "{":
            depth += 1
        elif clean[index] == "}":
            depth -= 1
            if depth == 0:
                return _active_constant_preprocessor(clean[opening + 1:index])
    return None


def _compact(expression: str) -> str:
    return re.sub(r"\s+", "", expression)


def _assignment_rhs(body: str, target: str) -> list[str]:
    """Collect complete semicolon-terminated RHS expressions for a target."""

    return [
        _compact(match.group(1))
        for match in re.finditer(
            rf"(?<![\w.>]){re.escape(target)}\s*=\s*([^;]+);",
            body,
            re.DOTALL,
        )
    ]


def classify_source_shape(source_text: str) -> dict[str, bool]:
    """Classify exact assignments confined to the current RenderTyped body."""

    body = _render_typed_body(source_text)
    if body is None:
        return {
            "render_typed_body_found": False,
            "screen_rgb": False,
            "source_alpha_passthrough": False,
            "outer_mode_branch": False,
            "outer_alpha_normalization": False,
        }

    expected_rgb = {
        channel: _compact(
            f"1.0f - (1.0f - src.{channel}) * "
            f"(1.0f - Clamp01(glow[idx].{channel} * glow_a))"
        )
        for channel in ("r", "g", "b")
    }
    screen_rgb = all(
        _assignment_rhs(body, f"out.{channel}") == [expected]
        for channel, expected in expected_rgb.items()
    )
    source_alpha_passthrough = _assignment_rhs(body, "out.a") == ["src_a"]
    return {
        "render_typed_body_found": True,
        "screen_rgb": screen_rgb,
        "source_alpha_passthrough": source_alpha_passthrough,
        "outer_mode_branch": bool(re.search(r"\bmerge_mode\s*==", body)),
        "outer_alpha_normalization": bool(
            re.search(r"\bsource_alpha\s*\+\s*glow_alpha\b", body)
        ),
    }


def _rgba_f32_hex(rgba: Sequence[float]) -> str:
    return struct.pack("<4f", *(ORACLE.f32(value) for value in rgba)).hex()


def current_mac_screen_pixel(
    source: Sequence[float],
    glow: Sequence[float],
    *,
    source_opacity: float,
    glow_opacity: float,
) -> tuple[float, float, float, float]:
    """Model the scalar shape currently present in RenderTyped."""

    src = tuple(ORACLE.f32(value) for value in source)
    glw = tuple(ORACLE.f32(value) for value in glow)
    glow_alpha = ORACLE.clamp_fun_181156740(
        ORACLE.f32(glw[3] * ORACLE.f32(glow_opacity))
    )
    rgb = []
    for channel in range(3):
        glow_term = ORACLE.clamp_fun_181156740(
            ORACLE.f32(glw[channel] * glow_alpha)
        )
        rgb.append(
            ORACLE.f32(
                ORACLE.f32(1.0)
                - ORACLE.f32(
                    ORACLE.f32(ORACLE.f32(1.0) - src[channel])
                    * ORACLE.f32(ORACLE.f32(1.0) - glow_term)
                )
            )
        )
    alpha = ORACLE.f32(src[3] * ORACLE.f32(source_opacity))
    return (rgb[0], rgb[1], rgb[2], alpha)


def audit(mac_source: str | None = None) -> dict[str, Any]:
    source_text = MAC_SOURCE.read_text(encoding="utf-8") if mac_source is None else mac_source
    current = current_mac_screen_pixel(
        FIXTURE["source"],
        FIXTURE["glow"],
        source_opacity=FIXTURE["source_opacity"],
        glow_opacity=FIXTURE["glow_opacity"],
    )
    mode1 = ORACLE.compose_pixel(
        FIXTURE["glow"],
        FIXTURE["source"],
        glow_opacity=FIXTURE["glow_opacity"],
        source_opacity=FIXTURE["source_opacity"],
        merge_mode=1,
    )
    mode2 = ORACLE.compose_pixel(
        FIXTURE["glow"],
        FIXTURE["source"],
        glow_opacity=FIXTURE["glow_opacity"],
        source_opacity=FIXTURE["source_opacity"],
        merge_mode=2,
    )

    shape = classify_source_shape(source_text)
    incompatible = (
        shape["screen_rgb"]
        and shape["source_alpha_passthrough"]
        and current != mode1
        and current != mode2
        and mode1 != mode2
    )
    return {
        "classification": (
            "incompatible-screen-source-alpha-passthrough"
            if incompatible
            else "not-classified-incompatible"
        ),
        "ae_free": True,
        "source_shape": shape,
        "fixture": FIXTURE,
        "rgba_f32": {
            "current_mac_screen": list(current),
            "grounded_mode1": list(mode1),
            "grounded_mode2": list(mode2),
        },
        "raw_rgba_f32_le_hex": {
            "current_mac_screen": _rgba_f32_hex(current),
            "grounded_mode1": _rgba_f32_hex(mode1),
            "grounded_mode2": _rgba_f32_hex(mode2),
        },
        "pairwise_distinct": {
            "mode1_vs_mode2": mode1 != mode2,
            "current_vs_mode1": current != mode1,
            "current_vs_mode2": current != mode2,
        },
    }


def main() -> int:
    report = audit()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["classification"].startswith("incompatible-") else 1


if __name__ == "__main__":
    raise SystemExit(main())
