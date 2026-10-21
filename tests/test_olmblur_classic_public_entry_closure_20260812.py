#!/usr/bin/env python3
"""Fail-closed regression for the bounded OLMBlur classic owner closure."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "refs/conformance/olmblur_classic_public_entry_closure_20260812.json"
SOURCE = ROOT / "mac/OLMBlur/OLMBlur.cpp"
SMART = ROOT / "refs/conformance/olmblur_smart_public_admission_20260813.json"
GENERATOR = ROOT / "tools/emulation/test_olmblur_classic_public_entry_closure_20260812.py"
AEX = ROOT / "plugins_2025/OLMBlur.aex"
WORKER = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker")
WORKER_ROOT = WORKER.parents[3]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OLMBlurClassicPublicEntryClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text())

    def test_identity_is_bound_and_current_source_is_superseded_by_smart_closure(self):
        report = self.report
        self.assertEqual(report["status"], "bounded_exact_and_fail_closed")
        self.assertEqual(report["actual_aex_sha256"], sha256(AEX))
        self.assertEqual(report["aexcompat"]["worker_sha256"], sha256(WORKER))
        self.assertEqual(report["identity"]["production_source_sha256"],
                         "21f3c96acd699ed463635435ed586030d65784406d71d06333a5d0afe6618c89")
        smart = json.loads(SMART.read_text())
        self.assertEqual(smart["identities"]["source"]["sha256"], sha256(SOURCE))
        self.assertEqual(smart["status"], "PASS_HOSTLESS_BOUNDED_PUBLIC6_AND_SAFETY100")
        self.assertEqual(report["identity"]["generator_sha256"], sha256(GENERATOR))
        self.assertEqual(report["identity"]["aex_loader_sha256"], sha256(ROOT / "tools/emulation/aex_loader.py"))
        self.assertEqual(report["identity"]["decomp_sha256"], sha256(ROOT / "decomp/OLMBlur.aex.c.txt"))
        self.assertEqual(report["identity"]["disasm_sha256"], sha256(ROOT / "disasm/OLMBlur.aex.asm.txt"))
        self.assertEqual(report["aexcompat"]["pixel_transport_sha256"], sha256(WORKER_ROOT / "guest/crates/aex-guest-worker/src/pixel.rs"))
        self.assertEqual(report["aexcompat"]["classic_lifecycle_sha256"], sha256(WORKER_ROOT / "guest/crates/aex-guest-worker/src/classic.rs"))
        self.assertEqual(report["actual_export"], "0x18000a970")
        self.assertEqual(report["actual_owner"], "0x18000a180 FUN_18000a180")
        setup = report["aexcompat"]["setup"]
        self.assertEqual((setup["execution_backend"], setup["global_setup_error"], setup["params_setup_error"], setup["advertised_num_params"]),
                         ("unicorn-x86_64", 0, 0, 6))
        self.assertEqual([(row["slot"], row["param_type"], row["default_value"]) for row in setup["parameters"]],
                         [(1, 10, 5.0), (2, 2, 100.0), (3, 1, 2.0), (4, 7, 1.0), (5, 4, 0.0)])

    def test_actual_default_is_copy_only_and_bias_legacy_invariant(self):
        rows = self.report["actual_public_cases"]
        self.assertEqual(len(rows), 12)
        for depth, expected in ((8, "572932cfa1c2c26b9bb6a6feaa4b9f3966ef0855e013ce3a86b139434a737adf"),
                                (16, "bb4130a96cab14e0e5a6c186f81803ffc744608ac4dfd8d10ea9e97aaae7ce88"),
                                (32, "9322e0b08c8623a892b4e75005c863a639bf604fe5882f4a6f12f46da18ce8ae")):
            selected = [row for row in rows if row["depth"] == depth]
            self.assertEqual({(row["bias"], row["legacy"]) for row in selected}, {(1, 0), (2, 0), (1, 1), (2, 1)})
            self.assertEqual({row["active_sha256"] for row in selected}, {expected})
            for row in selected:
                self.assertEqual(row["selectors"], [5, 10, 11, 12, 8])
                self.assertEqual(row["return_code"], 0)
                self.assertEqual(row["copy_calls"], 1)
                self.assertEqual(row["active_mismatches"], 0)
                self.assertEqual(row["padding_mismatches"], 0)
                self.assertTrue(row["input_and_guards_immutable"])
                self.assertTrue(row["params_and_output_world_immutable"])

    def test_production_admission_and_rejection_are_complete(self):
        admitted = self.report["production_admitted_cases"]
        self.assertEqual(len(admitted), 8)
        self.assertEqual({row["depth"] for row in admitted}, {8, 16})
        self.assertEqual({(row["bias"], row["legacy"]) for row in admitted}, {(1, 0), (2, 0), (1, 1), (2, 1)})
        actual_sources = {row["depth"]: row["source_sha256"] for row in self.report["actual_public_cases"]}
        for row in admitted:
            self.assertEqual(row["err"], 0)
            self.assertEqual(row["active_mismatches"], 0)
            self.assertEqual(row["padding_mismatches"], 0)
            self.assertTrue(row["input_immutable"])
            self.assertEqual(row["source_sha256"], actual_sources[row["depth"]])
        rejected = self.report["production_rejected_cases"]
        self.assertEqual(len(rejected), 22)
        self.assertEqual({row["mutation"] for row in rejected if row["depth"] == 8 and row["amount"] == 5 and row["smoothness"] == 100 and row["repeat"] == 2},
                         set(range(1, 19)))
        self.assertEqual(self.report["production_rejection_mutations"], {
            "1": "output width 23", "2": "output height 23", "3": "output rowbytes minus one",
            "4": "input width 23", "5": "input height 23", "6": "input rowbytes minus one",
            "7": "null input data", "8": "null output data", "9": "input PF8/output PF16 format mismatch",
            "10": "both widths 23", "11": "both heights 23", "12": "both rowbytes minus one",
            "13": "null params array", "14": "null output world", "15": "null input slot",
            "16": "null amount slot", "17": "null smoothness slot", "18": "null repeat slot",
        })
        self.assertEqual({(row["depth"], row["amount"], row["smoothness"], row["repeat"], row["mutation"]) for row in rejected if row["mutation"] == 0},
                         {(32, 5, 100, 2, 0), (8, 6, 100, 2, 0), (8, 5, 99, 2, 0), (8, 5, 100, 1, 0)})
        for row in rejected:
            self.assertEqual(row["err"], -1)
            self.assertEqual(row["untouched_mismatches"], 0)
            self.assertTrue(row["input_immutable"])
        self.assertEqual(self.report["actual_raw_exact_copy"], 12)
        self.assertEqual(self.report["production_admitted_exact"], 8)
        self.assertEqual(self.report["production_rejected_fail_closed"], 22)
        self.assertEqual(self.report["decision"], {
            "pf8_pf16_default": "copy-only exact for Bias 1/2 and Legacy 0/1",
            "bias_legacy": "ignored at classic owner; production no longer consumes them",
            "pf32": "fail closed because the actual classic owner cannot distinguish PF32 from PF16",
            "other_amount_smoothness_repeat": "fail closed; no generalized malformed classic parameter ABI claim",
            "layout": "only equal non-null 24x24 input/output with depth-specific admitted padded rowbytes",
            "numerical_owner": "advertised SmartPreRender/SmartRender remains unchanged",
        })
        self.assertIn("does not claim worker/native-AE classic pixel execution", self.report["boundary"])

    def test_source_does_not_consume_unowned_classic_fields(self):
        source = SOURCE.read_text()
        start = source.index("Render(PF_InData")
        end = source.index("SmartPreRender(PF_InData", start)
        body = source[start:end]
        self.assertNotRegex(body, re.compile(r"OLMBLUR_(BIAS_DIRECTION|LEGACY).*->u"))
        self.assertIn("case PF_PixelFormat_ARGB128:", body)
        self.assertIn("PF_GetPixelFormat(output, &output_format)", body)
        self.assertIn("input_format != output_format", body)
        self.assertIn("input->width != output->width", body)
        self.assertIn("input->rowbytes != output->rowbytes", body)
        self.assertIn("input->width != 24", body)
        self.assertIn("input->rowbytes != expected_rowbytes", body)
        self.assertIn("!params || !output || !params[OLMBLUR_INPUT]", body)
        self.assertIn("!params[OLMBLUR_BLUR_AMOUNT] || !params[OLMBLUR_BLUR_SMOOTHNESS]", body)
        self.assertIn("!params[OLMBLUR_REPEAT]", body)
        self.assertIn("return PF_Err_BAD_CALLBACK_PARAM;", body)
        self.assertIn("blur_amount != 5.0", body)
        self.assertIn("blur_smoothness != 100 * 65536", body)
        self.assertIn("repeat != 2", body)
        self.assertIn("ERR(PF_COPY(input, output, NULL, NULL));", body)
        self.assertNotIn("BlurRender(in_data, input, output", body)


if __name__ == "__main__":
    unittest.main()
