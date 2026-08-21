from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import itertools
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "tools/emulation/test_olmkirakira_mode3_ui_windows_owner_20260821.py"
)
REPORT = (
    ROOT
    / "refs/conformance/olmkirakira_mode3_ui_windows_owner_20260821.json"
)
REPORT_PIN = REPORT.with_suffix(".sha256")

# A semantic cell digest alone cannot detect a coordinated rewrite of all three
# owner hashes. The independent sidecar and this consumer therefore pin the
# complete canonical report; the raw-file pin additionally fixes its unique
# accepted presentation bytes.
EXPECTED_REPORT_FILE_SHA256 = (
    "c5acfb8c6ae03f637b21f8ac0355b8071f47d3e60caba94b1f06230f232cfac7"
)
EXPECTED_REPORT_CANONICAL_SHA256 = (
    "50bbf05233f985608e4e320473970e734987d60ffd9e1d859c63bd10b1d8f687"
)
EXPECTED_CELLS_SHA256 = (
    "865d282fa3e15d55b5155e1a406e629e39f14205256a1d5c4e06f5d76709bbd0"
)
EXPECTED_INPUT_SHA256 = {
    "rgba8": "7934392d34781b2330e4f1b451f47773d93e2f281851bd4546717ba2252068ec",
    "argb8": "3c024f8074f08c5152ba54c1b79e275eae2c5c2a2b4572a4497303cec836afd0",
    "argb16le": "b85a7304ea38b0ae22b142a3a95421a58ac3e1ff179ac53805b47a918a1f5ffb",
    "argb32fle": "2c8d46d068ef23fe313f151a4b6f4726cffbae6c98a66a5b331096e0eb849556",
}
EXPECTED_INPUT_BYTES = {
    "rgba8": 17 * 11 * 4,
    "argb8": 17 * 11 * 4,
    "argb16le": 17 * 11 * 8,
    "argb32fle": 17 * 11 * 16,
}
EXPECTED_CELLS = list(
    itertools.product((1, 2, 50, 300), (0, 1), ("PF8", "PF16", "PF32"))
)


