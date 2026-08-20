import argparse
import hashlib
import importlib.util
import json
import os
import tempfile
import time
import unittest
import zlib
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ae_batch_runner", ROOT / "scripts/run_ae_validation_batch.py"
)
assert SPEC and SPEC.loader
batch_runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(batch_runner)


def png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(payload, zlib.crc32(chunk_type)) & 0xFFFFFFFF
    return (
        len(payload).to_bytes(4, "big")
        + chunk_type
        + payload
        + crc.to_bytes(4, "big")
    )


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_IHDR = png_chunk(
    b"IHDR", b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
)
PNG_IDAT = png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\xff"))
PNG_IEND = png_chunk(b"IEND", b"")
VALID_PNG = PNG_SIGNATURE + PNG_IHDR + PNG_IDAT + PNG_IEND
ALTERNATE_VALID_PNG = (
    PNG_SIGNATURE
    + PNG_IHDR
    + png_chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00\xff"))
    + PNG_IEND
)


def bad_idat_crc_with_valid_signature_and_iend() -> bytes:
    payload = bytearray(VALID_PNG)
    idat_crc_offset = len(PNG_SIGNATURE) + len(PNG_IHDR) + len(PNG_IDAT) - 1
    payload[idat_crc_offset] ^= 1
    return bytes(payload)


