import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.ae_mac_validation_contract_20260728 import (
    ContractViolation,
    SIDECAR_KIND,
    validate_evalfile_sidecar,
    validate_mac_bundle_identity,
    validate_project_contract,
    validate_raw_float32_cross_host_gates,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


def gate(mismatches=0, delta=0):
    return {
        "sample_type": "FLOAT32",
        "word_count": 16,
        "mismatched_words": mismatches,
        "max_raw_u32_delta": delta,
    }


class ProjectContractTests(unittest.TestCase):
    def test_accepts_both_raw_none_working_space_forms(self):
        for raw in ("", None):
            with self.subTest(raw=raw):
                result = validate_project_contract(
                    {
                        "bits_per_channel_raw": 32,
                        "renderer_raw": 1816,
                        "working_space_raw": raw,
                        "linear_blending": False,
                    },
                    expected_bpc=32,
                )
                self.assertIsNone(result.working_space_raw)

    def test_rejects_labels_in_numeric_readback_fields(self):
        for field, value in (
            ("bits_per_channel_raw", "32"),
            ("renderer_raw", "SOFTWARE"),
            ("renderer_raw", True),
        ):
            observed = {
                "bits_per_channel_raw": 32,
                "renderer_raw": 1816,
                "working_space_raw": "",
                "linear_blending": False,
            }
            observed[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ContractViolation):
                validate_project_contract(observed, expected_bpc=32)

    def test_rejects_display_label_for_working_space(self):
        with self.assertRaisesRegex(ContractViolation, "raw empty string or null"):
            validate_project_contract(
                {
                    "bits_per_channel_raw": 16,
                    "renderer_raw": 1816,
                    "working_space_raw": "None",
                    "linear_blending": False,
                },
                expected_bpc=16,
            )


class IdentityTests(unittest.TestCase):
    def test_bundle_identity_uses_macho_hash(self):
        with TemporaryDirectory() as temp:
            bundle = Path(temp) / "OLMBlur.plugin"
            macho = bundle / "Contents" / "MacOS" / "OLMBlur"
            macho.parent.mkdir(parents=True)
            macho.touch()
            identity = validate_mac_bundle_identity(
                {
                    "bundle_path": str(bundle),
                    "macho_path": str(macho),
                    "macho_sha256": SHA_A.upper(),
                }
            )
            self.assertEqual(identity.macho_sha256, SHA_A)
            self.assertEqual(identity.bundle_path, str(bundle.resolve()))

    def test_rejects_binary_outside_bundle(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = root / "OLMBlur.plugin"
            bundle.mkdir()
            outside = root / "Other.plugin" / "Contents" / "MacOS" / "OLMBlur"
            outside.parent.mkdir(parents=True)
            outside.touch()
            with self.assertRaisesRegex(ContractViolation, "inside"):
                validate_mac_bundle_identity(
                    {
                        "bundle_path": str(bundle),
                        "macho_path": str(outside),
                        "macho_sha256": SHA_A,
                    }
                )

    def test_rejects_nonabsolute_and_traversal_paths(self):
        with TemporaryDirectory() as temp:
            bundle = Path(temp) / "OLMBlur.plugin"
            macho = bundle / "Contents" / "MacOS" / "OLMBlur"
            macho.parent.mkdir(parents=True)
            macho.touch()
            for declared_bundle, declared_macho, message in (
                ("OLMBlur.plugin", "OLMBlur.plugin/Contents/MacOS/OLMBlur", "absolute"),
                (
                    str(bundle),
                    str(bundle / "Contents" / ".." / "MacOS" / "OLMBlur"),
                    "traversal",
                ),
            ):
                with self.subTest(message=message), self.assertRaisesRegex(
                    ContractViolation, message
                ):
                    validate_mac_bundle_identity(
                        {
                            "bundle_path": declared_bundle,
                            "macho_path": declared_macho,
                            "macho_sha256": SHA_A,
                        }
                    )

    def test_rejects_sibling_prefix_and_symlink_escape(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = root / "OLM.plugin"
            macos = bundle / "Contents" / "MacOS"
            macos.mkdir(parents=True)
            sibling = root / "OLM.plugin-copy" / "Contents" / "MacOS" / "OLM"
            sibling.parent.mkdir(parents=True)
            sibling.touch()
            outside = root / "outside-OLM"
            outside.touch()
            escaped_link = macos / "OLM"
            escaped_link.symlink_to(outside)
            for macho in (sibling, escaped_link):
                with self.subTest(macho=macho), self.assertRaisesRegex(
                    ContractViolation, "inside"
                ):
                    validate_mac_bundle_identity(
                        {
                            "bundle_path": str(bundle),
                            "macho_path": str(macho),
                            "macho_sha256": SHA_A,
                        }
                    )

    def test_evalfile_sidecar_schema_is_closed_and_versioned(self):
        sidecar = {
            "kind": SIDECAR_KIND,
            "schema_version": 1,
            "eval_file_path": "/tmp/render.jsx",
            "eval_file_sha256": SHA_A,
            "wrapper_path": "/tmp/wrapper.jsx",
            "wrapper_sha256": SHA_B,
        }
        self.assertEqual(validate_evalfile_sidecar(sidecar).eval_file_sha256, SHA_A)
        for mutation in (
            {"schema_version": "1"},
            {"schema_version": 2},
            {"unexpected": True},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(ContractViolation):
                validate_evalfile_sidecar({**sidecar, **mutation})


class RawFloat32GateTests(unittest.TestCase):
    def _observed(self, expected_noop=False):
        changed = gate(7, 42)
        return {
            "expected_noop": expected_noop,
            "control_cross_host": gate(),
            "effect_cross_host": gate(),
            "windows_effect_vs_control": gate() if expected_noop else changed,
            "mac_effect_vs_control": gate() if expected_noop else changed,
        }

    def test_accepts_exact_control_and_effect_with_real_effect(self):
        self.assertFalse(
            validate_raw_float32_cross_host_gates(self._observed()).expected_noop
        )

    def test_explicit_expected_noop_allows_valid_declared_noop(self):
        self.assertTrue(
            validate_raw_float32_cross_host_gates(self._observed(True)).expected_noop
        )

    def test_rejects_undeclared_or_false_declared_noop(self):
        with self.assertRaisesRegex(ContractViolation, "expected_noop is false"):
            validate_raw_float32_cross_host_gates(
                {**self._observed(True), "expected_noop": False}
            )
        with self.assertRaisesRegex(ContractViolation, "effect changes"):
            validate_raw_float32_cross_host_gates(
                {**self._observed(False), "expected_noop": True}
            )

    def test_rejects_failed_control_before_effect_attribution(self):
        observed = self._observed()
        observed["control_cross_host"] = gate(1, 9)
        with self.assertRaisesRegex(ContractViolation, "control"):
            validate_raw_float32_cross_host_gates(observed)

    def test_rejects_host_disagreement_about_noop(self):
        observed = self._observed(True)
        observed["mac_effect_vs_control"] = gate(2, 5)
        with self.assertRaisesRegex(ContractViolation, "hosts disagree"):
            validate_raw_float32_cross_host_gates(observed)


if __name__ == "__main__":
    unittest.main()
