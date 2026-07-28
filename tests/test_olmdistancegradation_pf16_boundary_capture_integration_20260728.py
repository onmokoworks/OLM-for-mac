from __future__ import annotations

import importlib.util
import json
import signal
import tempfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_olmdistancegradation_pf16_boundary_capture_20260728.py"
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"


def load_runner():
    spec = importlib.util.spec_from_file_location("olmdg_pf16_capture_runner", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pf16_instrumentation_is_env_gated_and_logging_only():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'getenv("OLM_DG_PF16_BOUNDARY_CAPTURE_PATH")' in source
    assert 'getenv("OLM_DG_PF16_BOUNDARY_CAPTURE_CASE_ID")' in source
    assert "memcpy(&word, &value, sizeof(word));" in source
    assert "debug_dump_pf16_boundary_point(" in source
    shade = source[source.index("template<> void shade_scanline<PF_Pixel16>") :]
    shade = shade[: shade.index("template<> void shade_scanline<PF_PixelFloat>")]
    store = shade.index("dst[i].blue  = db;")
    capture = shade.index("debug_dump_pf16_boundary_point(")
    assert capture > store
    assert "src[i]," in shade[capture : capture + 220]
    assert "x_row[i], derived_field_word, oa, orv, og, ob, dst[i]" in shade[capture : capture + 280]
    assert '\\"direct_field_staging_word\\":\\"unavailable_at_mac_float_field_boundary\\"' in source
    assert '"raw_pf16_word"' not in source
    prefix = shade[: shade.index("if (pf16_capture_path")]
    assert "OLM_DG_PF16_BOUNDARY_CAPTURE" not in prefix.replace(
        'getenv("OLM_DG_PF16_BOUNDARY_CAPTURE_PATH")', ""
    ).replace('getenv("OLM_DG_PF16_BOUNDARY_CAPTURE_CASE_ID")', "")


def test_parser_preserves_direct_words_and_float_bits():
    module = load_runner()
    case_id = "olmdistancegradation_extended__case_0012"
    row = {
        "kind": "olmdg_pf16_shade_boundary_v1",
        "case_id": case_id,
        "x": 438,
        "y": 0,
        "source": {"a": 32768, "r": 10, "g": 20, "b": 30},
        "field": {
            "value": 0.5,
            "bits": "0x3f000000",
            "derived_pf16_word": 16384,
            "derivation": "nearest_even_clamp_float32_times_32768_logging_only",
            "direct_field_staging_word": "unavailable_at_mac_float_field_boundary",
        },
        "pre_store": {
            channel: {"value": value, "bits": bits}
            for channel, value, bits in (
                ("a", 1.0, "0x3f800000"),
                ("r", 0.5, "0x3f000000"),
                ("g", 0.25, "0x3e800000"),
                ("b", 0.0, "0x00000000"),
            )
        },
        "stored": {"a": 32768, "r": 16384, "g": 8192, "b": 0},
    }
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "capture.jsonl"
        log.write_text("noise\n" + json.dumps(row) + "\n", encoding="utf-8")
        parsed = module.parse_log(log, case_id, (438, 0))
    assert parsed == row


def test_process_identity_binds_pid_start_executable_and_exact_vmmap(tmp_path: Path):
    module = load_runner()
    plugin = tmp_path / "OLMDistanceGradation"
    executable = tmp_path / "After Effects"
    plugin.write_bytes(b"plugin")
    executable.write_bytes(b"afterfx")
    outputs = {
        ("ps", "-p", "123", "-o", "lstart="): "Mon Jul 28 12:34:56 2026\n",
        ("ps", "-p", "123", "-o", "comm="): str(executable) + "\n",
        ("vmmap", "123"): f"__TEXT 0-1 r-x/r-x {plugin.resolve()}\n",
    }
    with (
        mock.patch.object(module, "running_ae_pids", return_value=[123]),
        mock.patch.object(module, "run_text", side_effect=lambda args, timeout: outputs[tuple(args)]),
    ):
        identity = module.process_identity(plugin)
    assert identity["process_id"] == 123
    assert identity["process_start_token"] == "Mon Jul 28 12:34:56 2026"
    assert identity["process_executable"] == str(executable.resolve())
    assert identity["plugin_path"] == str(plugin.resolve())


def test_fabricated_manifests_are_rejected_without_launching_ae(tmp_path: Path):
    module = load_runner()
    request_dir = tmp_path / "request"
    request_dir.mkdir()
    cases = [{"id": case_id} for case_id in module.CASE_COORDINATES]
    (request_dir / "request_manifest.json").write_text(json.dumps({"cases": cases}), encoding="utf-8")
    (request_dir / "reference_manifest.json").write_text(
        json.dumps({"project": {"bits_per_channel": 16}, "cases": cases}), encoding="utf-8"
    )
    plugin = tmp_path / "OLMDistanceGradation"
    plugin.write_bytes(b"fixture")
    with mock.patch.object(module.subprocess, "Popen", side_effect=AssertionError("AE launch forbidden")):
        status = module.main(
            [
                "--request-dir",
                str(request_dir),
                "--plugin-binary",
                str(plugin),
                "--output-dir",
                str(tmp_path / "unused"),
                "--dry-run",
            ]
        )
    assert status == 1


def test_runner_uses_one_process_contract_and_cooperative_cleanup():
    source = RUNNER.read_text(encoding="utf-8")
    assert "keep_open=index < len(case_ids) - 1" in source
    assert 'command.append("--keep-open")' in source
    assert 'resume.write_text("abort-close\\n"' in source
    assert "close_exact_owned_process(args.app_name, owned_identity)" in source
    assert "verify_process_closed(bound[\"process_id\"])" in source
    assert "refusing capture while user After Effects is already running" in source
    assert "process.kill()" not in source


def owned_identity(tmp_path: Path) -> dict:
    executable = tmp_path / "After Effects"
    plugin = tmp_path / "OLMDistanceGradation"
    executable.write_bytes(b"ae")
    plugin.write_bytes(b"plugin")
    module = load_runner()
    return {
        "platform": "macos",
        "plugin_path": str(plugin),
        "plugin_sha256": module.sha256(plugin),
        "process_id": 123,
        "process_start_token": "owned-start",
        "process_executable": str(executable),
        "process_executable_sha256": module.sha256(executable),
    }


def invoke_main_with_case_failure(tmp_path: Path, failure: BaseException) -> tuple[int, list[dict]]:
    module = load_runner()
    plugin = tmp_path / "OLMDistanceGradation"
    plugin.write_bytes(b"plugin")
    request = tmp_path / "request.json"
    reference = tmp_path / "reference.json"
    request.write_bytes(b"request")
    reference.write_bytes(b"reference")
    identity = owned_identity(tmp_path)
    closed: list[dict] = []

    def fail_after_publish(args, case_id, output_root, expected_identity, keep_open, publish_owned_identity):
        publish_owned_identity(identity)
        raise failure

    with (
        mock.patch.object(module, "canonical_manifests", return_value=(request, reference)),
        mock.patch.object(module, "running_ae_pids", return_value=[]),
        mock.patch.object(module, "run_case", side_effect=fail_after_publish),
        mock.patch.object(module, "close_exact_owned_process", side_effect=lambda app, value: closed.append(value)),
    ):
        status = module.main(
            [
                "--request-dir",
                str(tmp_path),
                "--plugin-binary",
                str(plugin),
                "--output-dir",
                str(tmp_path / "output"),
            ]
        )
    return status, closed


def test_owned_process_cleanup_covers_all_postrender_failures(tmp_path: Path):
    failures = (
        FileNotFoundError("missing AE result"),
        RuntimeError("parse_log failure"),
        RuntimeError("true16 ImageMagick extraction failure"),
    )
    for index, failure in enumerate(failures):
        case_root = tmp_path / f"failure_{index}"
        case_root.mkdir()
        status, closed = invoke_main_with_case_failure(case_root, failure)
        assert status == 1
        assert len(closed) == 1
        assert closed[0]["process_id"] == 123
        assert closed[0]["process_start_token"] == "owned-start"


def test_next_case_setup_or_popen_failure_closes_prior_owned_process(tmp_path: Path):
    module = load_runner()
    plugin = tmp_path / "OLMDistanceGradation"
    plugin.write_bytes(b"plugin")
    request = tmp_path / "request.json"
    reference = tmp_path / "reference.json"
    request.write_bytes(b"request")
    reference.write_bytes(b"reference")
    identity = owned_identity(tmp_path)
    closed: list[dict] = []
    calls = 0

    def first_then_fail(args, case_id, output_root, expected_identity, keep_open, publish_owned_identity):
        nonlocal calls
        calls += 1
        if calls == 1:
            publish_owned_identity(identity)
            return identity, {"case_id": case_id}
        raise OSError("next-case mkdir/Popen failure")

    with (
        mock.patch.object(module, "canonical_manifests", return_value=(request, reference)),
        mock.patch.object(module, "running_ae_pids", return_value=[]),
        mock.patch.object(module, "run_case", side_effect=first_then_fail),
        mock.patch.object(module, "close_exact_owned_process", side_effect=lambda app, value: closed.append(value)),
    ):
        status = module.main(
            [
                "--request-dir",
                str(tmp_path),
                "--plugin-binary",
                str(plugin),
                "--output-dir",
                str(tmp_path / "output"),
            ]
        )
    assert status == 1
    assert calls == 2
    assert [item["process_id"] for item in closed] == [123]


def test_abnormal_cleanup_signals_only_twice_reverified_exact_owned_pid(tmp_path: Path):
    module = load_runner()
    identity = owned_identity(tmp_path)
    signals: list[tuple[int, signal.Signals]] = []
    with (
        mock.patch.object(module, "reverify_exact_owned_process", side_effect=[True, True]),
        mock.patch.object(module.os, "kill", side_effect=lambda pid, sig: signals.append((pid, sig))),
        mock.patch.object(module, "verify_process_closed"),
    ):
        module.close_exact_owned_process("Adobe After Effects 2026", identity)
    assert signals == [(123, signal.SIGTERM)]


def test_user_or_replacement_ae_process_prevents_all_cleanup_actions(tmp_path: Path):
    module = load_runner()
    identity = owned_identity(tmp_path)
    scenarios = (
        [123, 999],  # user second AE exists before cleanup
        [999],       # only a different/new AE exists
    )
    for running in scenarios:
        with (
            mock.patch.object(module, "running_ae_pids", return_value=running),
            mock.patch.object(module.os, "kill") as kill,
            mock.patch.object(module.subprocess, "run") as subprocess_run,
        ):
            try:
                module.close_exact_owned_process("Adobe After Effects 2026", identity)
            except RuntimeError as exc:
                assert "not exactly the owned PID" in str(exc)
            else:
                raise AssertionError(f"ambiguous process set unexpectedly accepted: {running}")
            kill.assert_not_called()
            subprocess_run.assert_not_called()  # in particular, no app-name AppleScript/DoScript

    with (
        mock.patch.object(module, "reverify_exact_owned_process", side_effect=[True, RuntimeError("owned exited; new AE")]),
        mock.patch.object(module.os, "kill") as kill,
        mock.patch.object(module.subprocess, "run") as subprocess_run,
    ):
        try:
            module.close_exact_owned_process("Adobe After Effects 2026", identity)
        except RuntimeError as exc:
            assert "owned exited; new AE" in str(exc)
        else:
            raise AssertionError("between-check replacement unexpectedly accepted")
        kill.assert_not_called()
        subprocess_run.assert_not_called()


def test_actual_reverify_rejects_each_changed_identity_field(tmp_path: Path):
    module = load_runner()
    identity = owned_identity(tmp_path)
    executable = Path(identity["process_executable"])
    plugin = Path(identity["plugin_path"])

    def check(outputs, running=(123,), candidate=None, mutate_files=None):
        if mutate_files:
            mutate_files()
        with (
            mock.patch.object(module, "running_ae_pids", return_value=list(running)),
            mock.patch.object(module, "run_text", side_effect=lambda args, timeout: outputs[tuple(args)]),
            mock.patch.object(module.os, "kill") as kill,
        ):
            try:
                module.close_exact_owned_process("Adobe After Effects 2026", candidate or identity)
            except RuntimeError:
                pass
            else:
                raise AssertionError("changed identity unexpectedly accepted")
            kill.assert_not_called()

    base = {
        ("ps", "-p", "123", "-o", "lstart="): "owned-start\n",
        ("ps", "-p", "123", "-o", "comm="): str(executable) + "\n",
        ("vmmap", "123"): f"__TEXT 0-1 r-x/r-x {plugin}\n",
    }
    changed_start = dict(base)
    changed_start[("ps", "-p", "123", "-o", "lstart=")] = "different-start\n"
    check(changed_start)

    changed_platform = dict(identity)
    changed_platform["platform"] = "windows"
    check(base, candidate=changed_platform)

    changed_executable_hash = dict(identity)
    changed_executable_hash["process_executable_sha256"] = "0" * 64
    check(base, candidate=changed_executable_hash)

    changed_plugin_hash = dict(identity)
    changed_plugin_hash["plugin_sha256"] = "0" * 64
    check(base, candidate=changed_plugin_hash)

    other_executable = tmp_path / "Other After Effects"
    other_executable.write_bytes(b"other")
    changed_path = dict(base)
    changed_path[("ps", "-p", "123", "-o", "comm=")] = str(other_executable) + "\n"
    check(changed_path)

    executable.write_bytes(b"changed executable")
    check(base)
    executable.write_bytes(b"ae")

    plugin.write_bytes(b"changed plugin")
    check(base)
    plugin.write_bytes(b"plugin")

    changed_vmmap = dict(base)
    changed_vmmap[("vmmap", "123")] = "__TEXT 0-1 r-x/r-x /different/plugin\n"
    check(changed_vmmap)

    check(base, running=(124,))

    with (
        mock.patch.object(module, "reverify_exact_owned_process", side_effect=RuntimeError("identity changed")),
        mock.patch.object(module.os, "kill") as kill,
    ):
        try:
            module.close_exact_owned_process("Adobe After Effects 2026", identity)
        except RuntimeError as exc:
            assert "identity changed" in str(exc)
        else:
            raise AssertionError("changed/preexisting identity unexpectedly accepted")
        kill.assert_not_called()
