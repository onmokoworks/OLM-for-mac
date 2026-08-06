#!/usr/bin/env python3
"""Regression tests for the AE-free Mac/Windows outer-compose audit."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT
    / "tools/emulation/audit_olmkirakira_mac_outer_compose_compatibility_20260730.py"
)


def load_audit():
    spec = importlib.util.spec_from_file_location("olmkirakira_mac_compose_audit", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load audit: {AUDIT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load_audit()


class MacOuterComposeCompatibilityTests(unittest.TestCase):
    def test_current_source_no_longer_contains_the_incompatible_shape(self) -> None:
        report = AUDIT.audit()
        self.assertEqual(report["classification"], "not-classified-incompatible")
        self.assertTrue(report["ae_free"])
        self.assertFalse(report["source_shape"]["screen_rgb"])
        self.assertFalse(report["source_shape"]["source_alpha_passthrough"])

    def test_unequal_alpha_fixture_separates_all_three_models(self) -> None:
        report = AUDIT.audit()
        self.assertEqual(
            report["pairwise_distinct"],
            {
                "mode1_vs_mode2": True,
                "current_vs_mode1": True,
                "current_vs_mode2": True,
            },
        )
        words = report["raw_rgba_f32_le_hex"]
        self.assertEqual(len(set(words.values())), 3)
        self.assertTrue(all(len(value) == 32 for value in words.values()))

    def test_classifier_does_not_flag_a_non_screen_shape(self) -> None:
        report = AUDIT.audit("outer_mode = merge_mode == 1; source_alpha + glow_alpha")
        self.assertEqual(report["classification"], "not-classified-incompatible")

    def test_comments_cannot_forge_the_source_shape(self) -> None:
        forged = r"""
            template <typename PixelT>
            static PF_Err RenderTyped(PF_EffectWorld *input) {
                // out.r = 1.0f - (1.0f - src.r) * (1.0f - Clamp01(glow[idx].r * glow_a));
                /* out.g = 1.0f - (1.0f - src.g) * (1.0f - Clamp01(glow[idx].g * glow_a));
                   out.b = 1.0f - (1.0f - src.b) * (1.0f - Clamp01(glow[idx].b * glow_a));
                   out.a = src_a; */
                return PF_Err_NONE;
            }
        """
        report = AUDIT.audit(forged)
        self.assertFalse(report["source_shape"]["screen_rgb"])
        self.assertFalse(report["source_shape"]["source_alpha_passthrough"])
        self.assertEqual(report["classification"], "not-classified-incompatible")

    def test_unrelated_function_cannot_forge_render_typed(self) -> None:
        forged = r"""
            static void Unrelated() {
                out.r = 1.0f - (1.0f - src.r) * (1.0f - Clamp01(glow[idx].r * glow_a));
                out.g = 1.0f - (1.0f - src.g) * (1.0f - Clamp01(glow[idx].g * glow_a));
                out.b = 1.0f - (1.0f - src.b) * (1.0f - Clamp01(glow[idx].b * glow_a));
                out.a = src_a;
            }
            template <typename PixelT>
            static PF_Err RenderTyped(PF_EffectWorld *input) {
                return PF_Err_NONE;
            }
        """
        report = AUDIT.audit(forged)
        self.assertFalse(report["source_shape"]["screen_rgb"])
        self.assertFalse(report["source_shape"]["source_alpha_passthrough"])
        self.assertEqual(report["classification"], "not-classified-incompatible")

    def test_rhs_suffix_mutation_is_rejected(self) -> None:
        source = dedent(r"""
            template <typename PixelT>
            static PF_Err RenderTyped(PF_EffectWorld *input) {
                out.r = 1.0f - (1.0f - src.r) * (1.0f - Clamp01(glow[idx].r * glow_a));
                out.g = 1.0f - (1.0f - src.g) * (1.0f - Clamp01(glow[idx].g * glow_a));
                out.b = 1.0f - (1.0f - src.b) * (1.0f - Clamp01(glow[idx].b * glow_a));
                out.a = src_a;
            }
        """)
        mutated = source.replace(
            "out.r = 1.0f - (1.0f - src.r) * (1.0f - Clamp01(glow[idx].r * glow_a));",
            "out.r = 1.0f - (1.0f - src.r) * "
            "(1.0f - Clamp01(glow[idx].r * glow_a)) + 0.01f;",
            1,
        )
        self.assertNotEqual(source, mutated)
        report = AUDIT.audit(mutated)
        self.assertFalse(report["source_shape"]["screen_rgb"])
        self.assertEqual(report["classification"], "not-classified-incompatible")

    def test_disabled_screen_branch_cannot_forge_active_helper_implementation(self) -> None:
        forged = r"""
            template <typename PixelT>
            static PF_Err RenderTyped(PF_EffectWorld *input) {
            #if 0
                out.r = 1.0f - (1.0f - src.r) * (1.0f - Clamp01(glow[idx].r * glow_a));
                out.g = 1.0f - (1.0f - src.g) * (1.0f - Clamp01(glow[idx].g * glow_a));
                out.b = 1.0f - (1.0f - src.b) * (1.0f - Clamp01(glow[idx].b * glow_a));
                out.a = src_a;
            #else
                out = ComposeWithGroundedOuterMode(src, glow[idx]);
            #endif
                return PF_Err_NONE;
            }
        """
        report = AUDIT.audit(forged)
        self.assertTrue(report["source_shape"]["render_typed_body_found"])
        self.assertFalse(report["source_shape"]["screen_rgb"])
        self.assertFalse(report["source_shape"]["source_alpha_passthrough"])
        self.assertEqual(report["classification"], "not-classified-incompatible")

    def test_if_one_active_screen_branch_is_detected(self) -> None:
        source = dedent(r"""
            template <typename PixelT>
            static PF_Err RenderTyped(PF_EffectWorld *input) {
                out.r = 1.0f - (1.0f - src.r) * (1.0f - Clamp01(glow[idx].r * glow_a));
                out.g = 1.0f - (1.0f - src.g) * (1.0f - Clamp01(glow[idx].g * glow_a));
                out.b = 1.0f - (1.0f - src.b) * (1.0f - Clamp01(glow[idx].b * glow_a));
                out.a = src_a;
            }
        """)
        start = source.index("template <typename PixelT>\nstatic PF_Err RenderTyped")
        opening = source.index("{", start)
        wrapped = source[:opening + 1] + "\n#if 1\n" + source[opening + 1:]
        end = AUDIT._render_typed_body(source)
        self.assertIsNotNone(end)
        # Insert the matching directive immediately before RenderTyped's close.
        body_start = wrapped.index("{", start)
        depth = 0
        closing = None
        for index in range(body_start, len(wrapped)):
            if wrapped[index] == "{":
                depth += 1
            elif wrapped[index] == "}":
                depth -= 1
                if depth == 0:
                    closing = index
                    break
        self.assertIsNotNone(closing)
        wrapped = wrapped[:closing] + "#endif\n" + wrapped[closing:]
        report = AUDIT.audit(wrapped)
        self.assertTrue(report["source_shape"]["screen_rgb"])
        self.assertEqual(
            report["classification"],
            "incompatible-screen-source-alpha-passthrough",
        )

    def test_unsupported_conditional_fails_closed(self) -> None:
        forged = r"""
            template <typename PixelT>
            static PF_Err RenderTyped(PF_EffectWorld *input) {
            #if ENABLE_KIRAKIRA_SCREEN
                out.r = 1.0f - (1.0f - src.r) * (1.0f - Clamp01(glow[idx].r * glow_a));
                out.g = 1.0f - (1.0f - src.g) * (1.0f - Clamp01(glow[idx].g * glow_a));
                out.b = 1.0f - (1.0f - src.b) * (1.0f - Clamp01(glow[idx].b * glow_a));
                out.a = src_a;
            #endif
            }
        """
        report = AUDIT.audit(forged)
        self.assertFalse(report["source_shape"]["render_typed_body_found"])
        self.assertEqual(report["classification"], "not-classified-incompatible")


if __name__ == "__main__":
    unittest.main()