class AeBatchPngIntegrityTests(unittest.TestCase):
    def batch(self, output_dir: Path, candidates: list[str]) -> dict[str, object]:
        return {
            "kind": "olm_ae_pixel_validation_batch_render_result",
            "schema_version": 2,
            "hostless_validation_required": True,
            "requests": [
                {
                    "kind": "olm_ae_pixel_validation_render_result",
                    "schema_version": 2,
                    "hostless_validation_required": True,
                    "request_id": "request_1",
                    "output_dir": str(output_dir),
                    "rendered": [],
                    "render_candidates": candidates,
                    "png_observations": {
                        "case_1": {
                            "status": "stable",
                            "format_complete": True,
                            "crc_validated": False,
                        }
                    },
                    "warnings": [],
                    "errors": [],
                }
            ],
        }

    def validate(self, result: dict[str, object], results_base: Path) -> bool:
        return batch_runner.validate_batch_outputs(
            result,
            not_before_ns=time.time_ns() - 1_000_000_000,
            expected_request_ids=["request_1"],
            expected_results_base=results_base,
            timeout_seconds=0.2,
            stable_window_seconds=0.02,
            poll_interval_seconds=0.005,
        )

    def test_jsx_only_emits_candidates_for_python_promotion(self):
        source = (ROOT / "scripts/ae_pixel_validation_render.jsx").read_text(encoding="utf-8")
        self.assertIn("summary.render_candidates.push(caseSpec.frame);", source)
        self.assertNotIn("summary.rendered.push(caseSpec.frame);", source)
        self.assertIn('"  \\"rendered\\": " + jsonStringArray(summary.rendered)', source)
        self.assertIn('"  \\"render_candidates\\": " + jsonStringArray(summary.render_candidates)', source)
        self.assertIn('"  \\"schema_version\\": 2', source)
        self.assertIn('"  \\"hostless_validation_required\\": true', source)
        self.assertIn('run_id: getenv("OLM_AE_RUN_ID") || ""', source)
        self.assertIn("if (png.alias)", source)
        self.assertIn("if (resultRoot.alias)", source)

    def test_jsx_parameter_depth_failures_are_not_render_candidates(self):
        source = (ROOT / "scripts/ae_pixel_validation_render.jsx").read_text(encoding="utf-8")
        parameter_error = source.index("parameter assignment failed")
        candidate = source.index("summary.render_candidates.push(caseSpec.frame);")
        self.assertLess(parameter_error, candidate)
        self.assertIn('throw new Error("bits_per_channel setup failed:', source)
        self.assertIn("Number(app.project.bitsPerChannel) !== requestedBits", source)

    def test_batch_and_single_case_share_lock_and_batch_run_dir_is_unique(self):
        source = (ROOT / "scripts/run_ae_validation_batch.py").read_text(encoding="utf-8")
        self.assertIn('default=Path("/tmp/olm_ae_single_case.lock")', source)
        self.assertIn("with ae_lock(args.lock_path.resolve()):", source)
        self.assertIn("%Y%m%d_%H%M%S_%f", source)
        self.assertIn("os.getpid()", source)
        self.assertIn("run_dir.mkdir(parents=False, exist_ok=False)", source)
        lock_index = source.index("with ae_lock(args.lock_path.resolve()):")
        run_index = source.index("return run_main_under_lock(args)", lock_index)
        self.assertLess(lock_index, run_index)
        stale_index = source.index("if raw_batch_result_json.exists():")
        unlink_index = source.index("raw_batch_result_json.unlink()", stale_index)
        host_index = source.index("host_started_ns = time.time_ns()", unlink_index)
        self.assertLess(stale_index, unlink_index)
        self.assertLess(unlink_index, host_index)

    def test_existing_generation_directory_is_never_reused(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            base = root / "base"
            run_parent = root / "runs"
            run_id = "20260821_010203_000004_1234_0011223344556677"
            existing = run_parent / f"batch_run_{run_id}"
            existing.mkdir(parents=True)
            sentinel = existing / "owner.txt"
            sentinel.write_text("first generation\n", encoding="utf-8")
            args = argparse.Namespace(
                base_dir=base,
                requests_base=base / "requests",
                results_base=run_parent,
                lock_path=root / "ae.lock",
            )
            fake_datetime = mock.Mock()
            fake_datetime.now.return_value.strftime.return_value = "20260821_010203_000004"

            with mock.patch.object(batch_runner, "parse_args", return_value=args), mock.patch.object(
                batch_runner, "datetime", fake_datetime
            ), mock.patch.object(batch_runner.os, "getpid", return_value=1234), mock.patch.object(
                batch_runner.secrets, "token_hex", return_value="0011223344556677"
            ), mock.patch.object(batch_runner, "selected_request_ids") as select_requests:
                self.assertEqual(batch_runner.main(), 1)

            select_requests.assert_not_called()
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "first generation\n")

    def test_default_request_ids_preserve_base_request_ids_file_precedence(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            (base / "REQUEST_IDS.txt").write_text("configured_request\n", encoding="utf-8")
            args = argparse.Namespace(request_id=[], request_ids_file=None)
            self.assertEqual(
                batch_runner.selected_request_ids(args, base),
                ["configured_request"],
            )

    def test_explicit_empty_request_ids_file_never_falls_back_to_base(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            (base / "REQUEST_IDS.txt").write_text("base_request\n", encoding="utf-8")
            explicit = base / "explicit.txt"
            explicit.write_text("\n", encoding="utf-8")
            args = argparse.Namespace(request_id=[], request_ids_file=explicit)
            with self.assertRaisesRegex(ValueError, "selected no request ids"):
                batch_runner.selected_request_ids(args, base)

    def test_duplicate_request_ids_fail_before_manifest_or_host_work(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            duplicate_file = base / "duplicate_ids.txt"
            duplicate_file.write_text("request_1\nrequest_1\n", encoding="utf-8")
            (base / "REQUEST_IDS.txt").write_text(
                "request_1\nREQUEST_1\n", encoding="utf-8"
            )
            selections = (
                argparse.Namespace(
                    request_id=["request_1", "request_1"], request_ids_file=None
                ),
                argparse.Namespace(request_id=[], request_ids_file=duplicate_file),
                argparse.Namespace(request_id=[], request_ids_file=None),
            )
            for args in selections:
                with self.subTest(args=args), self.assertRaisesRegex(
                    ValueError, "duplicate/case-colliding request id"
                ):
                    batch_runner.selected_request_ids(args, base)
            with self.assertRaisesRegex(
                ValueError, "duplicate/case-colliding request id"
            ):
                batch_runner.load_expected_frames(
                    base / "requests", ["request_1", "request_1"]
                )

    def test_portable_names_reject_colon_percent_and_dot_aliases_pre_host(self):
        for frame in ("foo:..png", "foo%2f..png", "../x.png"):
            with self.subTest(frame=frame), self.assertRaises(ValueError):
                batch_runner.validate_relative_png_frame(frame)
        with tempfile.TemporaryDirectory() as raw:
            results = Path(raw) / "results"
            results.mkdir()
            for request_id in ("ae_pixel_.", "ae_pixel_.."):
                with self.subTest(request_id=request_id), self.assertRaises(ValueError):
                    batch_runner.expected_output_directories(
                        results, {request_id: ["frame.png"]}
                    )

    def test_case_collisions_and_output_symlink_are_rejected_pre_host(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results = root / "results"
            results.mkdir()
            with self.assertRaisesRegex(ValueError, "case collision"):
                batch_runner.expected_output_directories(
                    results,
                    {
                        "ae_pixel_Foo_20260101": ["a.png"],
                        "ae_pixel_foo_20260102": ["b.png"],
                    },
                )
            outside = root / "outside"
            outside.mkdir()
            (results / "request_1").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                batch_runner.expected_output_directories(
                    results, {"request_1": ["frame.png"]}
                )

    def test_output_directory_symlink_replacement_after_preflight_fails_ownership(self):
        with tempfile.TemporaryDirectory() as raw:
            results_base = Path(raw) / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            frames = {"request_1": ["frame.png"]}
            expected_dirs = batch_runner.expected_output_directories(results_base, frames)
            expected_identities = batch_runner.bind_output_directory_identities(
                expected_dirs, create=False
            )
            result = self.batch(output_dir, ["frame.png"])
            moved = results_base / "moved"
            output_dir.rename(moved)
            output_dir.symlink_to(moved, target_is_directory=True)

            passed = batch_runner.validate_batch_outputs(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                expected_request_ids=["request_1"],
                expected_frames_by_request=frames,
                expected_output_dirs_by_request=expected_dirs,
                expected_output_identities_by_request=expected_identities,
                expected_results_base=results_base,
                timeout_seconds=0.1,
                stable_window_seconds=0.01,
                poll_interval_seconds=0.005,
            )

            self.assertFalse(passed)
            self.assertEqual(result["requests"][0]["rendered"], [])
            self.assertEqual(result["requests"][0]["hostless_png_observations"], {})
            self.assertTrue(
                any(
                    "not a lexical directory" in error or "identity differs" in error
                    for error in result["requests"][0]["errors"]
                )
            )

    def test_extendscript_path_limit_fails_closed(self):
        overlong = Path("/") / ("a" * (batch_runner.MAX_EXTENDSCRIPT_PATH_CHARS + 1))
        with self.assertRaisesRegex(ValueError, "safe ExtendScript path length"):
            batch_runner.validate_extendscript_path(overlong, "test")

    def test_full_crc_validation_promotes_only_the_valid_png(self):
        with tempfile.TemporaryDirectory() as raw:
            results_base = Path(raw) / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "valid.png").write_bytes(VALID_PNG)
            (output_dir / "bad_crc.png").write_bytes(bad_idat_crc_with_valid_signature_and_iend())
            result = self.batch(output_dir, ["valid.png", "bad_crc.png"])

            self.assertFalse(self.validate(result, results_base))

            request = result["requests"][0]
            self.assertEqual(request["rendered"], [])
            valid = request["hostless_png_observations"]["valid.png"]
            bad = request["hostless_png_observations"]["bad_crc.png"]
            self.assertEqual(valid["validation"], "png_chunks_crc_iend")
            self.assertTrue(valid["crc_validated"])
            self.assertTrue(valid["identity_bound"])
            self.assertEqual(len(valid["sha256"]), 64)
            self.assertEqual(bad["status"], "unstable")
            self.assertFalse(bad["crc_validated"])
            self.assertEqual(request["hostless_output_validation"]["status"], "failed")
            self.assertEqual(result["hostless_output_validation"]["status"], "failed")

    def test_run_id_must_match_batch_and_every_request(self):
        with tempfile.TemporaryDirectory() as raw:
            results_base = Path(raw) / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            result["run_id"] = "wrong"
            result["requests"][0]["run_id"] = "expected"

            passed = batch_runner.validate_batch_outputs(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                expected_request_ids=["request_1"],
                expected_run_id="expected",
                expected_results_base=results_base,
                timeout_seconds=0.2,
                stable_window_seconds=0.02,
                poll_interval_seconds=0.005,
            )
            self.assertFalse(passed)
            self.assertTrue(
                any("batch run_id differs" in error for error in result["hostless_output_validation"]["errors"])
            )

    def test_wrong_raw_kind_or_schema_never_promotes(self):
        with tempfile.TemporaryDirectory() as raw:
            results_base = Path(raw) / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            result.update(run_id="run-1", kind="WRONG", schema_version=999)
            result["requests"][0].update(run_id="run-1", kind="WRONG", schema_version=999)

            self.assertFalse(
                batch_runner.validate_batch_outputs(
                    result,
                    not_before_ns=time.time_ns() - 1_000_000_000,
                    expected_request_ids=["request_1"],
                    expected_run_id="run-1",
                    expected_results_base=results_base,
                    timeout_seconds=0.2,
                    stable_window_seconds=0.02,
                    poll_interval_seconds=0.005,
                )
            )
            self.assertEqual(result["requests"][0]["rendered"], [])
            self.assertTrue(any("batch kind" in error for error in result["hostless_output_validation"]["errors"]))
            self.assertTrue(any("request kind" in error for error in result["requests"][0]["errors"]))

    def test_lexical_frame_symlink_is_rejected_not_resolved(self):
        with tempfile.TemporaryDirectory() as raw:
            results_base = Path(raw) / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "other.png").write_bytes(VALID_PNG)
            (output_dir / "frame.png").symlink_to(output_dir / "other.png")
            result = self.batch(output_dir, ["frame.png"])

            self.assertFalse(self.validate(result, results_base))
            request = result["requests"][0]
            self.assertEqual(request["rendered"], [])
            self.assertTrue(any("is a symlink" in error for error in request["errors"]))

    def test_candidate_symlink_swap_between_check_and_old_resolve_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            results_base = Path(raw) / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            candidate = output_dir / "frame.png"
            other = output_dir / "other.png"
            candidate.write_bytes(VALID_PNG)
            other.write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            original_is_symlink = Path.is_symlink
            canonical_candidate = candidate.parent.resolve() / candidate.name
            swapped = False

            def swap_after_check(path: Path) -> bool:
                nonlocal swapped
                answer = original_is_symlink(path)
                if path == canonical_candidate and not swapped:
                    candidate.unlink()
                    candidate.symlink_to(other)
                    swapped = True
                    return False
                return answer

            with mock.patch.object(Path, "is_symlink", new=swap_after_check):
                passed = self.validate(result, results_base)

            self.assertTrue(swapped)
            self.assertFalse(passed)
            self.assertTrue(candidate.is_symlink())
            self.assertEqual(result["requests"][0]["rendered"], [])
            observation = result["requests"][0]["hostless_png_observations"]["frame.png"]
            self.assertFalse(observation["crc_validated"])

    def test_frame_swapped_to_symlink_after_path_binding_fails_nofollow_gate(self):
        with tempfile.TemporaryDirectory() as raw:
            results_base = Path(raw) / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            candidate = output_dir / "frame.png"
            other = output_dir / "other.png"
            candidate.write_bytes(VALID_PNG)
            other.write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])

            def swap_then_observe(path: Path, **kwargs: object) -> dict[str, object]:
                path.unlink()
                path.symlink_to(other)
                return batch_runner.wait_for_complete_png(path, **kwargs)

            passed = batch_runner.validate_batch_outputs(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                expected_request_ids=["request_1"],
                expected_results_base=results_base,
                timeout_seconds=0.08,
                stable_window_seconds=0.01,
                poll_interval_seconds=0.005,
                observe_png=swap_then_observe,
            )

            self.assertFalse(passed)
            self.assertTrue(candidate.is_symlink())
            self.assertEqual(result["requests"][0]["rendered"], [])
            observation = result["requests"][0]["hostless_png_observations"]["frame.png"]
            self.assertFalse(observation["crc_validated"])

    def test_frame_swapped_to_external_hardlink_after_binding_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            candidate = output_dir / "frame.png"
            external = root / "external.png"
            candidate.write_bytes(VALID_PNG)
            external.write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])

            def hardlink_then_observe(path: Path, **kwargs: object) -> dict[str, object]:
                path.unlink()
                os.link(external, path)
                return batch_runner.wait_for_complete_png(path, **kwargs)

            passed = batch_runner.validate_batch_outputs(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                expected_request_ids=["request_1"],
                expected_results_base=results_base,
                timeout_seconds=0.08,
                stable_window_seconds=0.01,
                poll_interval_seconds=0.005,
                observe_png=hardlink_then_observe,
            )

            self.assertFalse(passed)
            self.assertEqual(candidate.stat().st_ino, external.stat().st_ino)
            self.assertGreater(candidate.stat().st_nlink, 1)
            self.assertEqual(result["requests"][0]["rendered"], [])

    def test_post_parse_same_inode_symlink_swap_fails_final_lstat(self):
        with tempfile.TemporaryDirectory() as raw:
            results_base = Path(raw) / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            candidate = output_dir / "frame.png"
            kept = output_dir / "kept.png"
            candidate.write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])

            def observe_then_alias(path: Path, **kwargs: object) -> dict[str, object]:
                observation = batch_runner.wait_for_complete_png(path, **kwargs)
                path.rename(kept)
                path.symlink_to(kept)
                return observation

            passed = batch_runner.validate_batch_outputs(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                expected_request_ids=["request_1"],
                expected_results_base=results_base,
                timeout_seconds=0.2,
                stable_window_seconds=0.01,
                poll_interval_seconds=0.005,
                observe_png=observe_then_alias,
            )

            self.assertFalse(passed)
            self.assertTrue(candidate.is_symlink())
            observation = result["requests"][0]["hostless_png_observations"]["frame.png"]
            self.assertEqual(observation["status"], "validator_error")
            self.assertFalse(observation["crc_validated"])

    def test_inode_swap_with_same_size_and_mtime_breaks_crc_digest_handoff(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "frame.png"
            path.write_bytes(VALID_PNG)

            def swapping_observer(candidate: Path, **_: object) -> dict[str, object]:
                original = candidate.stat()
                replacement = candidate.with_name("replacement.png")
                replacement.write_bytes(VALID_PNG)
                os.utime(replacement, ns=(original.st_atime_ns, original.st_mtime_ns))
                os.replace(replacement, candidate)
                return {
                    "status": "stable",
                    "format_complete": True,
                    "crc_validated": True,
                    "validation": "png_chunks_crc_iend",
                    "size_bytes": original.st_size,
                    "modified_ns": original.st_mtime_ns,
                    "device": original.st_dev,
                    "inode": original.st_ino,
                }

            observation = batch_runner.observe_and_bind_png(
                path,
                observe_png=swapping_observer,
                not_before_ns=0,
                timeout_seconds=0.1,
                stable_window_seconds=0.01,
                poll_interval_seconds=0.005,
            )
            self.assertEqual(observation["status"], "changed_after_validation")
            self.assertFalse(observation["crc_validated"])
            self.assertNotIn("sha256", observation)

    def test_same_inode_same_mtime_bad_crc_is_reparsed_before_digest_binding(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "frame.png"
            path.write_bytes(VALID_PNG)

            def mutating_observer(candidate: Path, **_: object) -> dict[str, object]:
                original = candidate.stat()
                candidate.write_bytes(bad_idat_crc_with_valid_signature_and_iend())
                os.utime(candidate, ns=(original.st_atime_ns, original.st_mtime_ns))
                mutated = candidate.stat()
                self.assertEqual(mutated.st_ino, original.st_ino)
                return {
                    "status": "stable",
                    "format_complete": True,
                    "crc_validated": True,
                    "validation": "png_chunks_crc_iend",
                    "size_bytes": original.st_size,
                    "modified_ns": original.st_mtime_ns,
                    "device": original.st_dev,
                    "inode": original.st_ino,
                }

            observation = batch_runner.observe_and_bind_png(
                path,
                observe_png=mutating_observer,
                not_before_ns=0,
                timeout_seconds=0.1,
                stable_window_seconds=0.01,
                poll_interval_seconds=0.005,
            )
            self.assertEqual(observation["status"], "changed_or_invalid_after_validation")
            self.assertFalse(observation["crc_validated"])
            self.assertFalse(observation["identity_bound"])

    def test_valid_legacy_rendered_field_is_revalidated_and_preserved(self):
        with tempfile.TemporaryDirectory() as raw:
            results_base = Path(raw) / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "legacy.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, [])
            request = result["requests"][0]
            request.pop("render_candidates")
            request["rendered"] = ["legacy.png"]

            self.assertTrue(self.validate(result, results_base))
            self.assertEqual(request["render_candidates"], ["legacy.png"])
            self.assertEqual(request["rendered"], ["legacy.png"])
            self.assertEqual(request["hostless_output_validation"]["status"], "passed")

    def test_pre_host_manifest_prevents_silent_case_omission(self):
        with tempfile.TemporaryDirectory() as raw:
            results_base = Path(raw) / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "only.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["only.png"])

            passed = batch_runner.validate_batch_outputs(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                expected_request_ids=["request_1"],
                expected_frames_by_request={"request_1": ["only.png", "omitted.png"]},
                expected_results_base=results_base,
                timeout_seconds=0.2,
                stable_window_seconds=0.02,
                poll_interval_seconds=0.005,
            )

            self.assertFalse(passed)
            request = result["requests"][0]
            self.assertEqual(request["rendered"], [])
            self.assertTrue(
                any("differ from pre-host manifest" in error for error in request["errors"])
            )

    def test_duplicate_candidate_fails_without_double_promotion(self):
        with tempfile.TemporaryDirectory() as raw:
            results_base = Path(raw) / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png", "frame.png"])

            self.assertFalse(self.validate(result, results_base))
            request = result["requests"][0]
            self.assertEqual(request["rendered"], [])
            self.assertEqual(list(request["hostless_png_observations"]), ["frame.png"])
            self.assertTrue(any("duplicate render candidate" in error for error in request["errors"]))

    def test_cross_request_output_substitution_cannot_overwrite_summaries(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "results"
            first_dir = results_base / "request_1"
            second_dir = results_base / "request_2"
            first_dir.mkdir(parents=True)
            second_dir.mkdir(parents=True)
            (first_dir / "a.png").write_bytes(VALID_PNG)
            (first_dir / "b.png").write_bytes(VALID_PNG)
            result = {
                "kind": "olm_ae_pixel_validation_batch_render_result",
                "requests": [
                    self.batch(first_dir, ["a.png"])["requests"][0],
                    {
                        **self.batch(first_dir, ["b.png"])["requests"][0],
                        "request_id": "request_2",
                    },
                ],
            }
            expected_frames = {
                "request_1": ["a.png"],
                "request_2": ["b.png"],
            }
            expected_dirs = batch_runner.expected_output_directories(
                results_base, expected_frames
            )

            passed = batch_runner.validate_batch_outputs(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                expected_request_ids=["request_1", "request_2"],
                expected_frames_by_request=expected_frames,
                expected_output_dirs_by_request=expected_dirs,
                expected_results_base=results_base,
                timeout_seconds=0.2,
                stable_window_seconds=0.02,
                poll_interval_seconds=0.005,
            )
            self.assertFalse(passed)
            self.assertEqual(result["requests"][0]["rendered"], [])
            self.assertEqual(result["requests"][1]["rendered"], [])
            self.assertTrue(
                any("output_dir differs" in error for error in result["requests"][1]["errors"])
            )

            batch_json = root / "batch.json"
            validated = root / "validated"
            batch_runner.write_validated_batch_results(
                batch_json,
                result,
                expected_results_base=results_base,
                expected_output_dirs_by_request=expected_dirs,
                validated_summaries_base=validated,
            )
            self.assertFalse(
                (validated / "request_1" / "AE_PIXEL_VALIDATION_RENDER_RESULT.json").exists()
            )
            self.assertFalse(
                (validated / "request_2" / "AE_PIXEL_VALIDATION_RENDER_RESULT.json").exists()
            )

    def test_top_level_failure_rolls_back_every_valid_request_summary(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "results"
            requests = []
            for request_id, frame in (("request_1", "a.png"), ("request_2", "b.png")):
                output_dir = results_base / request_id
                output_dir.mkdir(parents=True)
                (output_dir / frame).write_bytes(VALID_PNG)
                request = self.batch(output_dir, [frame])["requests"][0]
                request["request_id"] = request_id
                requests.append(request)
            result = {
                "kind": "olm_ae_pixel_validation_batch_render_result",
                "schema_version": 2,
                "hostless_validation_required": True,
                "requests": requests,
            }

            passed = batch_runner.validate_batch_outputs(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                expected_request_ids=["request_1", "request_2"],
                expected_results_base=results_base,
                external_errors=["request source snapshot changed during host run"],
                timeout_seconds=0.2,
                stable_window_seconds=0.02,
                poll_interval_seconds=0.005,
            )

            self.assertFalse(passed)
            self.assertEqual(result["hostless_output_validation"]["status"], "failed")
            for request in result["requests"]:
                self.assertEqual(request["rendered"], [])
                self.assertEqual(request["hostless_output_validation"]["status"], "failed")
                self.assertIn(
                    "batch generation failed; request promotion rolled back",
                    request["errors"],
                )

            commit = root / "commit.json"
            validated = root / "validated"
            batch_runner.write_validated_batch_results(
                commit,
                result,
                expected_results_base=results_base,
                validated_summaries_base=validated,
                run_id="failed-run",
            )
            for request_id in ("request_1", "request_2"):
                self.assertFalse(
                    (
                        validated
                        / request_id
                        / "AE_PIXEL_VALIDATION_RENDER_RESULT.json"
                    ).exists()
                )
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")

    def test_path_escape_fails_closed_without_reading_outside_results(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (root / "outside.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["../../outside.png"])

            self.assertFalse(self.validate(result, results_base))
            request = result["requests"][0]
            self.assertEqual(request["rendered"], [])
            self.assertEqual(request["hostless_png_observations"], {})
            self.assertTrue(any("unsafe or non-portable" in error for error in request["errors"]))

    def test_manifest_traversal_is_rejected_before_host_selection(self):
        with tempfile.TemporaryDirectory() as raw:
            requests_base = Path(raw) / "requests"
            request_dir = requests_base / "request_1"
            request_dir.mkdir(parents=True)
            (request_dir / "request_manifest.json").write_text(
                json.dumps(
                    {
                        "request_id": "request_1",
                        "cases": [{"frame": "../../outside.png"}],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "unsafe or non-portable"):
                batch_runner.load_expected_frames(requests_base, ["request_1"])

    def test_dump_wrapper_uses_run_staged_sources_immune_to_original_mutation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            base = root / "handoff"
            request_root = base / "requests" / "request_1"
            input_dir = request_root / "input"
            input_dir.mkdir(parents=True)
            manifest_path = request_root / "request_manifest.json"
            manifest = {
                "request_id": "request_1",
                "reference_manifest": "reference_manifest.json",
                "input_dir": "input",
                "effect_name": "Original Effect",
                "cases": [
                    {
                        "frame": "frame.png",
                        "before_effects_frame": "before.png",
                    }
                ],
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (request_root / "reference_manifest.json").write_text("{}\n", encoding="utf-8")
            (input_dir / "before.png").write_bytes(VALID_PNG)
            original_snapshot = batch_runner.snapshot_request_sources(
                base / "requests", ["request_1"]
            )
            dump_js = root / "wrapper.jsx"

            with mock.patch(
                "sys.argv",
                [
                    "run_ae_validation_batch.py",
                    "--base-dir",
                    str(base),
                    "--request-id",
                    "request_1",
                    "--dump-js",
                    str(dump_js),
                ],
            ):
                self.assertEqual(batch_runner.main(), 0)

            staged_roots = list(
                (base / "batch_runs").glob(
                    "batch_run_*/source_capsule/staged_requests"
                )
            )
            self.assertEqual(len(staged_roots), 1)
            staged = staged_roots[0]
            self.assertIn(str(staged), dump_js.read_text(encoding="utf-8"))

            manifest["effect_name"] = "Transiently Mutated Effect"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertNotEqual(
                batch_runner.snapshot_request_sources(base / "requests", ["request_1"]),
                original_snapshot,
            )
            self.assertEqual(
                batch_runner.snapshot_request_sources(staged, ["request_1"]),
                original_snapshot,
            )
            staged_manifest = json.loads(
                (staged / "request_1" / "request_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(staged_manifest["effect_name"], "Original Effect")

    def test_staged_root_symlink_and_restored_source_mutation_fail_identity_binding(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source_root = root / "requests" / "request_1"
            input_dir = source_root / "input"
            input_dir.mkdir(parents=True)
            manifest = {
                "request_id": "request_1",
                "reference_manifest": "reference_manifest.json",
                "input_dir": "input",
                "cases": [
                    {
                        "frame": "frame.png",
                        "before_effects_frame": "before.png",
                    }
                ],
            }
            (source_root / "request_manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            (source_root / "reference_manifest.json").write_text(
                "{}\n", encoding="utf-8"
            )
            (input_dir / "before.png").write_bytes(VALID_PNG)
            expected = batch_runner.snapshot_request_sources(
                root / "requests", ["request_1"]
            )
            outside = root / "outside"
            outside.mkdir()
            symlink_stage = root / "run_symlink" / "staged_requests"
            symlink_stage.parent.mkdir()
            symlink_stage.symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "already exists"):
                batch_runner.stage_request_sources(
                    root / "requests", symlink_stage, expected
                )
            self.assertEqual(list(outside.iterdir()), [])

            staged = root / "run_owned" / "staged_requests"
            identities = batch_runner.stage_request_sources(
                root / "requests", staged, expected
            )
            staged_manifest = staged / "request_1" / "request_manifest.json"
            original = staged_manifest.read_bytes()
            os.chmod(staged_manifest, 0o644)
            staged_manifest.write_bytes(original + b" ")
            staged_manifest.write_bytes(original)
            os.chmod(staged_manifest, 0o444)
            restored_snapshot, changed_identities = (
                batch_runner.snapshot_owned_request_sources(staged, expected)
            )

            self.assertEqual(restored_snapshot, expected)
            self.assertNotEqual(changed_identities, identities)

    def test_restored_generation_ancestor_swap_changes_bound_guard(self):
        with tempfile.TemporaryDirectory() as raw:
            run_parent = Path(raw) / "runs"
            run_dir = run_parent / "batch_run_guarded"
            source_capsule = run_dir / "source_capsule"
            source_capsule.mkdir(parents=True)
            before = batch_runner.snapshot_generation_ancestors(run_dir)
            held = run_dir / "source_capsule_held"

            source_capsule.rename(held)
            source_capsule.mkdir()
            source_capsule.rmdir()
            held.rename(source_capsule)
            after = batch_runner.snapshot_generation_ancestors(run_dir)

            self.assertNotEqual(after, before)

    def test_atomic_persistence_updates_batch_and_per_request_schema(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "results"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))
            batch_json = root / "batch.json"
            validated = root / "validated"

            batch_runner.write_validated_batch_results(
                batch_json,
                result,
                expected_results_base=results_base,
                validated_summaries_base=validated,
            )

            written_batch = json.loads(batch_json.read_text(encoding="utf-8"))
            written_request = json.loads(
                (validated / "request_1" / "AE_PIXEL_VALIDATION_RENDER_RESULT.json").read_text(encoding="utf-8")
            )
            self.assertEqual(written_batch["requests"][0]["rendered"], ["frame.png"])
            self.assertEqual(written_request["rendered"], ["frame.png"])
            self.assertTrue(
                written_request["hostless_png_observations"]["frame.png"]["crc_validated"]
            )

    def test_production_persistence_separates_raw_and_validated_and_commits_last(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            raw_results = root / "raw_candidates"
            output_dir = raw_results / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            result["run_id"] = "run-1"
            result["requests"][0]["run_id"] = "run-1"
            self.assertTrue(
                batch_runner.validate_batch_outputs(
                    result,
                    not_before_ns=time.time_ns() - 1_000_000_000,
                    expected_request_ids=["request_1"],
                    expected_run_id="run-1",
                    expected_results_base=raw_results,
                    timeout_seconds=0.2,
                    stable_window_seconds=0.02,
                    poll_interval_seconds=0.005,
                )
            )
            raw_batch = root / "raw.json"
            raw_payload = b'{"raw":true}\n'
            raw_batch.write_bytes(raw_payload)
            validated = root / "validated_summaries"
            commit = root / "commit.json"

            batch_runner.write_validated_batch_results(
                commit,
                result,
                expected_results_base=raw_results,
                validated_summaries_base=validated,
                raw_batch_result_json=raw_batch,
                run_id="run-1",
            )

            self.assertEqual(raw_batch.read_bytes(), raw_payload)
            self.assertFalse((output_dir / "AE_PIXEL_VALIDATION_RENDER_RESULT.json").exists())
            summary = validated / "request_1" / "AE_PIXEL_VALIDATION_RENDER_RESULT.json"
            self.assertTrue(summary.is_file())
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["run_id"], "run-1")
            self.assertTrue(committed["generation_commit"]["commit_marker_written_last"])
            self.assertEqual(
                committed["raw_batch_result"]["sha256"],
                hashlib.sha256(raw_payload).hexdigest(),
            )
            validated_png = root / "validated_outputs" / "request_1" / "frame.png"
            self.assertTrue(validated_png.is_file())
            self.assertIsNotNone(batch_runner.inspect_complete_png(validated_png))
            self.assertEqual(
                committed["requests"][0]["output_dir"],
                str(validated_png.parent.resolve()),
            )
            self.assertEqual(
                committed["validated_outputs"]["request_1"]["frame.png"]["sha256"],
                hashlib.sha256(VALID_PNG).hexdigest(),
            )

    def test_mutation_between_validation_and_publication_forces_failed_commit(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            candidate = output_dir / "frame.png"
            candidate.write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))

            candidate.write_bytes(b"not a png")
            commit = root / "commit.json"
            published = batch_runner.write_validated_batch_results(
                commit,
                result,
                expected_results_base=results_base,
                validated_summaries_base=root / "validated_summaries",
                run_id="mutated-run",
            )

            self.assertFalse(published)
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertEqual(committed["requests"][0]["rendered"], [])
            self.assertEqual(committed["validated_outputs"], {})
            self.assertFalse(
                (
                    root
                    / "validated_summaries"
                    / "request_1"
                    / "AE_PIXEL_VALIDATION_RENDER_RESULT.json"
                ).exists()
            )

    def test_validated_root_symlink_cannot_publish_outside_generation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))
            outside = root / "outside"
            outside.mkdir()
            validated_outputs = root / "validated_outputs"
            validated_outputs.symlink_to(outside, target_is_directory=True)
            commit = root / "commit.json"

            published = batch_runner.write_validated_batch_results(
                commit,
                result,
                expected_results_base=results_base,
                validated_outputs_base=validated_outputs,
                validated_summaries_base=root / "validated_summaries",
                run_id="symlink-root-run",
            )

            self.assertFalse(published)
            self.assertEqual(list(outside.iterdir()), [])
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertEqual(committed["validated_outputs"], {})

    def test_validated_root_swap_after_binding_uses_dirfd_and_fails_commit(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))
            outside = root / "outside"
            outside.mkdir()
            validated_outputs = root / "validated_outputs"
            held_outputs = root / "validated_outputs_held"
            commit = root / "commit.json"
            original_copy = batch_runner.copy_bound_validated_png
            swapped = False

            def swap_root_then_copy(*args, **kwargs):
                nonlocal swapped
                if not swapped:
                    validated_outputs.rename(held_outputs)
                    validated_outputs.symlink_to(outside, target_is_directory=True)
                    swapped = True
                return original_copy(*args, **kwargs)

            with mock.patch.object(
                batch_runner,
                "copy_bound_validated_png",
                side_effect=swap_root_then_copy,
            ):
                published = batch_runner.write_validated_batch_results(
                    commit,
                    result,
                    expected_results_base=results_base,
                    validated_outputs_base=validated_outputs,
                    validated_summaries_base=root / "validated_summaries",
                    run_id="root-swap-run",
                )

            self.assertTrue(swapped)
            self.assertFalse(published)
            self.assertEqual(list(outside.rglob("*")), [])
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertEqual(committed["validated_outputs"], {})

    def test_all_summary_targets_preflight_before_any_summary_or_output(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_1 = results_base / "request_1"
            output_2 = results_base / "request_2"
            output_1.mkdir(parents=True)
            output_2.mkdir()
            (output_1 / "frame.png").write_bytes(VALID_PNG)
            (output_2 / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_1, ["frame.png"])
            request_2 = json.loads(json.dumps(result["requests"][0]))
            request_2["request_id"] = "request_2"
            request_2["output_dir"] = str(output_2)
            result["requests"].append(request_2)
            self.assertTrue(
                batch_runner.validate_batch_outputs(
                    result,
                    not_before_ns=time.time_ns() - 1_000_000_000,
                    expected_request_ids=["request_1", "request_2"],
                    expected_results_base=results_base,
                    timeout_seconds=0.2,
                    stable_window_seconds=0.02,
                    poll_interval_seconds=0.005,
                )
            )
            summaries = root / "validated_summaries"
            summaries.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (summaries / "request_2").symlink_to(
                outside, target_is_directory=True
            )
            commit = root / "commit.json"

            published = batch_runner.write_validated_batch_results(
                commit,
                result,
                expected_results_base=results_base,
                validated_summaries_base=summaries,
                run_id="summary-preflight-run",
            )

            self.assertFalse(published)
            self.assertFalse(
                (
                    summaries
                    / "request_1"
                    / "AE_PIXEL_VALIDATION_RENDER_RESULT.json"
                ).exists()
            )
            self.assertEqual(list(outside.iterdir()), [])
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertEqual(committed["validated_outputs"], {})
            self.assertEqual(committed["validated_summaries"], {})
            self.assertTrue(
                all(not request["rendered"] for request in committed["requests"])
            )

    def test_commit_boundary_rejects_validated_png_replaced_during_summary_write(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))
            validated_outputs = root / "validated_outputs"
            summaries = root / "validated_summaries"
            commit = root / "commit.json"
            original_write = batch_runner.write_result_json
            replaced = False

            def write_then_replace_png(path, payload, **kwargs):
                nonlocal replaced
                exact = original_write(path, payload, **kwargs)
                if path.name == "AE_PIXEL_VALIDATION_RENDER_RESULT.json" and not replaced:
                    target = validated_outputs / "request_1" / "frame.png"
                    replacement = target.with_name("replacement.png")
                    replacement.write_bytes(ALTERNATE_VALID_PNG)
                    os.replace(replacement, target)
                    replaced = True
                return exact

            with mock.patch.object(
                batch_runner, "write_result_json", side_effect=write_then_replace_png
            ):
                published = batch_runner.write_validated_batch_results(
                    commit,
                    result,
                    expected_results_base=results_base,
                    validated_outputs_base=validated_outputs,
                    validated_summaries_base=summaries,
                    run_id="late-png-swap",
                )

            self.assertTrue(replaced)
            self.assertFalse(published)
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertEqual(committed["validated_outputs"], {})
            self.assertEqual(committed["validated_summaries"], {})
            self.assertFalse((validated_outputs / "request_1" / "frame.png").exists())
            self.assertFalse(
                (summaries / "request_1" / "AE_PIXEL_VALIDATION_RENDER_RESULT.json").exists()
            )

    def test_commit_boundary_rejects_summary_replaced_after_atomic_write(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))
            summaries = root / "validated_summaries"
            commit = root / "commit.json"
            original_write = batch_runner.write_result_json
            replaced = False

            def write_then_replace_summary(path, payload, **kwargs):
                nonlocal replaced
                exact = original_write(path, payload, **kwargs)
                if path.name == "AE_PIXEL_VALIDATION_RENDER_RESULT.json" and not replaced:
                    replacement = path.with_name("replacement-summary.json")
                    replacement.write_bytes(b'{"tampered":true}\n')
                    os.replace(replacement, path)
                    replaced = True
                return exact

            with mock.patch.object(
                batch_runner,
                "write_result_json",
                side_effect=write_then_replace_summary,
            ):
                published = batch_runner.write_validated_batch_results(
                    commit,
                    result,
                    expected_results_base=results_base,
                    validated_summaries_base=summaries,
                    run_id="late-summary-swap",
                )

            self.assertTrue(replaced)
            self.assertFalse(published)
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertEqual(committed["validated_summaries"], {})
            self.assertFalse(
                (summaries / "request_1" / "AE_PIXEL_VALIDATION_RENDER_RESULT.json").exists()
            )

    def test_commit_boundary_rechecks_staged_source_identity_after_publication(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source_root = root / "requests" / "request_1"
            input_dir = source_root / "input"
            input_dir.mkdir(parents=True)
            manifest = {
                "request_id": "request_1",
                "reference_manifest": "reference_manifest.json",
                "input_dir": "input",
                "cases": [
                    {
                        "frame": "frame.png",
                        "before_effects_frame": "before.png",
                    }
                ],
            }
            (source_root / "request_manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            (source_root / "reference_manifest.json").write_text(
                "{}\n", encoding="utf-8"
            )
            (input_dir / "before.png").write_bytes(VALID_PNG)
            expected_sources = batch_runner.snapshot_request_sources(
                root / "requests", ["request_1"]
            )
            staged = root / "source_capsule" / "staged_requests"
            expected_identities = batch_runner.stage_request_sources(
                root / "requests", staged, expected_sources
            )
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))
            summaries = root / "validated_summaries"
            commit = root / "commit.json"
            staged_manifest = staged / "request_1" / "request_manifest.json"
            original_manifest = staged_manifest.read_bytes()
            original_write = batch_runner.write_result_json
            mutated = False

            def write_then_restore_staged_source(path, payload, **kwargs):
                nonlocal mutated
                exact = original_write(path, payload, **kwargs)
                if path.name == "AE_PIXEL_VALIDATION_RENDER_RESULT.json" and not mutated:
                    os.chmod(staged_manifest, 0o644)
                    staged_manifest.write_bytes(original_manifest + b" ")
                    staged_manifest.write_bytes(original_manifest)
                    os.chmod(staged_manifest, 0o444)
                    mutated = True
                return exact

            with mock.patch.object(
                batch_runner,
                "write_result_json",
                side_effect=write_then_restore_staged_source,
            ):
                published = batch_runner.write_validated_batch_results(
                    commit,
                    result,
                    expected_results_base=results_base,
                    validated_summaries_base=summaries,
                    staged_requests_base=staged,
                    expected_source_snapshot=expected_sources,
                    expected_staged_source_identities=expected_identities,
                    run_id="late-source-swap",
                )

            self.assertTrue(mutated)
            self.assertFalse(published)
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertFalse(
                (summaries / "request_1" / "AE_PIXEL_VALIDATION_RENDER_RESULT.json").exists()
            )

    def test_post_commit_verifier_rejects_commit_write_window_artifact_swaps(self):
        for target_kind in ("validated_png", "summary", "raw_candidate"):
            with self.subTest(target_kind=target_kind), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                results_base = root / "raw_candidates"
                output_dir = results_base / "request_1"
                output_dir.mkdir(parents=True)
                raw_png = output_dir / "frame.png"
                raw_png.write_bytes(VALID_PNG)
                result = self.batch(output_dir, ["frame.png"])
                self.assertTrue(self.validate(result, results_base))
                validated_outputs = root / "validated_outputs"
                summaries = root / "validated_summaries"
                commit = root / "commit.json"
                original_write = batch_runner.write_result_json
                replaced = False

                def replace_during_passed_commit(path, payload, **kwargs):
                    nonlocal replaced
                    generation = (
                        payload.get("generation_commit")
                        if isinstance(payload, dict)
                        else None
                    )
                    if (
                        path == commit
                        and isinstance(generation, dict)
                        and generation.get("status") == "passed"
                        and not replaced
                    ):
                        if target_kind == "validated_png":
                            target = validated_outputs / "request_1" / "frame.png"
                            replacement = target.with_name("replacement.png")
                            replacement.write_bytes(ALTERNATE_VALID_PNG)
                            os.replace(replacement, target)
                        elif target_kind == "summary":
                            target = (
                                summaries
                                / "request_1"
                                / "AE_PIXEL_VALIDATION_RENDER_RESULT.json"
                            )
                            replacement = target.with_name("replacement-summary.json")
                            replacement.write_bytes(b'{"tampered":true}\n')
                            os.replace(replacement, target)
                        else:
                            replacement = raw_png.with_name("replacement-raw.png")
                            replacement.write_bytes(ALTERNATE_VALID_PNG)
                            os.replace(replacement, raw_png)
                        replaced = True
                    return original_write(path, payload, **kwargs)

                with mock.patch.object(
                    batch_runner,
                    "write_result_json",
                    side_effect=replace_during_passed_commit,
                ):
                    published = batch_runner.write_validated_batch_results(
                        commit,
                        result,
                        expected_results_base=results_base,
                        validated_outputs_base=validated_outputs,
                        validated_summaries_base=summaries,
                        run_id=f"commit-window-{target_kind}",
                    )

                self.assertTrue(replaced)
                self.assertFalse(published)
                committed = json.loads(commit.read_text(encoding="utf-8"))
                self.assertEqual(committed["generation_commit"]["status"], "failed")
                self.assertEqual(committed["validated_outputs"], {})
                self.assertEqual(committed["validated_summaries"], {})
                self.assertFalse(
                    (validated_outputs / "request_1" / "frame.png").exists()
                )
                self.assertFalse(
                    (
                        summaries
                        / "request_1"
                        / "AE_PIXEL_VALIDATION_RENDER_RESULT.json"
                    ).exists()
                )

    def test_writer_anchor_rejects_coordinated_marker_and_png_rewrite(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))
            validated_outputs = root / "validated_outputs"
            summaries = root / "validated_summaries"
            commit = root / "commit.json"
            original_write = batch_runner.write_result_json
            rewritten = False

            def rewrite_png_and_marker_after_original(path, payload, **kwargs):
                nonlocal rewritten
                exact = original_write(path, payload, **kwargs)
                generation = (
                    payload.get("generation_commit")
                    if isinstance(payload, dict)
                    else None
                )
                if (
                    path == commit
                    and isinstance(generation, dict)
                    and generation.get("status") == "passed"
                    and not rewritten
                ):
                    target = validated_outputs / "request_1" / "frame.png"
                    replacement = target.with_name("replacement.png")
                    replacement.write_bytes(ALTERNATE_VALID_PNG)
                    os.replace(replacement, target)
                    new_details = batch_runner.inspect_complete_png(target)
                    self.assertIsNotNone(new_details)
                    forged = json.loads(json.dumps(payload))
                    artifact = forged["validated_outputs"]["request_1"]["frame.png"]
                    artifact.update(new_details)
                    observation = forged["requests"][0]["hostless_png_observations"]["frame.png"]
                    observation.update(new_details)
                    forged_bytes = (
                        json.dumps(forged, indent=2, sort_keys=True) + "\n"
                    ).encode("utf-8")
                    batch_runner.atomic_write_bytes(commit, forged_bytes)
                    rewritten = True
                return exact

            with mock.patch.object(
                batch_runner,
                "write_result_json",
                side_effect=rewrite_png_and_marker_after_original,
            ):
                published = batch_runner.write_validated_batch_results(
                    commit,
                    result,
                    expected_results_base=results_base,
                    validated_outputs_base=validated_outputs,
                    validated_summaries_base=summaries,
                    run_id="coordinated-marker-rewrite",
                )

            self.assertTrue(rewritten)
            self.assertFalse(published)
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertEqual(committed["validated_outputs"], {})
            self.assertEqual(committed["validated_summaries"], {})

    def test_passed_commit_write_failure_rolls_back_every_published_artifact(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))
            validated_outputs = root / "validated_outputs"
            summaries = root / "validated_summaries"
            commit = root / "commit.json"
            original_write = batch_runner.write_result_json
            failed_once = False

            def fail_only_passed_commit(path, payload, **kwargs):
                nonlocal failed_once
                generation = (
                    payload.get("generation_commit")
                    if isinstance(payload, dict)
                    else None
                )
                if (
                    path == commit
                    and isinstance(generation, dict)
                    and generation.get("status") == "passed"
                    and not failed_once
                ):
                    failed_once = True
                    raise OSError("injected passed commit write failure")
                return original_write(path, payload, **kwargs)

            with mock.patch.object(
                batch_runner,
                "write_result_json",
                side_effect=fail_only_passed_commit,
            ):
                published = batch_runner.write_validated_batch_results(
                    commit,
                    result,
                    expected_results_base=results_base,
                    validated_outputs_base=validated_outputs,
                    validated_summaries_base=summaries,
                    run_id="commit-write-failure",
                )

            self.assertTrue(failed_once)
            self.assertFalse(published)
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertEqual(committed["publication_validation"]["status"], "failed")
            self.assertEqual(committed["validated_outputs"], {})
            self.assertEqual(committed["validated_summaries"], {})
            self.assertTrue(
                all(not request["rendered"] for request in committed["requests"])
            )
            self.assertFalse(
                (validated_outputs / "request_1" / "frame.png").exists()
            )
            self.assertFalse(
                (
                    summaries
                    / "request_1"
                    / "AE_PIXEL_VALIDATION_RENDER_RESULT.json"
                ).exists()
            )

    def test_post_commit_verifier_rechecks_request_child_name_binding(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))
            validated_outputs = root / "validated_outputs"
            summaries = root / "validated_summaries"
            commit = root / "commit.json"
            original_read = batch_runner.read_regular_file_nofollow_with_identity
            swapped = False

            def swap_child_after_png_read(path, **kwargs):
                nonlocal swapped
                if (
                    path.name == "AE_PIXEL_VALIDATION_RENDER_RESULT.json"
                    and commit.exists()
                    and not swapped
                ):
                    child = validated_outputs / "request_1"
                    held = validated_outputs / "request_1-held"
                    child.rename(held)
                    child.mkdir()
                    swapped = True
                return original_read(path, **kwargs)

            with mock.patch.object(
                batch_runner,
                "read_regular_file_nofollow_with_identity",
                side_effect=swap_child_after_png_read,
            ):
                published = batch_runner.write_validated_batch_results(
                    commit,
                    result,
                    expected_results_base=results_base,
                    validated_outputs_base=validated_outputs,
                    validated_summaries_base=summaries,
                    run_id="request-child-swap",
                )

            self.assertTrue(swapped)
            self.assertFalse(published)
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertEqual(committed["validated_outputs"], {})
            self.assertEqual(committed["validated_summaries"], {})

    def test_post_commit_verifier_rejects_commit_write_window_source_restore(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source_root = root / "requests" / "request_1"
            input_dir = source_root / "input"
            input_dir.mkdir(parents=True)
            manifest = {
                "request_id": "request_1",
                "reference_manifest": "reference_manifest.json",
                "input_dir": "input",
                "cases": [
                    {
                        "frame": "frame.png",
                        "before_effects_frame": "before.png",
                    }
                ],
            }
            (source_root / "request_manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            (source_root / "reference_manifest.json").write_text(
                "{}\n", encoding="utf-8"
            )
            (input_dir / "before.png").write_bytes(VALID_PNG)
            expected_sources = batch_runner.snapshot_request_sources(
                root / "requests", ["request_1"]
            )
            staged = root / "source_capsule" / "staged_requests"
            expected_identities = batch_runner.stage_request_sources(
                root / "requests", staged, expected_sources
            )
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            result["request_source_snapshot"] = expected_sources
            result["request_source_identity_snapshot"] = expected_identities
            result["request_source_snapshot_verified"] = True
            result["staged_requests_base"] = str(staged)
            self.assertTrue(self.validate(result, results_base))
            summaries = root / "validated_summaries"
            commit = root / "commit.json"
            staged_manifest = staged / "request_1" / "request_manifest.json"
            original_manifest = staged_manifest.read_bytes()
            original_write = batch_runner.write_result_json
            mutated = False

            def mutate_source_during_passed_commit(path, payload, **kwargs):
                nonlocal mutated
                generation = (
                    payload.get("generation_commit")
                    if isinstance(payload, dict)
                    else None
                )
                if (
                    path == commit
                    and isinstance(generation, dict)
                    and generation.get("status") == "passed"
                    and not mutated
                ):
                    os.chmod(staged_manifest, 0o644)
                    staged_manifest.write_bytes(original_manifest + b" ")
                    staged_manifest.write_bytes(original_manifest)
                    os.chmod(staged_manifest, 0o444)
                    mutated = True
                return original_write(path, payload, **kwargs)

            with mock.patch.object(
                batch_runner,
                "write_result_json",
                side_effect=mutate_source_during_passed_commit,
            ):
                published = batch_runner.write_validated_batch_results(
                    commit,
                    result,
                    expected_results_base=results_base,
                    validated_summaries_base=summaries,
                    staged_requests_base=staged,
                    expected_source_snapshot=expected_sources,
                    expected_staged_source_identities=expected_identities,
                    run_id="commit-window-source",
                )

            self.assertTrue(mutated)
            self.assertFalse(published)
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertEqual(committed["validated_outputs"], {})
            self.assertEqual(committed["validated_summaries"], {})

    def test_consumer_verifier_detects_post_return_artifact_mutation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))
            validated_outputs = root / "validated_outputs"
            commit = root / "commit.json"

            self.assertTrue(
                batch_runner.write_validated_batch_results(
                    commit,
                    result,
                    expected_results_base=results_base,
                    validated_outputs_base=validated_outputs,
                    validated_summaries_base=root / "validated_summaries",
                    run_id="consumer-verifier",
                )
            )
            self.assertEqual(
                batch_runner.verify_generation_commit(
                    commit, expected_run_id="consumer-verifier"
                ),
                (True, []),
            )
            target = validated_outputs / "request_1" / "frame.png"
            replacement = target.with_name("replacement.png")
            replacement.write_bytes(ALTERNATE_VALID_PNG)
            os.replace(replacement, target)

            verified, errors = batch_runner.verify_generation_commit(
                commit, expected_run_id="consumer-verifier"
            )
            self.assertFalse(verified)
            self.assertTrue(
                any("validated PNG changed after commit" in error for error in errors)
            )

    def test_consumer_verifier_uses_published_writer_commit_anchor(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))
            validated_outputs = root / "validated_outputs"
            commit = root / "commit.json"

            self.assertTrue(
                batch_runner.write_validated_batch_results(
                    commit,
                    result,
                    expected_results_base=results_base,
                    validated_outputs_base=validated_outputs,
                    validated_summaries_base=root / "validated_summaries",
                    run_id="published-anchor",
                )
            )
            anchor = result.get("generation_commit_anchor")
            self.assertIsInstance(anchor, dict)
            original_sha = anchor["sha256"]
            target = validated_outputs / "request_1" / "frame.png"
            replacement = target.with_name("replacement.png")
            replacement.write_bytes(ALTERNATE_VALID_PNG)
            os.replace(replacement, target)
            forged = json.loads(commit.read_text(encoding="utf-8"))
            new_details = batch_runner.inspect_complete_png(target)
            self.assertIsNotNone(new_details)
            forged["validated_outputs"]["request_1"]["frame.png"].update(new_details)
            forged["requests"][0]["hostless_png_observations"]["frame.png"].update(new_details)
            batch_runner.write_result_json(commit, forged)

            verified, errors = batch_runner.verify_generation_commit(
                commit,
                expected_run_id="published-anchor",
                expected_commit_sha256=original_sha,
                expected_generation_identity=(
                    anchor["generation_device"],
                    anchor["generation_inode"],
                ),
            )
            self.assertFalse(verified)
            self.assertTrue(
                any("published anchor" in error for error in errors),
                errors,
            )

    def test_zero_request_generation_can_never_commit_passed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            results_base.mkdir()
            result = {
                "kind": "olm_ae_pixel_validation_batch_render_result",
                "schema_version": 2,
                "requests": [],
                "hostless_output_validation": {"status": "passed"},
            }
            commit = root / "commit.json"

            published = batch_runner.write_validated_batch_results(
                commit,
                result,
                expected_results_base=results_base,
                validated_summaries_base=root / "validated_summaries",
                run_id="empty-run",
            )

            self.assertFalse(published)
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertEqual(committed["validated_outputs"], {})
            self.assertEqual(committed["validated_summaries"], {})

    def test_late_request_copy_failure_removes_all_validated_outputs(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_1 = results_base / "request_1"
            output_2 = results_base / "request_2"
            output_1.mkdir(parents=True)
            output_2.mkdir()
            (output_1 / "frame.png").write_bytes(VALID_PNG)
            (output_2 / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_1, ["frame.png"])
            request_2 = json.loads(json.dumps(result["requests"][0]))
            request_2["request_id"] = "request_2"
            request_2["output_dir"] = str(output_2)
            result["requests"].append(request_2)
            self.assertTrue(
                batch_runner.validate_batch_outputs(
                    result,
                    not_before_ns=time.time_ns() - 1_000_000_000,
                    expected_request_ids=["request_1", "request_2"],
                    expected_results_base=results_base,
                    timeout_seconds=0.2,
                    stable_window_seconds=0.02,
                    poll_interval_seconds=0.005,
                )
            )
            validated_outputs = root / "validated_outputs"
            commit = root / "commit.json"
            original_copy = batch_runner.copy_bound_validated_png
            calls = 0

            def fail_second_copy(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected second request publication failure")
                return original_copy(*args, **kwargs)

            with mock.patch.object(
                batch_runner,
                "copy_bound_validated_png",
                side_effect=fail_second_copy,
            ):
                published = batch_runner.write_validated_batch_results(
                    commit,
                    result,
                    expected_results_base=results_base,
                    validated_outputs_base=validated_outputs,
                    validated_summaries_base=root / "validated_summaries",
                    run_id="late-copy-failure",
                )

            self.assertFalse(published)
            self.assertEqual(calls, 2)
            self.assertFalse((validated_outputs / "request_1" / "frame.png").exists())
            self.assertFalse((validated_outputs / "request_2" / "frame.png").exists())
            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(committed["generation_commit"]["status"], "failed")
            self.assertEqual(committed["validated_outputs"], {})
            self.assertEqual(committed["validated_summaries"], {})

    def test_committed_raw_sha_binds_exact_bytes_parsed_before_disk_mutation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            results_base = root / "raw_candidates"
            output_dir = results_base / "request_1"
            output_dir.mkdir(parents=True)
            (output_dir / "frame.png").write_bytes(VALID_PNG)
            result = self.batch(output_dir, ["frame.png"])
            self.assertTrue(self.validate(result, results_base))
            raw_result = root / "raw.json"
            parsed_bytes = b'{"kind":"exactly-parsed-host-result"}\n'
            raw_result.write_bytes(b'{"kind":"mutated-after-parse"}\n')
            commit = root / "commit.json"

            self.assertTrue(
                batch_runner.write_validated_batch_results(
                    commit,
                    result,
                    expected_results_base=results_base,
                    validated_summaries_base=root / "validated_summaries",
                    raw_batch_result_json=raw_result,
                    raw_batch_result_bytes=parsed_bytes,
                    run_id="raw-binding-run",
                )
            )

            committed = json.loads(commit.read_text(encoding="utf-8"))
            self.assertEqual(raw_result.read_bytes(), parsed_bytes)
            self.assertEqual(
                committed["raw_batch_result"]["sha256"],
                hashlib.sha256(parsed_bytes).hexdigest(),
            )
            self.assertTrue(
                committed["raw_batch_result"]["digest_of_exact_parsed_bytes"]
            )

    def test_mocked_host_timeout_retains_shared_active_lease(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            run_dir = root / "run"
            raw_results = run_dir / "raw_candidates"
            run_dir.mkdir()
            raw_results.mkdir()
            frames = {"request_1": ["frame.png"]}
            output_dirs = batch_runner.expected_output_directories(raw_results, frames)
            output_identities = batch_runner.bind_output_directory_identities(
                output_dirs, create=True
            )
            validated_outputs = run_dir / "validated_outputs"
            validated_summaries = run_dir / "validated"
            validated_root_identities = batch_runner.bind_output_directory_identities(
                {
                    "validated_outputs": validated_outputs,
                    "validated_summaries": validated_summaries,
                },
                create=True,
            )
            lock_path = root / "ae.lock"
            args = argparse.Namespace(timeout=1, app_name="Adobe After Effects 2026", lock_path=lock_path)
            source_snapshot = {"request_1": {"request_manifest.json": "a" * 64}}
            source_identities = {"directories": {}, "files": {}}
            with mock.patch.object(
                batch_runner.subprocess,
                "run",
                side_effect=batch_runner.subprocess.TimeoutExpired(["osascript"], 1),
            ), mock.patch.object(
                batch_runner,
                "snapshot_owned_request_sources",
                return_value=(source_snapshot, source_identities),
            ):
                rc = batch_runner.run_locked_batch(
                    args=args,
                    run_dir=run_dir,
                    wrapper_jsx=run_dir / "wrapper.jsx",
                    raw_batch_result_json=run_dir / "raw.json",
                    commit_result_json=run_dir / "commit.json",
                    published_result_json=None,
                    requests_base=root / "requests",
                    results_base=raw_results,
                    validated_outputs_base=validated_outputs,
                    validated_summaries_base=validated_summaries,
                    run_id="run-timeout",
                    request_ids=["request_1"],
                    expected_frames=frames,
                    expected_output_dirs=output_dirs,
                    expected_output_identities=output_identities,
                    expected_validated_root_identities=validated_root_identities,
                    expected_source_snapshot=source_snapshot,
                    expected_staged_source_identities=source_identities,
                    js="// no AE",
                )
            self.assertEqual(rc, 1)
            lease = batch_runner.ae_active_marker_path(lock_path)
            self.assertTrue(lease.is_file())
            marker = json.loads(lease.read_text(encoding="utf-8"))
            self.assertEqual(marker["run_id"], "run-timeout")


if __name__ == "__main__":
    unittest.main()