def load_script():
    spec = importlib.util.spec_from_file_location(
        "olmkirakira_mode3_ui_windows_owner", SCRIPT
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fixture_planes() -> dict[str, bytes]:
    """Independently reproduce the C++ harness's 17x11 source planes."""
    rgba8 = bytearray()
    argb8 = bytearray()
    argb16le = bytearray()
    argb32fle = bytearray()
    for y in range(11):
        for x in range(17):
            value = (
                ((x * 0x9E3779B9) & 0xFFFFFFFF)
                ^ ((y * 0x85EBCA6B) & 0xFFFFFFFF)
                ^ 0x51F15E5D
            )
            alpha = 0 if value == 0x51F15E5D else 32 + ((value >> 24) & 223)
            red = value & 255
            green = (value >> 8) & 255
            blue = (value >> 16) & 255
            rgba8.extend((red, green, blue, alpha))
            argb8.extend((alpha, red, green, blue))

            def to_pf16(component: int) -> int:
                # Equivalent to lround(component * 32768.0 / 255.0) for the
                # non-negative 8-bit domain (255 is odd, so there are no ties).
                return (component * 32768 + 127) // 255

            argb16le.extend(
                struct.pack(
                    "<4H",
                    to_pf16(alpha),
                    to_pf16(red),
                    to_pf16(green),
                    to_pf16(blue),
                )
            )
            argb32fle.extend(
                struct.pack(
                    "<4f",
                    alpha / 255.0,
                    red / 255.0,
                    green / 255.0,
                    blue / 255.0,
                )
            )
    return {
        "rgba8": bytes(rgba8),
        "argb8": bytes(argb8),
        "argb16le": bytes(argb16le),
        "argb32fle": bytes(argb32fle),
    }


class KiraMode3UiWindowsOwnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_script()
        cls.report_bytes = REPORT.read_bytes()
        cls.report = json.loads(cls.report_bytes)

    def stored_repository_source(self) -> list[dict]:
        return copy.deepcopy(
            self.report["identities"]["repository_source"]
        )

    def rewrite_route_hashes(self, *, all_cells: bool) -> dict:
        changed = copy.deepcopy(self.report)
        cells = changed["cells"] if all_cells else changed["cells"][:1]
        for cell in cells:
            for field in (
                "windows_exported_smart_sha256",
                "mac_public_smart_sha256",
                "mac_public_classic_sha256",
            ):
                cell[field] = "0" * 64
        changed["cells_sha256"] = self.module.canonical_sha256(
            changed["cells"]
        )
        return changed

    def type_confusion_mutations(self):
        return (
            ("fixture width int-to-float",
             lambda value: value["fixture"].__setitem__("width", 17.0),
             False),
            ("fixture count int-to-bool",
             lambda value: value["fixture"]["counts"].__setitem__(
                 "zero_alpha_nonzero_rgb_pixels", True
             ), False),
            ("parameter int-to-float",
             lambda value: value["parameters"].__setitem__(
                 "blur_mode", 3.0
             ), False),
            ("AEX size int-to-float",
             lambda value: value["identities"]["windows_aex"].__setitem__(
                 "size_bytes", float(self.module.AEX_EXPECTED_SIZE)
             ), False),
            ("worker size int-to-float",
             lambda value: value["identities"]["aex_guest_worker"].__setitem__(
                 "size_bytes", float(self.module.EXPECTED_WORKER_SIZE)
             ), False),
            ("worker build size int-to-float",
             lambda value: value["identities"]["aexcompat"][
                 "worker_build"
             ].__setitem__(
                 "target_size_bytes", float(self.module.EXPECTED_WORKER_SIZE)
             ), False),
            ("official member size int-to-float",
             lambda value: value["identities"][
                 "official_distribution"
             ].__setitem__(
                 "archive_member_size_bytes",
                 float(self.module.AEX_EXPECTED_SIZE),
             ), False),
            ("lifecycle schema int-to-bool",
             lambda value: value["cells"][0]["windows_lifecycle"].__setitem__(
                 "worker_schema_version", True
             ), True),
            ("summary int-to-float",
             lambda value: value["summary"].__setitem__(
                 "cell_count", 24.0
             ), False),
        )

    def verify(
        self,
        report: dict,
        *,
        expected_report_sha256: str | None = None,
        external_aex: Path | None = None,
        external_worker: Path | None = None,
        aexcompat_source: Path | None = None,
    ) -> bool:
        return bool(
            self.module.verify_report(
                report,
                expected_report_sha256=expected_report_sha256,
                external_aex=external_aex,
                external_worker=external_worker,
                aexcompat_source=aexcompat_source,
            )
        )

    def reject(self, mutate, *, recanonicalize: bool = False) -> None:
        changed = copy.deepcopy(self.report)
        mutate(changed)
        if recanonicalize:
            changed["cells_sha256"] = self.module.canonical_sha256(
                changed["cells"]
            )
        self.assertFalse(self.verify(changed))

    def test_tracked_report_is_semantically_valid_and_whole_file_pinned(self) -> None:
        self.assertRegex(EXPECTED_REPORT_FILE_SHA256, r"^[0-9a-f]{64}$")
        self.assertRegex(EXPECTED_REPORT_CANONICAL_SHA256, r"^[0-9a-f]{64}$")
        self.assertRegex(EXPECTED_CELLS_SHA256, r"^[0-9a-f]{64}$")
        self.assertEqual(
            sha256_bytes(self.report_bytes), EXPECTED_REPORT_FILE_SHA256
        )
        self.assertEqual(
            self.report_bytes,
            self.module._report_bytes(self.report),
            "the tracked report must use the sole accepted presentation bytes",
        )
        self.assertEqual(
            self.module.canonical_sha256(self.report),
            EXPECTED_REPORT_CANONICAL_SHA256,
        )
        self.assertEqual(
            REPORT_PIN.read_bytes(),
            (EXPECTED_REPORT_CANONICAL_SHA256 + "\n").encode("ascii"),
        )
        self.assertEqual(
            self.module._read_default_report_pin(),
            EXPECTED_REPORT_CANONICAL_SHA256,
        )
        self.assertEqual(self.report["cells_sha256"], EXPECTED_CELLS_SHA256)
        self.assertTrue(self.verify(self.report))
        self.assertTrue(
            self.verify(
                self.report,
                expected_report_sha256=EXPECTED_REPORT_CANONICAL_SHA256,
            )
        )
        self.assertFalse(
            self.verify(self.report, expected_report_sha256="0" * 64)
        )

        changed = self.rewrite_route_hashes(all_cells=False)
        self.assertFalse(
            self.verify(
                changed,
                expected_report_sha256=EXPECTED_REPORT_CANONICAL_SHA256,
            )
        )

    def test_default_pin_rejects_coordinated_route_and_type_rewrites(self) -> None:
        # Freeze source identity to the report under test so these assertions
        # isolate the independent whole-report pin even before/after recapture.
        with mock.patch.object(
            self.module,
            "repository_source_records",
            return_value=self.stored_repository_source(),
        ):
            self.assertTrue(self.verify(self.report))
            self.assertFalse(
                self.verify(self.rewrite_route_hashes(all_cells=False))
            )
            self.assertFalse(
                self.verify(self.rewrite_route_hashes(all_cells=True))
            )

            for label, mutate, recanonicalize in self.type_confusion_mutations():
                with self.subTest(label=label):
                    changed = copy.deepcopy(self.report)
                    mutate(changed)
                    if recanonicalize:
                        changed["cells_sha256"] = self.module.canonical_sha256(
                            changed["cells"]
                        )
                    self.assertFalse(self.verify(changed))

    def test_explicit_self_digest_cannot_bypass_strict_json_types(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kira_windows_owner_types_") as raw, \
                mock.patch.object(
                    self.module,
                    "repository_source_records",
                    return_value=self.stored_repository_source(),
                ):
            directory = Path(raw)
            for index, (label, mutate, recanonicalize) in enumerate(
                self.type_confusion_mutations()
            ):
                with self.subTest(label=label):
                    changed = copy.deepcopy(self.report)
                    mutate(changed)
                    if recanonicalize:
                        changed["cells_sha256"] = self.module.canonical_sha256(
                            changed["cells"]
                        )
                    self_digest = self.module.canonical_sha256(changed)
                    self.assertFalse(
                        self.verify(
                            changed,
                            expected_report_sha256=self_digest,
                        )
                    )

                    alternate = directory / f"type-confusion-{index}.json"
                    alternate.write_bytes(self.module._report_bytes(changed))
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(stdout), \
                            contextlib.redirect_stderr(stderr):
                        result = self.module.main([
                            "--report", str(alternate),
                            "--expected-report-sha256", self_digest,
                        ])
                    self.assertNotEqual(
                        result, 0, stdout.getvalue() + stderr.getvalue()
                    )
                    self.assertIn("type mismatch", stderr.getvalue())

    def test_report_reader_rejects_unbounded_or_nonregular_inputs_quickly(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kira_windows_owner_reader_") as raw:
            directory = Path(raw)
            regular = directory / "regular.json"
            regular.write_bytes(self.report_bytes)
            self.assertEqual(
                self.module._read_report_bytes(regular), self.report_bytes
            )

            oversized = directory / "oversized.json"
            oversized.write_bytes(b"x" * (self.module.MAX_REPORT_BYTES + 1))
            fifo = directory / "report.fifo"
            os.mkfifo(fifo)
            report_symlink = directory / "report-symlink.json"
            report_symlink.symlink_to(regular)
            report_directory = directory / "report-directory"
            report_directory.mkdir()

            cases = [
                ("oversized", oversized, "exceeds"),
                ("fifo", fifo, "not a regular file"),
                ("symlink", report_symlink, "is a symlink"),
                ("directory", report_directory, "not a regular file"),
            ]
            if Path("/dev/zero").exists():
                cases.append(("device", Path("/dev/zero"), "not a regular file"))
            for label, path, expected_error in cases:
                with self.subTest(label=label):
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(SCRIPT),
                            "--report", str(path),
                            "--expected-report-sha256",
                            EXPECTED_REPORT_CANONICAL_SHA256,
                        ],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        timeout=3,
                    )
                    self.assertNotEqual(
                        result.returncode, 0, result.stdout + result.stderr
                    )
                    self.assertIn(expected_error, result.stderr)

    def test_default_pin_is_strict_and_explicit_alternate_pin_bypasses_it(self) -> None:
        expected_line = (EXPECTED_REPORT_CANONICAL_SHA256 + "\n").encode("ascii")
        with tempfile.TemporaryDirectory(prefix="kira_windows_owner_pin_") as raw:
            directory = Path(raw)
            good = directory / "good.sha256"
            good.write_bytes(expected_line)
            self.assertEqual(
                self.module._read_default_report_pin(good),
                EXPECTED_REPORT_CANONICAL_SHA256,
            )

            malformed = (
                b"",
                expected_line[:-1],
                expected_line + b"\n",
                EXPECTED_REPORT_CANONICAL_SHA256.upper().encode("ascii") + b"\n",
                ("0" * 64 + "\r\n").encode("ascii"),
                b"g" * 64 + b"\n",
            )
            for index, payload in enumerate(malformed):
                with self.subTest(index=index, payload=payload):
                    bad = directory / f"bad-{index}.sha256"
                    bad.write_bytes(payload)
                    with self.assertRaises(self.module.VerificationFailure):
                        self.module._read_default_report_pin(bad)

            target = directory / "target.sha256"
            target.write_bytes(expected_line)
            symlink = directory / "symlink.sha256"
            symlink.symlink_to(target)
            with self.assertRaises(self.module.VerificationFailure):
                self.module._read_default_report_pin(symlink)

            missing = directory / "missing.sha256"
            with mock.patch.object(self.module, "DEFAULT_REPORT_PIN", missing), \
                    mock.patch.object(
                        self.module,
                        "repository_source_records",
                        return_value=self.stored_repository_source(),
                    ):
                self.assertFalse(self.verify(self.report))
                self.assertTrue(
                    self.verify(
                        self.report,
                        expected_report_sha256=EXPECTED_REPORT_CANONICAL_SHA256,
                    )
                )
                # capture_report uses this private semantic verifier and must
                # remain able to validate a newly generated, not-yet-pinned report.
                self.module._verify_report_or_raise(self.report)

    def test_cli_default_pin_alternate_workflow_and_unique_presentation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kira_windows_owner_alt_report_") as raw:
            directory = Path(raw)
            alternate = directory / "alternate.json"
            alternate.write_bytes(self.report_bytes)
            missing_pin = directory / "missing.sha256"

            with mock.patch.object(
                self.module,
                "repository_source_records",
                return_value=self.stored_repository_source(),
            ), mock.patch.object(self.module, "DEFAULT_REPORT_PIN", missing_pin):
                stdout, stderr = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    result = self.module.main([
                        "--report", str(alternate),
                        "--expected-report-sha256",
                        EXPECTED_REPORT_CANONICAL_SHA256,
                    ])
                self.assertEqual(result, 0, stdout.getvalue() + stderr.getvalue())

                stdout, stderr = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    result = self.module.main(["--report", str(alternate)])
                self.assertNotEqual(result, 0)
                self.assertIn("alternate --report requires", stderr.getvalue())

                noncanonical = directory / "noncanonical.json"
                noncanonical.write_bytes(
                    json.dumps(
                        self.report,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                        allow_nan=False,
                    ).encode("utf-8")
                )
                self.assertNotEqual(noncanonical.read_bytes(), self.report_bytes)
                stdout, stderr = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    result = self.module.main([
                        "--report", str(noncanonical),
                        "--expected-report-sha256",
                        EXPECTED_REPORT_CANONICAL_SHA256,
                    ])
                self.assertNotEqual(result, 0)
                self.assertIn("canonical presentation form", stderr.getvalue())

            pin = directory / "tracked.sha256"
            pin.write_bytes(
                (EXPECTED_REPORT_CANONICAL_SHA256 + "\n").encode("ascii")
            )
            for label, changed in (
                ("one-cell", self.rewrite_route_hashes(all_cells=False)),
                ("all-24-cells", self.rewrite_route_hashes(all_cells=True)),
            ):
                with self.subTest(label=label):
                    default_report = directory / f"{label}.json"
                    default_report.write_bytes(self.module._report_bytes(changed))
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with mock.patch.object(
                        self.module, "DEFAULT_REPORT", default_report
                    ), mock.patch.object(
                        self.module, "DEFAULT_REPORT_PIN", pin
                    ), mock.patch.object(
                        self.module,
                        "repository_source_records",
                        return_value=self.stored_repository_source(),
                    ):
                        with contextlib.redirect_stdout(stdout), \
                                contextlib.redirect_stderr(stderr):
                            result = self.module.main([])
                        self.assertNotEqual(result, 0)
                        self.assertIn(
                            "canonical whole-report SHA-256 mismatch",
                            stderr.getvalue(),
                        )

                        # Even an explicit digest for the rewritten default
                        # report cannot override the independent tracked pin.
                        stdout, stderr = io.StringIO(), io.StringIO()
                        with contextlib.redirect_stdout(stdout), \
                                contextlib.redirect_stderr(stderr):
                            result = self.module.main([
                                "--expected-report-sha256",
                                self.module.canonical_sha256(changed),
                            ])
                        self.assertNotEqual(result, 0)
                        self.assertIn(
                            "disagrees with tracked sidecar",
                            stderr.getvalue(),
                        )

    def test_schema_is_strict_at_top_nested_and_cell_levels(self) -> None:
        self.reject(lambda value: value.__setitem__("unexpected", True))
        self.reject(lambda value: value.pop("summary"))
        self.reject(
            lambda value: value["fixture"].__setitem__("unexpected", True)
        )
        self.reject(lambda value: value["identities"].popitem())
        self.reject(
            lambda value: value["cells"][0].__setitem__("unexpected", True),
            recanonicalize=True,
        )
        self.reject(
            lambda value: value["cells"][0].pop("windows_lifecycle"),
            recanonicalize=True,
        )
        self.reject(
            lambda value: value["cells"][0]["windows_lifecycle"].__setitem__(
                "unexpected", True
            ),
            recanonicalize=True,
        )

    def test_cells_are_the_exact_ordered_24_cell_cartesian_product(self) -> None:
        actual = [
            (
                cell["length"],
                cell["rotation_raw_fixed"],
                cell["depth"],
            )
            for cell in self.report["cells"]
        ]
        self.assertEqual(actual, EXPECTED_CELLS)
        self.assertEqual(len(actual), len(set(actual)))

        def duplicate(value: dict) -> None:
            first = value["cells"][0]
            second = value["cells"][1]
            for key in ("length", "rotation_raw_fixed", "depth"):
                second[key] = first[key]

        self.reject(duplicate, recanonicalize=True)
        self.reject(lambda value: value["cells"].reverse(), recanonicalize=True)

    def test_route_hash_mismatch_is_rejected_after_recanonicalization(self) -> None:
        self.reject(
            lambda value: value["cells"][0].__setitem__(
                "windows_exported_smart_sha256", "0" * 64
            ),
            recanonicalize=True,
        )
        self.reject(
            lambda value: value["cells"][1].__setitem__(
                "routes_exact", False
            ),
            recanonicalize=True,
        )

    def test_input_planes_are_recomputed_not_trusted_from_the_report(self) -> None:
        planes = fixture_planes()
        actual_hashes = {
            name: sha256_bytes(payload) for name, payload in planes.items()
        }
        actual_counts = {name: len(payload) for name, payload in planes.items()}
        self.assertEqual(actual_hashes, EXPECTED_INPUT_SHA256)
        self.assertEqual(actual_counts, EXPECTED_INPUT_BYTES)
        self.assertEqual(
            self.report["fixture"]["input_sha256"], EXPECTED_INPUT_SHA256
        )
        self.assertEqual(
            self.report["fixture"]["input_active_bytes"], EXPECTED_INPUT_BYTES
        )
        self.assertEqual(planes["rgba8"][:4], bytes((0x5D, 0x5E, 0xF1, 0)))
        self.assertEqual(
            self.report["fixture"]["counts"]["zero_alpha_nonzero_rgb_pixels"],
            1,
        )
        depth_input = {
            "PF8": "argb8",
            "PF16": "argb16le",
            "PF32": "argb32fle",
        }
        for cell in self.report["cells"]:
            plane = depth_input[cell["depth"]]
            self.assertEqual(cell["active_bytes"], EXPECTED_INPUT_BYTES[plane])
            self.assertEqual(cell["input_sha256"], EXPECTED_INPUT_SHA256[plane])

        self.reject(
            lambda value: value["fixture"]["input_sha256"].__setitem__(
                "rgba8", "0" * 64
            )
        )
        self.reject(
            lambda value: value["cells"][0].__setitem__(
                "input_sha256", "0" * 64
            ),
            recanonicalize=True,
        )

    def test_current_mac_source_closure_is_bound_and_drift_is_rejected(self) -> None:
        self.assertEqual(
            self.report["identities"]["repository_source"],
            self.module.repository_source_records(),
        )

        def drift(value: dict) -> None:
            value["identities"]["repository_source"][0]["sha256"] = "0" * 64

        self.reject(drift)

    def test_official_distribution_cross_binds_zip_member_and_executed_aex(self) -> None:
        identities = self.report["identities"]
        distribution = identities["official_distribution"]
        self.assertEqual(
            distribution["archive_member_sha256"],
            identities["windows_aex"]["sha256"],
        )
        self.assertEqual(
            distribution["archive_member_size_bytes"],
            identities["windows_aex"]["size_bytes"],
        )
        self.assertEqual(distribution["zip_sha256"], self.module.OFFICIAL_ZIP_SHA256)
        self.assertEqual(
            distribution["archive_member"],
            "OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex",
        )
        self.reject(
            lambda value: value["identities"]["official_distribution"].__setitem__(
                "archive_member_sha256", "0" * 64
            )
        )
        self.reject(
            lambda value: value["identities"]["official_distribution"].__setitem__(
                "zip_sha256", "0" * 64
            )
        )

    def test_worker_build_cross_binds_pinned_source_and_captured_target(self) -> None:
        identities = self.report["identities"]
        worker = identities["aex_guest_worker"]
        compat = identities["aexcompat"]
        build = compat["worker_build"]
        self.assertTrue(compat["tracked_worktree_clean"])
        self.assertTrue(build["completed"])
        self.assertEqual(build["command"], list(self.module.AEXCOMPAT_BUILD_COMMAND))
        self.assertEqual(build["target"], self.module.AEXCOMPAT_WORKER_TARGET)
        self.assertEqual(build["target_sha256"], worker["sha256"])
        self.assertEqual(build["target_size_bytes"], worker["size_bytes"])
        self.assertEqual(worker["sha256"], self.module.EXPECTED_WORKER_SHA256)
        self.assertTrue(
            self.report["scope"]["worker_built_from_pinned_aexcompat_source"]
        )

        self.reject(
            lambda value: value["identities"]["aexcompat"]["worker_build"].__setitem__(
                "target_sha256", "0" * 64
            )
        )
        self.reject(
            lambda value: value["identities"]["aexcompat"]["source_files"][0].__setitem__(
                "sha256", "0" * 64
            )
        )

        def coordinated_worker_rewrite(value: dict) -> None:
            value["identities"]["aex_guest_worker"]["sha256"] = "0" * 64
            value["identities"]["aexcompat"]["worker_build"][
                "target_sha256"
            ] = "0" * 64

        self.reject(coordinated_worker_rewrite)

        with tempfile.TemporaryDirectory(prefix="kira_wrong_worker_target_") as raw:
            source = Path(raw)
            wrong_worker = source / "different-worker"
            wrong_worker.write_bytes(b"not the exact Cargo target")
            with self.assertRaises(self.module.VerificationFailure):
                self.module._worker_build_identity(source, wrong_worker)

    def test_cell_canonical_digest_is_recomputed(self) -> None:
        self.assertEqual(
            self.report["cells_sha256"],
            self.module.canonical_sha256(self.report["cells"]),
        )
        self.assertEqual(self.report["cells_sha256"], EXPECTED_CELLS_SHA256)
        self.reject(lambda value: value.__setitem__("cells_sha256", "0" * 64))

    def test_claim_scope_cannot_be_promoted_beyond_hostless_owner_evidence(self) -> None:
        self.assertEqual(self.report["claim_boundary"], self.module.CLAIM_BOUNDARY)
        self.assertEqual(self.report["scope"], self.module.SCOPE)
        for field in (
            "native_windows_after_effects",
            "native_macos_after_effects",
            "installed_plugin",
            "native_windows_ucrt_or_trigonometry",
            "gpu",
        ):
            self.assertFalse(self.report["scope"][field])
            self.reject(
                lambda value, field=field: value["scope"].__setitem__(
                    field, True
                )
            )

    def test_optional_external_artifacts_are_hash_checked_when_supplied(self) -> None:
        self.assertTrue(self.verify(self.report))
        with tempfile.TemporaryDirectory(prefix="kira_windows_owner_bad_external_") as raw:
            directory = Path(raw)
            bad_aex = directory / "OLMKiraKira.aex"
            bad_worker = directory / "aex-guest-worker"
            bad_source = directory / "AEXCompat"
            bad_aex.write_bytes(b"not the captured AEX")
            bad_worker.write_bytes(b"not the captured worker")
            bad_source.mkdir()
            self.assertFalse(self.verify(self.report, external_aex=bad_aex))
            self.assertFalse(self.verify(self.report, external_worker=bad_worker))
            self.assertFalse(
                self.verify(self.report, aexcompat_source=bad_source)
            )
            self.assertFalse(
                self.verify(
                    self.report,
                    external_aex=directory / "missing.aex",
                )
            )

    def test_default_cli_is_read_only_and_capture_cli_fails_closed(self) -> None:
        before = REPORT.read_bytes()
        verified = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.assertEqual(REPORT.read_bytes(), before)

        with tempfile.TemporaryDirectory(prefix="kira_windows_owner_cli_") as raw:
            directory = Path(raw)
            missing_aex = directory / "missing.aex"
            missing_worker = directory / "missing-worker"
            missing_source = directory / "missing-source"
            cases = (
                ["--capture"],
                ["--write-report"],
                ["--aex", str(missing_aex)],
                [
                    "--capture",
                    "--aex",
                    str(missing_aex),
                    "--worker",
                    str(missing_worker),
                    "--aexcompat-source",
                    str(missing_source),
                    "--write-report",
                    str(directory / "must-not-be-written.json"),
                ],
            )
            for arguments in cases:
                with self.subTest(arguments=arguments):
                    result = subprocess.run(
                        [sys.executable, str(SCRIPT), *arguments],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        timeout=30,
                    )
                    self.assertNotEqual(
                        result.returncode,
                        0,
                        result.stdout + result.stderr,
                    )
                    self.assertEqual(REPORT.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
