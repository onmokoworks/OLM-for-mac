import importlib.util
import hashlib
import json
import os
import re
import tempfile
import threading
import time
import types
import unittest
import zlib
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("single_case_runner", ROOT / "scripts/run_ae_single_case.py")
assert SPEC and SPEC.loader
single_case_runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(single_case_runner)


def png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return len(payload).to_bytes(4, "big") + chunk_type + payload + crc.to_bytes(4, "big")


PNG_IHDR = png_chunk(b"IHDR", b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00")
PNG_IDAT_PAYLOAD = zlib.compress(b"\x00\x00\x00\x00\xff")
PNG_IDAT_CRC = (zlib.crc32(PNG_IDAT_PAYLOAD, zlib.crc32(b"IDAT")) & 0xFFFFFFFF).to_bytes(4, "big")
PNG_STALLED_AT_IDAT_HEADER = (
    single_case_runner.PNG_SIGNATURE
    + PNG_IHDR
    + len(PNG_IDAT_PAYLOAD).to_bytes(4, "big")
    + b"IDAT"
)
PNG_WITHOUT_IEND = PNG_STALLED_AT_IDAT_HEADER + PNG_IDAT_PAYLOAD + PNG_IDAT_CRC
PNG_IEND = png_chunk(b"IEND", b"")
VALID_PNG = PNG_WITHOUT_IEND + PNG_IEND
ALTERNATE_VALID_PNG = (
    single_case_runner.PNG_SIGNATURE
    + PNG_IHDR
    + png_chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00\xff"))
    + PNG_IEND
)


def create_request_fixture(
    root: Path,
    *,
    case_id: str = "case_0001",
    frame: str = "case_0001.png",
    input_name: str = "case_0001_before_effects.png",
) -> Path:
    request_dir = root / "request"
    input_dir = request_dir / "input"
    input_dir.mkdir(parents=True)
    (input_dir / input_name).write_bytes(VALID_PNG)
    (request_dir / "reference_manifest.json").write_text(
        json.dumps({"cases": [{"id": case_id, "time": 0}]}),
        encoding="utf-8",
    )
    (request_dir / "request_manifest.json").write_text(
        json.dumps({
            "reference_manifest": "reference_manifest.json",
            "input_dir": "input",
            "cases": [{
                "id": case_id,
                "frame": frame,
                "before_effects_frame": input_name,
            }],
        }),
        encoding="utf-8",
    )
    return request_dir


def publish_valid_png_fixture(root: Path) -> dict[str, object]:
    root = root.resolve()
    request_dir = create_request_fixture(root)
    output_container = root / "output"
    output_container.mkdir()
    run_id, run_dir = single_case_runner.create_single_run_directory(output_container)
    for leaf in ("runtime", "raw_output", "validated_output", "publication"):
        os.mkdir(run_dir / leaf, 0o700)
    origin_binding = single_case_runner.build_expected_output_binding(
        request_dir=request_dir,
        case_id="case_0001",
        output_dir=run_dir / "raw_output",
        output_mode="png",
    )
    staged_request = single_case_runner.stage_request_sources(origin_binding, run_dir)
    binding = single_case_runner.build_expected_output_binding(
        request_dir=staged_request,
        case_id="case_0001",
        output_dir=run_dir / "raw_output",
        output_mode="png",
    )
    runtime_dir = run_dir / "runtime"
    staged_program = runtime_dir / single_case_runner.RUNTIME_PROGRAM_LEAF
    wrapper_path = runtime_dir / single_case_runner.RUNTIME_WRAPPER_LEAF
    single_case_runner.atomic_write_bytes(
        staged_program,
        (ROOT / "scripts" / "ae_render_single_case.jsx").read_bytes(),
        mode=0o444,
    )
    wrapper = single_case_runner.build_single_case_wrapper_js(
        request_dir=staged_request,
        case_id="case_0001",
        output_dir=run_dir / "raw_output",
        log_path=run_dir / "raw_output" / "AE_SINGLE_CASE.log",
        result_json=run_dir / "raw_output" / "AE_SINGLE_CASE_RESULT.json",
        jsx_path=staged_program,
        overrides={},
        ae_env={},
        output_mode="png",
        output_template="",
        keep_open=False,
    )
    single_case_runner.atomic_write_bytes(
        wrapper_path,
        wrapper.encode("utf-8"),
        mode=0o444,
    )
    runtime_source_snapshot = single_case_runner.read_fixed_runtime_sources(
        runtime_dir
    )
    binding.output_path.write_bytes(VALID_PNG)
    result = {
        "kind": "olm_ae_single_case_result",
        "status": "ok",
        "request_dir": str(staged_request),
        "case_id": "case_0001",
        "output_dir": str(run_dir / "raw_output"),
        "output_png": str(binding.output_path),
        "output_exr": "",
    }
    valid = single_case_runner.validate_result_output(
        result,
        not_before_ns=time.time_ns() - 1_000_000_000,
        expected_binding=binding,
        timeout_seconds=1.0,
        stable_window_seconds=0.02,
        poll_interval_seconds=0.005,
    )
    if not valid or result.get("status") != "ok":
        raise AssertionError(f"fixture output validation failed: {result}")
    result_path, commit_path, commit_sha256 = (
        single_case_runner.publish_single_case_evidence(
            result=result,
            raw_binding=binding,
            invocation_request_dir=request_dir,
            validated_dir=run_dir / "validated_output",
            publication_dir=run_dir / "publication",
            run_id=run_id,
            run_dir=run_dir,
            runtime_source_snapshot=runtime_source_snapshot,
        )
    )
    return {
        "request_dir": request_dir,
        "run_id": run_id,
        "run_dir": run_dir,
        "result": result,
        "result_path": result_path,
        "commit_path": commit_path,
        "commit_sha256": commit_sha256,
        "commit_bytes": commit_path.read_bytes(),
        "validated_output": run_dir / "validated_output" / "case_0001.png",
    }


class AePngCompletionContractTests(unittest.TestCase):
    def test_completion_regression_is_in_generic_beta_gate(self):
        source = (ROOT / "scripts/run_olm_generic_beta_gate.py").read_text(encoding="utf-8")
        self.assertIn(
            '("ae-output-completion", "tests/test_ae_png_completion.py", "scripts/run_ae_single_case.py")',
            source,
        )

    def test_default_output_is_unique_and_post_host_gate_remains_locked(self):
        source = (ROOT / "scripts/run_ae_single_case.py").read_text(encoding="utf-8")
        self.assertIn("%Y%m%d_%H%M%S_%f", source)
        self.assertIn("os.getpid()", source)
        main_index = source.index("def main() -> int:")
        lock_index = source.index("with ae_lock(args.lock_path.resolve()):")
        create_index = source.index("create_single_run_directory(output_container)", lock_index)
        origin_index = source.index("origin_binding = build_expected_output_binding(", create_index)
        stage_index = source.index("staged_request_dir = stage_request_sources(", origin_index)
        staged_binding_index = source.index("expected_binding = build_expected_output_binding(", stage_index)
        wrapper_index = source.index("js = build_single_case_wrapper_js(", staged_binding_index)
        host_index = source.index("proc = subprocess.run(", wrapper_index)
        validate_index = source.index("if validate_result_output(", host_index)
        publish_index = source.index("publish_single_case_evidence(", validate_index)
        self.assertLess(main_index, lock_index)
        self.assertLess(lock_index, create_index)
        self.assertLess(create_index, origin_index)
        self.assertLess(origin_index, stage_index)
        self.assertLess(stage_index, staged_binding_index)
        self.assertLess(staged_binding_index, wrapper_index)
        self.assertLess(wrapper_index, host_index)
        self.assertLess(host_index, validate_index)
        self.assertLess(validate_index, publish_index)
        self.assertIn("expected_commit_bytes=commit_payload", source)
        self.assertIn("expected_commit_sha256=commit_sha256", source)

    def test_single_case_uses_png_terminal_gate_and_two_second_window(self):
        source = (ROOT / "scripts/ae_render_single_case.jsx").read_text(encoding="utf-8")
        self.assertIn("function hasCompletePngTrailer", source)
        self.assertIn("var watchedPath = file.fsName;", source)
        self.assertIn("file = new File(watchedPath);", source)
        self.assertIn("var verifiedFile = new File(watchedPath);", source)
        self.assertIn("file.seek(Number(file.length) - 12, 0);", source)
        self.assertNotIn("file.seek(-12, 2);", source)
        self.assertIn("waitForStableFile(png, renderStarted, 120000, 250, 2000)", source)
        self.assertIn("stableForMs >= stableWindowMs && formatComplete", source)
        self.assertNotIn("stablePolls >= 2", source)
        self.assertNotIn("if (!file.seek", source)
        self.assertIn("verifiedSize === size && verifiedModified === modified", source)
        self.assertIn('summary.png_observation.status !== "stable"', source)
        self.assertIn("crc_validated", source)
        self.assertIn("could not remove stale PNG", source)
        self.assertIn("could not remove stale render-queue output", source)
        self.assertIn('outputMode === "png16_render_queue"', source)
        self.assertIn("/usr/bin/sips -s format png", source)
        self.assertIn("could not remove intermediate TIFF", source)
        runner_source = (ROOT / "scripts/run_ae_single_case.py").read_text(encoding="utf-8")
        self.assertIn("atomic_write_bytes(raw_result_json, b\"\", mode=0o600)", runner_source)
        self.assertIn("host_directory_snapshot = snapshot_directory_chains", runner_source)

    def test_batch_uses_same_png_completion_contract(self):
        source = (ROOT / "scripts/ae_pixel_validation_render.jsx").read_text(encoding="utf-8")
        self.assertIn("function hasCompletePngTrailer", source)
        self.assertIn("waitForStableFile(png, renderStarted, 120000, 250, 2000)", source)
        self.assertIn("stableForMs >= stableWindowMs && formatComplete", source)
        self.assertNotIn("stablePolls >= 2", source)
        self.assertNotIn("if (!file.seek", source)
        self.assertIn("verifiedSize === size && verifiedModified === modified", source)
        self.assertIn('if (observation.status !== "stable")', source)
        self.assertIn("summary.png_observations[caseSpec.id] = observation", source)
        self.assertIn("remove returned false or file still exists", source)

    def test_png_parser_requires_valid_crc_terminal_iend_and_no_trailing_bytes(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "case.png"
            cases = {
                "valid": (VALID_PNG, True),
                "missing_iend": (PNG_WITHOUT_IEND, False),
                "bad_crc": (VALID_PNG[:-1] + bytes([VALID_PNG[-1] ^ 1]), False),
                "trailing_byte": (VALID_PNG + b"x", False),
                "ihdr_not_first": (
                    single_case_runner.PNG_SIGNATURE + png_chunk(b"tEXt", b"x\x00y") + VALID_PNG[8:],
                    False,
                ),
                "noncontiguous_idat": (
                    single_case_runner.PNG_SIGNATURE
                    + PNG_IHDR
                    + png_chunk(b"IDAT", PNG_IDAT_PAYLOAD[:1])
                    + png_chunk(b"tEXt", b"x\x00y")
                    + png_chunk(b"IDAT", PNG_IDAT_PAYLOAD[1:])
                    + PNG_IEND,
                    False,
                ),
            }
            for label, (payload, expected) in cases.items():
                with self.subTest(label=label):
                    path.write_bytes(payload)
                    self.assertIs(single_case_runner.is_complete_png(path), expected)

    def test_png_parser_can_bind_leaf_to_a_trusted_parent_descriptor(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            output = root / "case.png"
            output.write_bytes(VALID_PNG)
            directory_descriptor = os.open(
                root,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
            )
            try:
                details = single_case_runner.inspect_complete_png(
                    Path("/untrusted/parent/case.png"),
                    dir_fd=directory_descriptor,
                )
            finally:
                os.close(directory_descriptor)

            self.assertIsNotNone(details)
            self.assertEqual(details["size_bytes"], len(VALID_PNG))
            self.assertEqual(
                details["sha256"],
                single_case_runner.inspect_complete_png(output)["sha256"],
            )

    def test_png_parser_rejects_invalid_ihdr_palette_critical_and_idat_structure(self):
        zero_width_ihdr = png_chunk(
            b"IHDR", b"\x00\x00\x00\x00\x00\x00\x00\x01\x08\x06\x00\x00\x00"
        )
        bad_compression_ihdr = png_chunk(
            b"IHDR", b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x01\x00\x00"
        )
        indexed_ihdr = png_chunk(
            b"IHDR", b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x03\x00\x00\x00"
        )
        indexed_idat = png_chunk(b"IDAT", zlib.compress(b"\x00\x00"))
        cases = {
            "zero_width": single_case_runner.PNG_SIGNATURE
            + zero_width_ihdr
            + png_chunk(b"IDAT", PNG_IDAT_PAYLOAD)
            + PNG_IEND,
            "bad_compression": single_case_runner.PNG_SIGNATURE
            + bad_compression_ihdr
            + png_chunk(b"IDAT", PNG_IDAT_PAYLOAD)
            + PNG_IEND,
            "plte_after_idat": single_case_runner.PNG_SIGNATURE
            + PNG_IHDR
            + png_chunk(b"IDAT", PNG_IDAT_PAYLOAD)
            + png_chunk(b"PLTE", b"\x00\x00\x00")
            + PNG_IEND,
            "indexed_without_plte": single_case_runner.PNG_SIGNATURE
            + indexed_ihdr
            + indexed_idat
            + PNG_IEND,
            "unknown_critical": single_case_runner.PNG_SIGNATURE
            + PNG_IHDR
            + png_chunk(b"ABCD", b"")
            + png_chunk(b"IDAT", PNG_IDAT_PAYLOAD)
            + PNG_IEND,
            "invalid_deflate": single_case_runner.PNG_SIGNATURE
            + PNG_IHDR
            + png_chunk(b"IDAT", b"not-a-zlib-stream")
            + PNG_IEND,
            "invalid_chunk_type": single_case_runner.PNG_SIGNATURE
            + PNG_IHDR
            + png_chunk(b"A1CD", b"")
            + png_chunk(b"IDAT", PNG_IDAT_PAYLOAD)
            + PNG_IEND,
        }
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "invalid.png"
            for label, payload in cases.items():
                with self.subTest(label=label):
                    path.write_bytes(payload)
                    self.assertIsNone(single_case_runner.inspect_complete_png(path))

    def test_same_inode_mutation_with_restored_mtime_fails_final_ctime_identity(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "case.png"
            path.write_bytes(VALID_PNG)
            original_inspector = single_case_runner.inspect_complete_png
            mutated = False

            def inspect_then_mutate(candidate: Path) -> dict[str, object] | None:
                nonlocal mutated
                details = original_inspector(candidate)
                if details is not None and not mutated:
                    before = candidate.stat()
                    candidate.write_bytes(VALID_PNG[:-1] + bytes([VALID_PNG[-1] ^ 1]))
                    os.utime(candidate, ns=(before.st_atime_ns, before.st_mtime_ns))
                    self.assertNotEqual(candidate.stat().st_ctime_ns, details["changed_ns"])
                    mutated = True
                return details

            with mock.patch.object(
                single_case_runner,
                "inspect_complete_png",
                side_effect=inspect_then_mutate,
            ):
                observation = single_case_runner.wait_for_complete_png(
                    path,
                    timeout_seconds=0.1,
                    stable_window_seconds=0.01,
                    poll_interval_seconds=0.005,
                )

            self.assertTrue(mutated)
            self.assertNotEqual(observation["status"], "stable")
            self.assertFalse(observation["crc_validated"])
            self.assertIsNone(original_inspector(path))

    def test_growth_plateau_does_not_become_stable_before_iend(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "case.png"
            path.write_bytes(PNG_STALLED_AT_IDAT_HEADER)
            final_write_done = threading.Event()

            def finish_png() -> None:
                time.sleep(0.15)
                with path.open("ab") as output:
                    output.write(PNG_IDAT_PAYLOAD + PNG_IDAT_CRC + PNG_IEND)
                    output.flush()
                    os.fsync(output.fileno())
                final_write_done.set()

            producer = threading.Thread(target=finish_png)
            producer.start()
            observation = single_case_runner.wait_for_complete_png(
                path,
                timeout_seconds=1.0,
                stable_window_seconds=0.04,
                poll_interval_seconds=0.01,
            )
            producer.join(timeout=1.0)
            self.assertTrue(final_write_done.is_set(), "waiter returned during the staged-write plateau")
            self.assertEqual(observation["status"], "stable")
            self.assertTrue(observation["format_complete"])
            self.assertTrue(observation["crc_validated"])
            self.assertEqual(observation["validation"], "png_chunks_crc_iend")
            self.assertEqual(observation["size_bytes"], len(VALID_PNG))
            self.assertGreaterEqual(observation["stable_for_ms"], 40)

    def test_stable_truncated_png_times_out_instead_of_passing(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "case.png"
            path.write_bytes(PNG_WITHOUT_IEND)
            observation = single_case_runner.wait_for_complete_png(
                path,
                timeout_seconds=0.08,
                stable_window_seconds=0.02,
                poll_interval_seconds=0.005,
            )
            self.assertEqual(observation["status"], "unstable")
            self.assertFalse(observation["format_complete"])
            self.assertFalse(observation["crc_validated"])

    def test_python_gate_authoritatively_replaces_js_png_observation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root, frame="case.png")
            output_dir = root / "output"
            output_dir.mkdir()
            path = output_dir / "case.png"
            path.write_bytes(VALID_PNG)
            result = {
                "kind": "olm_ae_single_case_result",
                "status": "ok",
                "request_dir": str(request_dir),
                "case_id": "case_0001",
                "output_dir": str(output_dir),
                "output_png": str(path),
                "output_exr": "",
                "png_observation": {"status": "stable", "size_bytes": 1},
            }
            binding = single_case_runner.build_expected_output_binding(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_dir,
                output_mode="png",
            )
            self.assertTrue(single_case_runner.validate_result_output(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                expected_binding=binding,
                timeout_seconds=1.0,
                stable_window_seconds=0.03,
                poll_interval_seconds=0.005,
            ))
            self.assertEqual(result["status"], "ok")
            self.assertIs(result["output_observation"], result["png_observation"])
            self.assertEqual(result["png_observation"]["size_bytes"], len(VALID_PNG))
            self.assertGreaterEqual(result["png_observation"]["stable_for_ms"], 30)
            self.assertTrue(result["png_observation"]["crc_validated"])
            self.assertEqual(result["output_binding_validation"]["status"], "matched")

    def test_expected_binding_rejects_fresh_valid_other_case_path_without_waiting(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_dir = root / "output"
            output_dir.mkdir()
            other_output = output_dir / "other_case.png"
            other_output.write_bytes(VALID_PNG)
            binding = single_case_runner.build_expected_output_binding(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_dir,
                output_mode="png",
            )
            result = {
                "kind": "olm_ae_single_case_result",
                "status": "ok",
                "request_dir": str(request_dir),
                "case_id": "case_0001",
                "output_dir": str(output_dir),
                "output_png": str(other_output),
                "output_exr": "",
            }

            with mock.patch.object(
                single_case_runner,
                "wait_for_stable_output",
                side_effect=AssertionError("binding mismatch must fail before stability wait"),
            ):
                self.assertTrue(single_case_runner.validate_result_output(
                    result,
                    not_before_ns=0,
                    expected_binding=binding,
                ))

            self.assertEqual(result["status"], "error")
            self.assertEqual(result["output_binding_validation"]["status"], "failed")
            self.assertIn("result output_png mismatch", result["error"])

    def test_expected_binding_derives_png_and_exr_leaves_from_invocation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root, frame="manifest_frame.png")
            output_dir = root / "output"
            output_dir.mkdir()

            png_binding = single_case_runner.build_expected_output_binding(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_dir,
                output_mode="png",
            )
            exr_binding = single_case_runner.build_expected_output_binding(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_dir,
                output_mode="exr_render_queue",
            )

            self.assertEqual(png_binding.output_path, output_dir / "manifest_frame.png")
            self.assertEqual(exr_binding.output_path, output_dir / "case_0001_00000.exr")

    def test_expected_binding_rejects_output_directory_inode_substitution(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_dir = root / "output"
            displaced_dir = root / "displaced"
            output_dir.mkdir()
            binding = single_case_runner.build_expected_output_binding(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_dir,
                output_mode="png",
            )
            output_dir.rename(displaced_dir)
            output_dir.mkdir()
            expected_output = output_dir / "case_0001.png"
            expected_output.write_bytes(VALID_PNG)
            result = {
                "kind": "olm_ae_single_case_result",
                "status": "ok",
                "request_dir": str(request_dir),
                "case_id": "case_0001",
                "output_dir": str(output_dir),
                "output_png": str(expected_output),
                "output_exr": "",
            }

            self.assertTrue(single_case_runner.validate_result_output(
                result,
                not_before_ns=0,
                expected_binding=binding,
            ))
            self.assertEqual(result["status"], "error")
            self.assertFalse(
                result["output_binding_validation"]["output_dir_identity_matches"]
            )

    def test_expected_binding_rejects_uri_active_paths_and_frame_names(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            output_dir = root / "output"
            output_dir.mkdir()
            request_dir = create_request_fixture(root, frame="case%20one.png")
            with self.assertRaisesRegex(ValueError, "portable ExtendScript leaf"):
                single_case_runner.build_expected_output_binding(
                    request_dir=request_dir,
                    case_id="case_0001",
                    output_dir=output_dir,
                    output_mode="png",
                )

        with tempfile.TemporaryDirectory(prefix="request%20alias_") as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_dir = root / "output"
            output_dir.mkdir()
            with self.assertRaisesRegex(ValueError, "URI/path-active"):
                single_case_runner.build_expected_output_binding(
                    request_dir=request_dir,
                    case_id="case_0001",
                    output_dir=output_dir,
                    output_mode="png",
                )

    def test_expected_binding_rejects_request_source_mutation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_dir = root / "output"
            output_dir.mkdir()
            output = output_dir / "case_0001.png"
            output.write_bytes(VALID_PNG)
            binding = single_case_runner.build_expected_output_binding(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_dir,
                output_mode="png",
            )
            result = {
                "kind": "olm_ae_single_case_result",
                "status": "ok",
                "request_dir": str(request_dir),
                "case_id": "case_0001",
                "output_dir": str(output_dir),
                "output_png": str(output),
                "output_exr": "",
            }
            manifest = request_dir / "request_manifest.json"
            original_stat = manifest.stat()
            manifest.write_bytes(manifest.read_bytes() + b" ")
            os.utime(manifest, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

            with mock.patch.object(
                single_case_runner,
                "wait_for_stable_output",
                side_effect=AssertionError("source mismatch must fail before stability wait"),
            ):
                self.assertTrue(single_case_runner.validate_result_output(
                    result,
                    not_before_ns=0,
                    expected_binding=binding,
                ))

            self.assertEqual(result["status"], "error")
            self.assertFalse(
                result["output_binding_validation"]["request_source_snapshot_matches"]
            )

    def test_expected_binding_rejects_case_spelling_alias(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_dir = root / "output"
            output_dir.mkdir()
            binding = single_case_runner.build_expected_output_binding(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_dir,
                output_mode="png",
            )
            output_dir.rename(root / "OUTPUT")

            result = {
                "kind": "olm_ae_single_case_result",
                "status": "ok",
                "request_dir": str(request_dir),
                "case_id": "case_0001",
                "output_dir": str(output_dir),
                "output_png": str(binding.output_path),
                "output_exr": "",
            }
            self.assertFalse(
                single_case_runner.validate_expected_output_binding(result, binding)
            )
            self.assertFalse(
                result["output_binding_validation"]["output_dir_identity_matches"]
            )

    def test_commit_revalidation_rejects_output_parent_swap_after_binding_check(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_dir = root / "output"
            displaced_dir = root / "displaced"
            output_dir.mkdir()
            output = output_dir / "case_0001.png"
            output.write_bytes(VALID_PNG)
            binding = single_case_runner.build_expected_output_binding(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_dir,
                output_mode="png",
            )
            result = {
                "kind": "olm_ae_single_case_result",
                "status": "ok",
                "request_dir": str(request_dir),
                "case_id": "case_0001",
                "output_dir": str(output_dir),
                "output_png": str(output),
                "output_exr": "",
            }
            self.assertTrue(single_case_runner.validate_result_output(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                expected_binding=binding,
                timeout_seconds=1.0,
                stable_window_seconds=0.02,
                poll_interval_seconds=0.005,
            ))
            original_inspector = single_case_runner.inspect_complete_png
            swapped = False

            def inspect_then_swap(
                candidate: Path,
                *,
                dir_fd: int | None = None,
            ) -> dict[str, object] | None:
                nonlocal swapped
                details = original_inspector(candidate, dir_fd=dir_fd)
                if not swapped:
                    output_dir.rename(displaced_dir)
                    output_dir.symlink_to(displaced_dir, target_is_directory=True)
                    swapped = True
                return details

            with mock.patch.object(
                single_case_runner,
                "inspect_complete_png",
                side_effect=inspect_then_swap,
            ):
                self.assertFalse(single_case_runner.revalidate_result_output_for_commit(
                    result,
                    expected_binding=binding,
                ))

            self.assertTrue(swapped)
            self.assertEqual(result["status"], "error")
            self.assertFalse(
                result["output_commit_revalidation"]["parent_mapping_matches"]
            )

    def test_commit_revalidation_rejects_case_alias_output_leaf(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_dir = root / "output"
            output_dir.mkdir()
            binding = single_case_runner.build_expected_output_binding(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_dir,
                output_mode="exr_render_queue",
            )
            aliased_output = output_dir / "CASE_0001_00000.EXR"
            aliased_output.write_bytes(b"\x76\x2f\x31\x01payload")
            details = single_case_runner.inspect_readable_nonempty_file(aliased_output)
            result = {
                "kind": "olm_ae_single_case_result",
                "status": "ok",
                "request_dir": str(request_dir),
                "case_id": "case_0001",
                "output_dir": str(output_dir),
                "output_png": "",
                "output_exr": str(binding.output_path),
                "output_observation": {
                    "status": "stable",
                    "output_kind": "exr",
                    **details,
                },
            }

            self.assertFalse(single_case_runner.revalidate_result_output_for_commit(
                result,
                expected_binding=binding,
            ))
            self.assertEqual(result["status"], "error")
            self.assertFalse(
                result["output_commit_revalidation"]["leaf_spelling_matches"]
            )

    def test_bound_result_commit_downgrades_output_mutated_during_json_write(self):
        self.assertEqual(len(ALTERNATE_VALID_PNG), len(VALID_PNG))
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_dir = root / "output"
            output_dir.mkdir()
            output = output_dir / "case_0001.png"
            result_json = output_dir / "AE_SINGLE_CASE_RESULT.json"
            output.write_bytes(VALID_PNG)
            binding = single_case_runner.build_expected_output_binding(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_dir,
                output_mode="png",
            )
            result = {
                "kind": "olm_ae_single_case_result",
                "status": "ok",
                "request_dir": str(request_dir),
                "case_id": "case_0001",
                "output_dir": str(output_dir),
                "output_png": str(output),
                "output_exr": "",
            }
            self.assertTrue(single_case_runner.validate_result_output(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                expected_binding=binding,
                timeout_seconds=1.0,
                stable_window_seconds=0.02,
                poll_interval_seconds=0.005,
            ))
            original_writer = single_case_runner.write_result_json
            writes = 0

            def write_then_mutate(
                path: Path,
                payload: dict[str, object],
                *,
                parent_dir_fd: int | None = None,
            ) -> bytes:
                nonlocal writes
                exact = original_writer(
                    path,
                    payload,
                    parent_dir_fd=parent_dir_fd,
                )
                writes += 1
                if writes == 1:
                    before = output.stat()
                    output.write_bytes(ALTERNATE_VALID_PNG)
                    os.utime(output, ns=(before.st_atime_ns, before.st_mtime_ns))
                return exact

            with mock.patch.object(
                single_case_runner,
                "write_result_json",
                side_effect=write_then_mutate,
            ):
                self.assertFalse(single_case_runner.commit_bound_result_json(
                    result_json,
                    result,
                    binding,
                ))

            committed = json.loads(result_json.read_text(encoding="utf-8"))
            self.assertGreaterEqual(writes, 2)
            self.assertEqual(committed["status"], "error")
            self.assertEqual(
                committed["output_commit_revalidation"]["status"],
                "failed",
            )

    def test_bound_result_commit_downgrades_source_mutated_during_json_write(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_dir = root / "output"
            output_dir.mkdir()
            output = output_dir / "case_0001.png"
            result_json = output_dir / "AE_SINGLE_CASE_RESULT.json"
            output.write_bytes(VALID_PNG)
            binding = single_case_runner.build_expected_output_binding(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_dir,
                output_mode="png",
            )
            result = {
                "kind": "olm_ae_single_case_result",
                "status": "ok",
                "request_dir": str(request_dir),
                "case_id": "case_0001",
                "output_dir": str(output_dir),
                "output_png": str(output),
                "output_exr": "",
            }
            self.assertTrue(single_case_runner.validate_result_output(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                expected_binding=binding,
                timeout_seconds=1.0,
                stable_window_seconds=0.02,
                poll_interval_seconds=0.005,
            ))
            original_writer = single_case_runner.write_result_json
            reference = request_dir / "reference_manifest.json"
            writes = 0

            def write_then_mutate(
                path: Path,
                payload: dict[str, object],
                *,
                parent_dir_fd: int | None = None,
            ) -> bytes:
                nonlocal writes
                exact = original_writer(
                    path,
                    payload,
                    parent_dir_fd=parent_dir_fd,
                )
                writes += 1
                if writes == 1:
                    before = reference.stat()
                    reference.write_bytes(reference.read_bytes() + b" ")
                    os.utime(reference, ns=(before.st_atime_ns, before.st_mtime_ns))
                return exact

            with mock.patch.object(
                single_case_runner,
                "write_result_json",
                side_effect=write_then_mutate,
            ):
                self.assertFalse(single_case_runner.commit_bound_result_json(
                    result_json,
                    result,
                    binding,
                ))

            committed = json.loads(result_json.read_text(encoding="utf-8"))
            self.assertGreaterEqual(writes, 2)
            self.assertEqual(committed["status"], "error")
            self.assertFalse(
                committed["output_binding_validation"]["request_source_snapshot_matches"]
            )

    def test_commit_revalidation_rejects_png_mutated_after_stable_observation(self):
        self.assertEqual(len(ALTERNATE_VALID_PNG), len(VALID_PNG))
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            output = root / "case.png"
            result_json = root / "result.json"
            output.write_bytes(VALID_PNG)
            result = {"status": "ok", "output_png": str(output), "output_exr": ""}
            self.assertTrue(single_case_runner.validate_result_output(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                timeout_seconds=1.0,
                stable_window_seconds=0.02,
                poll_interval_seconds=0.005,
            ))
            self.assertEqual(result["status"], "ok")
            observed_sha = result["output_observation"]["sha256"]
            observed_stat = output.stat()

            output.write_bytes(ALTERNATE_VALID_PNG)
            os.utime(output, ns=(observed_stat.st_atime_ns, observed_stat.st_mtime_ns))
            self.assertNotEqual(
                single_case_runner.inspect_complete_png(output)["sha256"],
                observed_sha,
            )

            self.assertFalse(single_case_runner.revalidate_result_output_for_commit(result))
            single_case_runner.write_result_json(result_json, result)
            committed = json.loads(result_json.read_text(encoding="utf-8"))
            self.assertEqual(committed["status"], "error")
            self.assertEqual(committed["output_commit_revalidation"]["status"], "failed")
            self.assertIn("changed after stable observation", committed["error"])

    def test_commit_revalidation_binds_readable_exr_identity(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "frame.exr"
            output.write_bytes(b"\x76\x2f\x31\x01payload")
            result = {"status": "ok", "output_png": "", "output_exr": str(output)}
            self.assertTrue(single_case_runner.validate_result_output(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                timeout_seconds=1.0,
                stable_window_seconds=0.02,
                poll_interval_seconds=0.005,
            ))

            self.assertTrue(single_case_runner.revalidate_result_output_for_commit(result))
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["output_commit_revalidation"]["status"], "matched")
            self.assertEqual(
                result["output_commit_revalidation"]["validation"],
                "exr_magic_sha256_identity",
            )

    def test_commit_revalidation_rejects_post_parse_png_symlink_swap(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            output = root / "case.png"
            moved = root / "moved.png"
            output.write_bytes(VALID_PNG)
            result = {"status": "ok", "output_png": str(output), "output_exr": ""}
            self.assertTrue(single_case_runner.validate_result_output(
                result,
                not_before_ns=time.time_ns() - 1_000_000_000,
                timeout_seconds=1.0,
                stable_window_seconds=0.02,
                poll_interval_seconds=0.005,
            ))
            original_inspector = single_case_runner.inspect_complete_png

            def inspect_then_swap(candidate: Path) -> dict[str, object] | None:
                details = original_inspector(candidate)
                candidate.rename(moved)
                candidate.symlink_to(moved)
                return details

            with mock.patch.object(
                single_case_runner,
                "inspect_complete_png",
                side_effect=inspect_then_swap,
            ):
                self.assertFalse(single_case_runner.revalidate_result_output_for_commit(result))

            self.assertEqual(result["status"], "error")
            self.assertFalse(
                result["output_commit_revalidation"]["path_identity_matches"]
            )

    def test_stale_nonzero_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "stale.exr"
            path.write_bytes(b"\x76\x2f\x31\x01stale")
            old_ns = time.time_ns() - 10_000_000_000
            os.utime(path, ns=(old_ns, old_ns))
            observation = single_case_runner.wait_for_stable_output(
                path,
                output_kind="exr",
                not_before_ns=time.time_ns(),
                timeout_seconds=0.05,
                stable_window_seconds=0.01,
                poll_interval_seconds=0.005,
            )
            self.assertEqual(observation["status"], "stale")
            self.assertFalse(observation["fresh"])

    def test_exr_uses_fresh_quiet_gate_without_png_rules(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "frame.exr"
            path.write_bytes(b"\x76\x2f\x31\x01payload-without-iend")
            result = {"status": "ok", "output_png": "", "output_exr": str(path)}
            with mock.patch.object(single_case_runner, "is_complete_png", side_effect=AssertionError("PNG-only rule")):
                self.assertTrue(single_case_runner.validate_result_output(
                    result,
                    not_before_ns=time.time_ns() - 1_000_000_000,
                    timeout_seconds=1.0,
                    stable_window_seconds=0.03,
                    poll_interval_seconds=0.005,
                ))
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["output_observation"]["output_kind"], "exr")
            self.assertTrue(result["output_observation"]["readable"])
            self.assertIsNone(result["output_observation"]["format_complete"])
            self.assertFalse(result["output_observation"]["crc_validated"])
            self.assertEqual(result["output_observation"]["validation"], "exr_magic_sha256")

    def test_exr_hardlink_never_becomes_a_valid_stable_artifact(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            output = root / "frame.exr"
            alias = root / "frame_alias.exr"
            output.write_bytes(single_case_runner.EXR_MAGIC + b"payload")
            os.link(output, alias)

            self.assertIsNone(single_case_runner.inspect_readable_nonempty_file(output))
            observation = single_case_runner.wait_for_stable_output(
                output,
                output_kind="exr",
                not_before_ns=0,
                timeout_seconds=0.06,
                stable_window_seconds=0.01,
                poll_interval_seconds=0.005,
            )

            self.assertEqual(observation["status"], "unstable")
            self.assertFalse(observation["readable"])
            self.assertEqual(observation["link_count"], 2)

    def test_staged_capsule_remains_host_input_after_origin_ancestor_substitution(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_container = root / "output"
            output_container.mkdir()
            run_id, run_dir = single_case_runner.create_single_run_directory(
                output_container
            )
            del run_id
            for leaf in ("runtime", "raw_output", "validated_output", "publication"):
                os.mkdir(run_dir / leaf, 0o700)
            origin_binding = single_case_runner.build_expected_output_binding(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=run_dir / "raw_output",
                output_mode="png",
            )
            staged_request = single_case_runner.stage_request_sources(
                origin_binding,
                run_dir,
            )
            staged_binding = single_case_runner.build_expected_output_binding(
                request_dir=staged_request,
                case_id="case_0001",
                output_dir=run_dir / "raw_output",
                output_mode="png",
            )
            wrapper = single_case_runner.build_single_case_wrapper_js(
                request_dir=staged_request,
                case_id="case_0001",
                output_dir=run_dir / "raw_output",
                log_path=run_dir / "raw_output" / "AE_SINGLE_CASE.log",
                result_json=run_dir / "raw_output" / "AE_SINGLE_CASE_RESULT.json",
                jsx_path=ROOT / "scripts" / "ae_render_single_case.jsx",
                overrides={},
                ae_env={},
                output_mode="png",
                output_template="",
                keep_open=False,
            )
            displaced = root / "request_original"
            request_dir.rename(displaced)
            decoy_root = root / "decoy"
            decoy_request = create_request_fixture(decoy_root)
            decoy_request.rename(request_dir)
            try:
                self.assertIn(
                    f"$.setenv('OLM_AE_REQUEST_DIR', {json.dumps(str(staged_request))});",
                    wrapper,
                )
                self.assertNotIn(
                    f"$.setenv('OLM_AE_REQUEST_DIR', {json.dumps(str(request_dir))});",
                    wrapper,
                )
                self.assertTrue(
                    single_case_runner.source_snapshot_matches(
                        staged_binding.source_snapshot
                    )
                )
            finally:
                request_dir.rename(decoy_root / "consumed_decoy")
                displaced.rename(request_dir)

    def test_main_uses_nested_run_files_and_does_not_follow_top_level_wrapper_symlink(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_container = root / "output"
            output_container.mkdir()
            victim = root / "victim.txt"
            victim.write_text("keep me\n", encoding="utf-8")
            top_level_wrapper = output_container / "AE_SINGLE_CASE_WRAPPER.jsx"
            top_level_wrapper.symlink_to(victim)
            lock_path = root / "single.lock"
            args = types.SimpleNamespace(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_container,
                app_name="Fake After Effects",
                output_mode="png",
                output_template="",
                keep_open=False,
                timeout=1,
                param_override=[],
                ae_env=[],
                lock_path=lock_path,
                dump_js=None,
            )
            original_wait = single_case_runner.wait_for_stable_output

            def fast_wait(path: Path, **kwargs: object) -> dict[str, object]:
                kwargs["stable_window_seconds"] = 0.02
                kwargs["poll_interval_seconds"] = 0.005
                return original_wait(path, **kwargs)

            def fake_host(*_args: object, **_kwargs: object) -> object:
                runs = list(output_container.glob("single_run_*"))
                self.assertEqual(len(runs), 1)
                run_dir = runs[0]
                staged_request = run_dir / "source_capsule" / "staged_request"
                raw_output = run_dir / "raw_output"
                staged_program = (
                    run_dir / "runtime" / single_case_runner.RUNTIME_PROGRAM_LEAF
                )
                wrapper_path = (
                    run_dir / "runtime" / single_case_runner.RUNTIME_WRAPPER_LEAF
                )
                wrapper_text = wrapper_path.read_text(encoding="utf-8")
                self.assertEqual(
                    staged_program.read_bytes(),
                    (ROOT / "scripts" / "ae_render_single_case.jsx").read_bytes(),
                )
                self.assertIn(
                    f"$.evalFile(new File({json.dumps(str(staged_program))}));",
                    wrapper_text,
                )
                self.assertNotIn(
                    f"$.evalFile(new File({json.dumps(str(ROOT / 'scripts' / 'ae_render_single_case.jsx'))}));",
                    wrapper_text,
                )
                self.assertIn(json.dumps(str(staged_request)), wrapper_text)
                self.assertNotIn(
                    f"$.setenv('OLM_AE_REQUEST_DIR', {json.dumps(str(request_dir))});",
                    wrapper_text,
                )
                (raw_output / "case_0001.png").write_bytes(VALID_PNG)
                with (raw_output / "AE_SINGLE_CASE.log").open("a", encoding="utf-8") as log:
                    log.write("fake host\n")
                (raw_output / "AE_SINGLE_CASE_RESULT.json").write_text(
                    json.dumps({
                        "kind": "olm_ae_single_case_result",
                        "status": "ok",
                        "request_dir": str(staged_request),
                        "case_id": "case_0001",
                        "output_dir": str(raw_output),
                        "output_png": str(raw_output / "case_0001.png"),
                        "output_exr": "",
                    }),
                    encoding="utf-8",
                )
                return types.SimpleNamespace(stdout="", stderr="", returncode=0)

            with (
                mock.patch.object(single_case_runner, "parse_args", return_value=args),
                mock.patch.object(single_case_runner.subprocess, "run", side_effect=fake_host),
                mock.patch.object(
                    single_case_runner,
                    "wait_for_stable_output",
                    side_effect=fast_wait,
                ),
            ):
                self.assertEqual(single_case_runner.main(), 0)

            self.assertEqual(victim.read_text(encoding="utf-8"), "keep me\n")
            self.assertTrue(top_level_wrapper.is_symlink())
            run_dir = next(output_container.glob("single_run_*"))
            nested_wrapper = run_dir / "runtime" / "AE_SINGLE_CASE_WRAPPER.jsx"
            self.assertTrue(nested_wrapper.is_file())
            self.assertFalse(nested_wrapper.is_symlink())
            result_path = run_dir / "publication" / "AE_SINGLE_CASE_RESULT.json"
            commit_path = run_dir / "publication" / "AE_SINGLE_CASE_COMMIT.json"
            committed_result = json.loads(result_path.read_text(encoding="utf-8"))
            commit_bytes = commit_path.read_bytes()
            self.assertEqual(committed_result["status"], "ok")
            self.assertEqual(committed_result["invocation_request_dir"], str(request_dir))
            self.assertIs(
                committed_result["invocation_request_dir_provenance_only"],
                True,
            )
            self.assertEqual(
                committed_result["host_request_dir"],
                str(run_dir / "source_capsule" / "staged_request"),
            )
            self.assertEqual(
                committed_result["request_dir"],
                str(run_dir / "source_capsule" / "staged_request"),
            )
            committed_marker = json.loads(commit_path.read_text(encoding="utf-8"))
            self.assertEqual(len(committed_marker["runtime_sources"]), 2)
            verification = single_case_runner.verify_single_case_commit(
                commit_path,
                expected_run_id=committed_result["run_id"],
                expected_commit_sha256=hashlib.sha256(commit_bytes).hexdigest(),
                expected_commit_bytes=commit_bytes,
            )
            self.assertEqual(verification["status"], "passed", verification)
            self.assertFalse(single_case_runner.ae_active_marker_path(lock_path).exists())

    def test_runner_owned_ae_environment_bindings_cannot_be_overridden(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_container = root / "output"
            for reserved_key in sorted(
                single_case_runner.RUNNER_OWNED_AE_ENV_KEYS
            ):
                with self.subTest(reserved_key=reserved_key):
                    args = types.SimpleNamespace(
                        request_dir=request_dir,
                        case_id="case_0001",
                        output_dir=output_container,
                        app_name="Fake After Effects",
                        output_mode="png",
                        output_template="",
                        keep_open=False,
                        timeout=1,
                        param_override=[],
                        ae_env=[f"{reserved_key}=/tmp/redirected"],
                        lock_path=root / "single.lock",
                        dump_js=None,
                    )
                    with (
                        mock.patch.object(
                            single_case_runner,
                            "parse_args",
                            return_value=args,
                        ),
                        mock.patch.object(
                            single_case_runner.subprocess,
                            "run",
                            side_effect=AssertionError(
                                "reserved environment must fail before host invocation"
                            ),
                        ),
                    ):
                        self.assertEqual(single_case_runner.main(), 1)
                    self.assertFalse(any(output_container.glob("single_run_*")))

            with self.assertRaisesRegex(ValueError, "runner-owned AE environment"):
                single_case_runner.build_single_case_wrapper_js(
                    request_dir=request_dir,
                    case_id="case_0001",
                    output_dir=output_container,
                    log_path=output_container / "log",
                    result_json=output_container / "result.json",
                    jsx_path=ROOT / "scripts" / "ae_render_single_case.jsx",
                    overrides={},
                    ae_env={"OLM_AE_REQUEST_DIR": "/tmp/redirected"},
                    output_mode="png",
                    output_template="",
                    keep_open=False,
                )

            allowed_wrapper = single_case_runner.build_single_case_wrapper_js(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_container,
                log_path=output_container / "log",
                result_json=output_container / "result.json",
                jsx_path=ROOT / "scripts" / "ae_render_single_case.jsx",
                overrides={},
                ae_env={"OLM_AE_INPUT_FILE_OVERRIDE": "alternate.png"},
                output_mode="png",
                output_template="",
                keep_open=False,
            )
            self.assertIn("OLM_AE_INPUT_FILE_OVERRIDE", allowed_wrapper)

    def test_main_rejects_same_inode_runtime_source_mutation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            for runtime_leaf in (
                single_case_runner.RUNTIME_PROGRAM_LEAF,
                single_case_runner.RUNTIME_WRAPPER_LEAF,
            ):
                with self.subTest(runtime_leaf=runtime_leaf):
                    case_root = root / runtime_leaf.replace(".", "_")
                    case_root.mkdir()
                    request_dir = create_request_fixture(case_root)
                    output_container = case_root / "output"
                    lock_path = case_root / "single.lock"
                    args = types.SimpleNamespace(
                        request_dir=request_dir,
                        case_id="case_0001",
                        output_dir=output_container,
                        app_name="Fake After Effects",
                        output_mode="png",
                        output_template="",
                        keep_open=False,
                        timeout=1,
                        param_override=[],
                        ae_env=[],
                        lock_path=lock_path,
                        dump_js=None,
                    )

                    def mutate_runtime(*_args: object, **_kwargs: object) -> object:
                        run_dir = next(output_container.glob("single_run_*"))
                        target = run_dir / "runtime" / runtime_leaf
                        before = target.lstat()
                        payload = bytearray(target.read_bytes())
                        self.assertTrue(payload)
                        payload[0] ^= 1
                        target.chmod(0o644)
                        target.write_bytes(payload)
                        target.chmod(0o444)
                        after = target.lstat()
                        self.assertEqual(
                            (before.st_dev, before.st_ino),
                            (after.st_dev, after.st_ino),
                        )
                        return types.SimpleNamespace(
                            stdout="",
                            stderr="",
                            returncode=0,
                        )

                    with (
                        mock.patch.object(
                            single_case_runner,
                            "parse_args",
                            return_value=args,
                        ),
                        mock.patch.object(
                            single_case_runner.subprocess,
                            "run",
                            side_effect=mutate_runtime,
                        ),
                    ):
                        self.assertEqual(single_case_runner.main(), 1)
                    self.assertFalse(
                        single_case_runner.ae_active_marker_path(lock_path).exists()
                    )

    def test_consumer_reverification_rejects_post_publication_output_mutation(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture = publish_valid_png_fixture(Path(raw))
            commit_path = fixture["commit_path"]
            result_path = fixture["result_path"]
            validated_output = fixture["validated_output"]
            static_result = json.loads(result_path.read_text(encoding="utf-8"))
            static_commit = json.loads(commit_path.read_text(encoding="utf-8"))
            self.assertEqual(static_result["status"], "ok")
            self.assertIs(static_result["static_status_is_authoritative"], False)
            self.assertEqual(static_commit["status"], "passed")

            validated_output.chmod(0o644)
            validated_output.write_bytes(ALTERNATE_VALID_PNG)
            verification = single_case_runner.verify_single_case_commit(
                commit_path,
                expected_run_id=fixture["run_id"],
                expected_commit_sha256=fixture["commit_sha256"],
                expected_commit_bytes=fixture["commit_bytes"],
            )

            self.assertEqual(verification["status"], "failed")
            self.assertTrue(
                any("validated output" in error for error in verification["errors"]),
                verification,
            )

    def test_consumer_rejects_same_inode_runtime_source_mutation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            for runtime_leaf in (
                single_case_runner.RUNTIME_PROGRAM_LEAF,
                single_case_runner.RUNTIME_WRAPPER_LEAF,
            ):
                with self.subTest(runtime_leaf=runtime_leaf):
                    case_root = root / runtime_leaf.replace(".", "_")
                    case_root.mkdir()
                    fixture = publish_valid_png_fixture(case_root)
                    target = fixture["run_dir"] / "runtime" / runtime_leaf
                    before = target.lstat()
                    payload = bytearray(target.read_bytes())
                    payload[-1] ^= 1
                    target.chmod(0o644)
                    target.write_bytes(payload)
                    target.chmod(0o444)
                    after = target.lstat()
                    self.assertEqual(
                        (before.st_dev, before.st_ino),
                        (after.st_dev, after.st_ino),
                    )

                    verification = single_case_runner.verify_single_case_commit(
                        fixture["commit_path"],
                        expected_run_id=fixture["run_id"],
                        expected_commit_sha256=fixture["commit_sha256"],
                        expected_commit_bytes=fixture["commit_bytes"],
                    )

                    self.assertEqual(verification["status"], "failed")
                    self.assertTrue(
                        any(
                            "runtime source" in error
                            for error in verification["errors"]
                        ),
                        verification,
                    )

    def test_runtime_source_comparison_allows_only_ctime_drift(self):
        source = single_case_runner.BoundSource(
            Path("/tmp/runtime.jsx"), "a" * 64, 1, 2, 3, 4, 5, 1
        )
        ctime_only = source._replace(changed_ns=6)
        content_changed = source._replace(sha256="b" * 64, changed_ns=6)

        self.assertTrue(
            single_case_runner.runtime_source_snapshots_match(
                (source,), (ctime_only,)
            )
        )
        self.assertFalse(
            single_case_runner.runtime_source_snapshots_match(
                (source,), (content_changed,)
            )
        )

    def test_consumer_rejects_coordinated_semantically_invalid_result_rewrite(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture = publish_valid_png_fixture(Path(raw))
            result_path = fixture["result_path"]
            commit_path = fixture["commit_path"]
            result = json.loads(result_path.read_text(encoding="utf-8"))
            result["kind"] = "forged-result-kind"
            result["consumer_verifier"] = "forged-verifier"
            result["request_dir"] = str(fixture["request_dir"])
            result["host_request_dir"] = str(fixture["request_dir"])
            result["invocation_request_dir"] = "/tmp/../forged-request"
            result["raw_output_path"] = str(
                fixture["run_dir"] / "raw_output" / "case_0001.png"
            )
            for artifact_field in (
                "validated_output",
                "output_observation",
                "png_observation",
            ):
                result[artifact_field]["sha256"] = "0" * 64
                result[artifact_field]["unexpected_claim"] = True
            single_case_runner.write_result_json(result_path, result)
            _, result_source = single_case_runner.read_bound_source(result_path)

            commit = json.loads(commit_path.read_text(encoding="utf-8"))
            commit["result"] = single_case_runner._bound_source_payload(result_source)
            commit["invocation_request_dir"] = "/tmp/../forged-request"
            commit["validated_output"]["sha256"] = "0" * 64
            commit["validated_output"]["unexpected_claim"] = True
            forged_commit_bytes = single_case_runner.write_result_json(
                commit_path,
                commit,
            )
            verification = single_case_runner.verify_single_case_commit(
                commit_path,
                expected_run_id=fixture["run_id"],
                expected_commit_sha256=hashlib.sha256(forged_commit_bytes).hexdigest(),
                expected_commit_bytes=forged_commit_bytes,
            )

            self.assertEqual(verification["status"], "failed")
            joined_errors = "\n".join(verification["errors"])
            self.assertIn("result kind mismatch", joined_errors)
            self.assertIn("result consumer verifier mismatch", joined_errors)
            self.assertIn("result host request path mismatch", joined_errors)
            self.assertIn("invocation request provenance mismatch", joined_errors)
            self.assertIn("unauthoritative raw field", joined_errors)
            self.assertIn("validated output identity/structure/digest mismatch", joined_errors)
            self.assertIn("PNG observation differs", joined_errors)

    def test_consumer_allows_unrelated_sibling_run_but_rejects_container_replacement(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture = publish_valid_png_fixture(Path(raw))
            output_container = fixture["run_dir"].parent
            (output_container / "single_run_unrelated").mkdir()
            verification = single_case_runner.verify_single_case_commit(
                fixture["commit_path"],
                expected_run_id=fixture["run_id"],
                expected_commit_sha256=fixture["commit_sha256"],
                expected_commit_bytes=fixture["commit_bytes"],
            )
            self.assertEqual(verification["status"], "passed", verification)

            displaced = output_container.with_name("output_displaced")
            output_container.rename(displaced)
            output_container.mkdir()
            replaced_verification = single_case_runner.verify_single_case_commit(
                fixture["commit_path"],
                expected_run_id=fixture["run_id"],
                expected_commit_sha256=fixture["commit_sha256"],
                expected_commit_bytes=fixture["commit_bytes"],
            )
            self.assertEqual(replaced_verification["status"], "failed")

    def test_consumer_rejects_commit_path_redirection_and_duplicate_sources(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture = publish_valid_png_fixture(Path(raw))
            commit_path = fixture["commit_path"]
            commit = json.loads(commit_path.read_text(encoding="utf-8"))
            outside = fixture["run_dir"].parent / "outside"
            outside.mkdir()
            commit["result"]["path"] = str(outside / "forged_result.json")
            commit["validated_output"]["path"] = str(outside / "forged.png")
            commit["staged_sources"][0]["path"] = str(outside / "request_manifest.json")
            commit["staged_sources"].append(dict(commit["staged_sources"][1]))
            forged_bytes = single_case_runner.write_result_json(commit_path, commit)
            verification = single_case_runner.verify_single_case_commit(
                commit_path,
                expected_run_id=fixture["run_id"],
                expected_commit_sha256=hashlib.sha256(forged_bytes).hexdigest(),
                expected_commit_bytes=forged_bytes,
            )

            self.assertEqual(verification["status"], "failed")
            self.assertTrue(
                any("fixed result leaf" in error for error in verification["errors"]),
                verification,
            )
            self.assertTrue(
                any("staged source set mismatch" in error for error in verification["errors"]),
                verification,
            )

    def test_consumer_rejects_commit_argument_under_nonpublication_parent(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture = publish_valid_png_fixture(Path(raw))
            forged_argument = (
                fixture["run_dir"]
                / "NOT_PUBLICATION"
                / "AE_SINGLE_CASE_COMMIT.json"
            )
            verification = single_case_runner.verify_single_case_commit(
                forged_argument,
                expected_run_id=fixture["run_id"],
                expected_commit_sha256=fixture["commit_sha256"],
                expected_commit_bytes=fixture["commit_bytes"],
            )

            self.assertEqual(verification["status"], "failed")
            self.assertTrue(
                any("fixed publication leaf" in error for error in verification["errors"]),
                verification,
            )

    def test_consumer_rejects_ancestor_alias_even_when_it_targets_the_real_run(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            fixture = publish_valid_png_fixture(root / "real")
            aliased_container = root / "aliased-output"
            aliased_container.symlink_to(fixture["run_dir"].parent)
            aliased_commit = (
                aliased_container
                / fixture["run_dir"].name
                / "publication"
                / "AE_SINGLE_CASE_COMMIT.json"
            )
            self.assertTrue(aliased_commit.exists())

            verification = single_case_runner.verify_single_case_commit(
                aliased_commit,
                expected_run_id=fixture["run_id"],
                expected_commit_sha256=fixture["commit_sha256"],
                expected_commit_bytes=fixture["commit_bytes"],
            )

            self.assertEqual(verification["status"], "failed")
            self.assertTrue(
                any(
                    "fixed publication leaf" in error or "alias" in error
                    for error in verification["errors"]
                ),
                verification,
            )

    def test_consumer_rejects_forged_committed_directory_map(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture = publish_valid_png_fixture(Path(raw))
            commit_path = fixture["commit_path"]
            commit = json.loads(commit_path.read_text(encoding="utf-8"))
            output_container = commit["directories"]["output_container"]
            output_container["path"] = str(fixture["run_dir"] / "outside")
            output_container["device"] += 1
            forged_bytes = single_case_runner.write_result_json(commit_path, commit)
            verification = single_case_runner.verify_single_case_commit(
                commit_path,
                expected_run_id=fixture["run_id"],
                expected_commit_sha256=hashlib.sha256(forged_bytes).hexdigest(),
                expected_commit_bytes=forged_bytes,
            )

            self.assertEqual(verification["status"], "failed")
            self.assertTrue(
                any(
                    "output_container directory identity mismatch" in error
                    for error in verification["errors"]
                ),
                verification,
            )

    def test_consumer_rejects_noncanonical_scalar_types_and_ancestor_fields(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture = publish_valid_png_fixture(Path(raw))
            commit_path = fixture["commit_path"]
            commit = json.loads(commit_path.read_text(encoding="utf-8"))
            commit["staged_sources"][0]["link_count"] = True
            commit["validated_output"]["link_count"] = True
            commit["validated_output"]["identity_bound"] = 1
            commit["directories"]["runtime"]["link_count"] = True
            ancestor_entries = [
                entry
                for entry in commit["directory_chain_snapshot"].values()
                if set(entry) == {"path", "device", "inode"}
            ]
            self.assertTrue(ancestor_entries)
            ancestor_entries[0]["modified_ns"] = 0
            forged_bytes = single_case_runner.write_result_json(commit_path, commit)
            verification = single_case_runner.verify_single_case_commit(
                commit_path,
                expected_run_id=fixture["run_id"],
                expected_commit_sha256=hashlib.sha256(forged_bytes).hexdigest(),
                expected_commit_bytes=forged_bytes,
            )

            self.assertEqual(verification["status"], "failed")
            joined_errors = "\n".join(verification["errors"])
            self.assertIn("staged source identity mismatch", joined_errors)
            self.assertIn("validated output identity/structure/digest mismatch", joined_errors)
            self.assertIn("committed runtime directory identity mismatch", joined_errors)
            self.assertIn("committed directory chain identity mismatch", joined_errors)

            runtime_path = fixture["run_dir"] / "runtime"
            canonical_directory = single_case_runner._directory_payload(runtime_path)
            canonical_directory["link_count"] = 1
            boolean_alias = dict(canonical_directory)
            boolean_alias["link_count"] = True
            with mock.patch.object(
                single_case_runner,
                "_directory_payload",
                return_value=canonical_directory,
            ):
                self.assertFalse(
                    single_case_runner._directory_matches_entry(
                        runtime_path,
                        boolean_alias,
                    )
                )

    def test_every_allowed_control_environment_is_reset_between_wrappers(self):
        jsx_source = (ROOT / "scripts/ae_render_single_case.jsx").read_text(
            encoding="utf-8"
        )
        jsx_environment_keys = set(
            re.findall(r'getenv\("([A-Z0-9_]+)"\)', jsx_source)
        )
        covered_keys = (
            set(single_case_runner.RUNNER_OWNED_AE_ENV_KEYS)
            | set(single_case_runner.VOLATILE_AE_ENV_KEYS)
        )
        self.assertLessEqual(jsx_environment_keys, covered_keys)

        allowed_controls = {
            key: f"first-run-value-{index}"
            for index, key in enumerate(single_case_runner.VOLATILE_AE_ENV_KEYS)
        }
        common = {
            "request_dir": Path("/tmp/request"),
            "case_id": "case_0001",
            "output_dir": Path("/tmp/output"),
            "log_path": Path("/tmp/output/log"),
            "result_json": Path("/tmp/output/result.json"),
            "jsx_path": ROOT / "scripts" / "ae_render_single_case.jsx",
            "overrides": {},
            "output_mode": "png",
            "output_template": "",
            "keep_open": False,
        }
        first_wrapper = single_case_runner.build_single_case_wrapper_js(
            **common,
            ae_env=allowed_controls,
        )
        second_wrapper = single_case_runner.build_single_case_wrapper_js(
            **common,
            ae_env={},
        )
        for key, first_value in allowed_controls.items():
            with self.subTest(key=key):
                reset_line = f"$.setenv({json.dumps(key)}, '');"
                set_line = f"$.setenv({json.dumps(key)}, {json.dumps(first_value)});"
                self.assertIn(reset_line, first_wrapper)
                self.assertIn(set_line, first_wrapper)
                self.assertLess(
                    first_wrapper.index(reset_line),
                    first_wrapper.index(set_line),
                )
                self.assertIn(reset_line, second_wrapper)
                self.assertNotIn(first_value, second_wrapper)

    def test_dump_js_replaces_leaf_symlink_without_writing_its_target(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            request_dir = create_request_fixture(root)
            output_container = root / "output"
            victim = root / "victim.txt"
            victim.write_text("do not replace\n", encoding="utf-8")
            dump_path = root / "wrapper.jsx"
            dump_path.symlink_to(victim)
            args = types.SimpleNamespace(
                request_dir=request_dir,
                case_id="case_0001",
                output_dir=output_container,
                app_name="Fake After Effects",
                output_mode="png",
                output_template="",
                keep_open=False,
                timeout=1,
                param_override=[],
                ae_env=[],
                lock_path=root / "single.lock",
                dump_js=dump_path,
            )

            with (
                mock.patch.object(single_case_runner, "parse_args", return_value=args),
                mock.patch.object(
                    single_case_runner.subprocess,
                    "run",
                    side_effect=AssertionError("dump-js must not invoke the host"),
                ),
            ):
                self.assertEqual(single_case_runner.main(), 0)

            self.assertEqual(victim.read_text(encoding="utf-8"), "do not replace\n")
            self.assertTrue(dump_path.is_file())
            self.assertFalse(dump_path.is_symlink())
            self.assertIn("OLM_AE_REQUEST_DIR", dump_path.read_text(encoding="utf-8"))

    def test_success_result_requires_exactly_one_declared_output(self):
        cases = [
            {"status": "ok", "output_png": "", "output_exr": ""},
            {"status": "ok", "output_png": "/tmp/a.png", "output_exr": "/tmp/a.exr"},
        ]
        for result in cases:
            with self.subTest(result=result):
                self.assertTrue(single_case_runner.validate_result_output(result, not_before_ns=0))
                self.assertEqual(result["status"], "error")

    def test_short_host_timeout_still_allows_the_required_quiet_window(self):
        self.assertGreaterEqual(
            single_case_runner.output_wait_timeout(0.1),
            single_case_runner.OUTPUT_STABLE_WINDOW_SECONDS
            + single_case_runner.OUTPUT_POLL_INTERVAL_SECONDS,
        )
        self.assertEqual(
            single_case_runner.output_wait_timeout(999.0),
            single_case_runner.OUTPUT_COMPLETION_TIMEOUT_SECONDS,
        )

    def test_observation_metadata_is_json_compatible(self):
        observation = {
            "status": "stable",
            "timeout_ms": 120000,
            "waited_ms": 2250,
            "polls": 10,
            "stable_polls": 9,
            "stable_for_ms": 2000,
            "stable_window_ms": 2000,
            "size_bytes": 4096,
            "modified_ms": 1760000000000,
            "modified_ns": 1760000000000000000,
            "regular_file": True,
            "fresh": True,
            "readable": True,
            "format_complete": True,
            "crc_validated": True,
            "validation": "png_chunks_crc_iend",
            "output_kind": "png",
        }
        round_tripped = json.loads(json.dumps(observation))
        self.assertEqual(round_tripped["status"], "stable")
        self.assertEqual(round_tripped["size_bytes"], 4096)
        self.assertGreaterEqual(round_tripped["stable_for_ms"], round_tripped["stable_window_ms"])

    def test_atomic_json_writer_ignores_predictable_temp_symlink(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            destination = root / "result.json"
            victim = root / "victim.txt"
            victim.write_text("do not overwrite\n", encoding="utf-8")
            legacy_temporary = destination.with_name(
                f".{destination.name}.{os.getpid()}.tmp"
            )
            legacy_temporary.symlink_to(victim)
            payload = {"status": "passed", "value": 7}

            exact_bytes = single_case_runner.write_result_json(destination, payload)

            self.assertEqual(victim.read_text(encoding="utf-8"), "do not overwrite\n")
            self.assertTrue(legacy_temporary.is_symlink())
            self.assertFalse(destination.is_symlink())
            self.assertEqual(destination.read_bytes(), exact_bytes)
            self.assertEqual(json.loads(exact_bytes), payload)

    def test_atomic_json_writer_can_bind_a_trusted_parent_descriptor(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            directory_descriptor = os.open(
                root,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
            )
            try:
                payload = {"status": "passed", "bound": True}
                exact_bytes = single_case_runner.write_result_json(
                    Path("/untrusted/parent/result.json"),
                    payload,
                    parent_dir_fd=directory_descriptor,
                )
            finally:
                os.close(directory_descriptor)

            self.assertEqual((root / "result.json").read_bytes(), exact_bytes)
            self.assertEqual(json.loads(exact_bytes), payload)


if __name__ == "__main__":
    unittest.main()
