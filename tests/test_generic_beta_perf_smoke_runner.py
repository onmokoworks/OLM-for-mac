import importlib.util
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/perf/run_generic_beta_smoke.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generic_perf", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def directional_case_results(geometry: str) -> list[dict[str, object]]:
    width, height = (1920, 1080) if geometry == "hd" else (3840, 2160)
    return [
        {
            "side": side,
            "depth": depth,
            "geometry": geometry,
            "width": width,
            "height": height,
            "angle": 37.25,
            "brightness_gain": 0.75,
            "front_strength": 0 if side == "back" else 2,
            "back_strength": 0 if side == "front" else 2,
            "input_padding_bytes": 5 if depth == 8 else 1,
            "output_padding_bytes": 17 if depth == 8 else 3,
            "input_span_unchanged": True,
            "output_active_changed": True,
            "output_padding_unchanged": True,
            "independent_strides": True,
            "opposite_side_output_differs": True,
            "profile_outputs_pairwise_differ": True,
        }
        for side in ("front", "back", "dual")
        for depth in (8, 16, 32)
    ]


def kirakira_case_results(geometry: str) -> list[dict[str, object]]:
    dimensions = [1920, 1080] if geometry == "hd" else [3840, 2160]
    profiles = (
        ("box", "m1_h7_r0", 7, 0.0),
        ("approximated_gaussian", "m2_h7_ramp_r0", 7, 0.0),
        ("gaussian_length50", "m3_h50_r0", 50, 0.0),
        ("exponential", "m4_highlight_r3", 0, 0.0),
        ("gaussian_length300", "m3_ui_length", 300, 1.0),
    )
    return [
        {
            "mode": mode, "tuple": tuple_name, "depth_bpc": depth,
            "dimensions": dimensions, "horizontal_length": length,
            "rotation_degrees": rotation, "returncode": 0,
            "wall_seconds": 0.1, "peak_rss_bytes": 1024,
            "content_bounds": "full", "callback_shape": "1/1/1/0",
            "workload": "Smart plus two Classic production renders with parity/determinism checks",
            "classic_smart_parity": True, "deterministic": True,
            "independent_strides": True, "input_span_unchanged": True,
            "output_padding_unchanged": True, "output_active_changed": True,
        }
        for mode, tuple_name, length, rotation in profiles
        for depth in (8, 16, 32)
    ]


def test_catalog_has_all_ten_lanes_and_both_geometries() -> None:
    module = load_module()
    assert len(module.LANES) == 10
    assert len(set(module.LANES)) == 10
    assert module.GEOMETRIES == {"hd": [1920, 1080], "uhd": [3840, 2160]}
    assert set(module.COMMANDS) == {
        (lane, geometry) for lane in module.LANES for geometry in module.GEOMETRIES
    }


def test_budgets_are_bounded() -> None:
    module = load_module()
    assert module.TIMEOUT_SECONDS["hd"] <= 120
    assert module.TIMEOUT_SECONDS["uhd"] <= 180
    assert module.RSS_BUDGET_BYTES["hd"] <= 2 * 1024**3
    assert module.RSS_BUDGET_BYTES["uhd"] <= 3 * 1024**3
    assert set(module.TIMEOUT_SECONDS) == {"hd", "uhd"}
    assert set(module.RSS_BUDGET_BYTES) == {"hd", "uhd"}
    assert all(value > 0 for value in module.TIMEOUT_SECONDS.values())
    assert all(value > 0 for value in module.RSS_BUDGET_BYTES.values())


def test_toolchain_identity_binds_both_compiler_routes_and_external_sdk() -> None:
    module = load_module()
    identity = module.toolchain_metadata()
    module.validate_toolchain_metadata(identity)
    for key in ("hardcoded_clangxx", "configured_cxx"):
        assert identity[key]["returncode"] == 0
        assert len(identity[key]["sha256"]) == 64
        assert identity[key]["size_bytes"] > 0
    roots = identity["adobe_after_effects_sdk_workspace_roots"]
    assert set(roots) == {"Headers", "Util", "Resources"}
    assert all(item["status"] == "captured" and len(item["tree_sha256"]) == 64
               for item in roots.values())


def test_toolchain_tree_identity_is_bounded() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="perf_toolchain_tree_") as raw:
        root = Path(raw)
        for index in range(3):
            (root / f"file-{index}").write_text(str(index), encoding="utf-8")
        with patch.object(module, "TOOLCHAIN_TREE_MAX_FILES", 2):
            try:
                module._tree_identity(root)
            except module.EvidenceBindingError as error:
                assert "too many files" in str(error)
            else:
                raise AssertionError("oversized toolchain tree was accepted")


def test_every_lane_binds_runner_driver_and_production_source() -> None:
    module = load_module()
    assert set(module.LANE_DEPENDENCIES) == set(module.LANES)
    for lane in module.LANES:
        binding = module.capture_lane_binding(lane)
        roles = [item["role"] for item in binding["files"]]
        assert roles.count("runner") == 1, lane
        assert roles.count("driver") == 1, lane
        assert roles.count("production_source") == 1, lane
        assert all(len(item["sha256"]) == 64 for item in binding["files"])
        module.verify_lane_binding(lane, binding)


def test_dependency_binding_rejects_tampered_and_missing_files() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="perf_binding_tamper_") as raw:
        root = Path(raw)
        driver = root / "driver.py"
        source = root / "production.cpp"
        driver.write_text("print('driver')\n", encoding="utf-8")
        source.write_text("int production = 1;\n", encoding="utf-8")
        entries = (("driver", "driver.py"), ("production_source", "production.cpp"))
        expected = module.capture_file_bindings(entries, root)
        source.write_text("int production = 2;\n", encoding="utf-8")
        try:
            module.verify_file_bindings(entries, expected, root)
        except module.EvidenceBindingError:
            pass
        else:
            raise AssertionError("tampered dependency was accepted")
        source.unlink()
        try:
            module.verify_file_bindings(entries, expected, root)
        except module.EvidenceBindingError as error:
            assert "missing dependency" in str(error)
        else:
            raise AssertionError("missing dependency was accepted")


def test_current_canonical_twenty_cells_can_be_bound_without_overclaiming() -> None:
    module = load_module()
    report_path = ROOT / "reports/generic_beta_perf_smoke.json"
    payload = report_path.read_bytes()
    report = json.loads(payload)
    bound = module.bind_existing_report(
        report, source_report_sha256=hashlib.sha256(payload).hexdigest(),
        argv=("--bind-existing", str(report_path)),
    )
    module.verify_report_bindings(bound)
    assert len(bound["results"]) == 20
    assert bound["run_state"] == "COMPLETED"
    assert bound["outcome"] == "PASS"
    provenance = bound["provenance"]
    assert provenance["binding_mode"] == "retrospective_catalog_compatibility"
    assert provenance["measurement_source_identity"] == "unproven"
    assert provenance["does_not_prove_execution_against_bound_sources"] is True
    assert set(provenance["dependency_bindings"]) == set(module.LANES)
    assert all(row["dependency_binding_sha256"] ==
               provenance["dependency_bindings"][row["lane"]]["binding_sha256"]
               for row in bound["results"])
    directional = [row for row in bound["results"]
                   if row["lane"] == "OLMDirectionalBlur"]
    assert len(directional) == 2
    for row in directional:
        assert len(row["case_results"]) == 9
        assert {(case["side"], case["depth"]) for case in row["case_results"]} == {
            (side, depth) for side in ("front", "back", "dual")
            for depth in (8, 16, 32)
        }


def test_current_canonical_schema2_report_verifies_against_current_files() -> None:
    module = load_module()
    report = json.loads(
        (ROOT / "reports/generic_beta_perf_smoke.json").read_text(encoding="utf-8")
    )
    assert report["schema_version"] == 2
    module.verify_report_bindings(report)


def test_report_verifier_rejects_semantic_result_and_metadata_tampering() -> None:
    module = load_module()
    original = json.loads(
        (ROOT / "reports/generic_beta_perf_smoke.json").read_text(encoding="utf-8")
    )

    def rejected(mutator, digest_key="results_sha256"):
        candidate = json.loads(json.dumps(original))
        mutator(candidate)
        if digest_key == "results_sha256":
            candidate["provenance"][digest_key] = module._json_sha256(candidate["results"])
        elif digest_key == "invocation_sha256":
            invocation = candidate.get("invocation") or candidate["binding_invocation"]
            candidate["provenance"][digest_key] = module._json_sha256(invocation)
        elif digest_key == "platform_sha256":
            platform_info = candidate.get("platform") or candidate["binding_platform"]
            candidate["provenance"][digest_key] = module._json_sha256(platform_info)
        try:
            module.verify_report_bindings(candidate)
        except module.EvidenceBindingError:
            return
        raise AssertionError("tampered report was accepted")

    rejected(lambda report: report["results"][0].update(parameters="all_parameters"))
    rejected(lambda report: report["results"][0].update(wall_seconds=float("nan")))
    rejected(lambda report: report["results"][0].update(returncode=False))
    rejected(lambda report: report["results"][0].update(peak_rss_bytes=False))
    rejected(lambda report: report["results"][0]["case_results"][0].update(status="failed"))
    rejected(lambda report: report["results"][0]["case_results"].__setitem__(
        1, dict(report["results"][0]["case_results"][0])
    ))
    rejected(lambda report: next(
        row for row in report["results"] if row["lane"] == "OLMDistanceGradation"
    ).__setitem__("case_results", [{"status": "passed"}]))
    rejected(
        lambda report: (report.get("invocation") or report["binding_invocation"])
        .update(working_directory="/tampered"),
        "invocation_sha256",
    )
    rejected(
        lambda report: (report.get("platform") or report["binding_platform"])
        .update(machine="tampered"),
        "platform_sha256",
    )


def test_outcome_prioritizes_real_failure_over_unavailable_cells() -> None:
    module = load_module()
    assert module._outcome([{"status": "passed"}]) == ("COMPLETED", "PASS", 0)
    assert module._outcome([{"status": "not_measured"}]) == \
        ("INCOMPLETE", "INCOMPLETE", 1)
    assert module._outcome([{"status": "failed"}, {"status": "not_measured"}]) == \
        ("FAILED", "FAIL", 1)


def test_running_report_precedes_measurement_and_final_is_atomic_and_bound() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="perf_running_report_") as raw:
        output = Path(raw) / "report.json"

        def fake_measure(_command, geometry):
            running = json.loads(output.read_text(encoding="utf-8"))
            assert running["run_state"] == "RUNNING"
            assert running["outcome"] is None
            assert running["results"] == []
            assert running["provenance"]["measurement_source_identity"] == \
                "pre_run_snapshot_captured"
            return {
                "status": "passed", "returncode": 0,
                "wall_seconds": 0.001, "peak_rss_bytes": 1024,
                "rss_budget_bytes": module.RSS_BUDGET_BYTES[geometry],
                "timeout_seconds": module.TIMEOUT_SECONDS[geometry],
                "stdout_tail": "", "stderr_tail": "",
            }

        with patch.object(module, "measure", side_effect=fake_measure):
            result = module.run_measurements(
                output, ["OLMDistanceGradation"], ["hd"],
                ["--lane", "OLMDistanceGradation", "--geometry", "hd"],
            )
        assert result == 0
        final = json.loads(output.read_text(encoding="utf-8"))
        assert final["run_state"] == "COMPLETED"
        assert final["outcome"] == "PASS"
        assert final["provenance"]["measurement_source_identity"] == \
            "exact_pre_and_post_match"
        module.verify_report_bindings(final)
        encoded = (json.dumps(final, sort_keys=True) + "\n").encode("utf-8")
        rebound = module.bind_existing_report(
            final, source_report_sha256=hashlib.sha256(encoded).hexdigest(),
            argv=("--bind-existing", str(output)),
        )
        assert "invocation" not in rebound and "platform" not in rebound
        assert rebound["provenance"]["binding_mode"] == \
            "retrospective_catalog_compatibility"
        module.verify_report_bindings(rebound)
        assert not list(output.parent.glob(f".{output.name}.*.tmp"))


def test_interrupted_measurement_never_leaves_an_old_pass_report() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="perf_interrupted_report_") as raw:
        output = Path(raw) / "report.json"
        module.atomic_write_json(output, {"run_state": "COMPLETED", "outcome": "PASS"})
        with patch.object(module, "measure", side_effect=KeyboardInterrupt):
            try:
                module.run_measurements(
                    output, ["OLMDistanceGradation"], ["hd"],
                    ["--lane", "OLMDistanceGradation"],
                )
            except KeyboardInterrupt:
                pass
            else:
                raise AssertionError("KeyboardInterrupt was swallowed")
        remaining = json.loads(output.read_text(encoding="utf-8"))
        assert remaining["run_state"] == "RUNNING"
        assert remaining["outcome"] is None
        assert remaining["run_id"]


def test_toolchain_preflight_interrupt_invalidates_old_pass_first() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="perf_toolchain_interrupt_") as raw:
        output = Path(raw) / "report.json"
        module.atomic_write_json(output, {"run_state": "COMPLETED", "outcome": "PASS"})
        with patch.object(module, "toolchain_metadata", side_effect=KeyboardInterrupt):
            try:
                module.run_measurements(
                    output, ["OLMDistanceGradation"], ["hd"],
                    ["--lane", "OLMDistanceGradation"],
                )
            except KeyboardInterrupt:
                pass
            else:
                raise AssertionError("toolchain KeyboardInterrupt was swallowed")
        remaining = json.loads(output.read_text(encoding="utf-8"))
        assert remaining["run_state"] == "RUNNING"
        assert remaining["outcome"] is None
        assert remaining["provenance"]["measurement_source_identity"] == \
            "preflight_pending"


def test_launch_failure_emits_a_structurally_verifiable_failed_report() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="perf_launch_failure_") as raw:
        output = Path(raw) / "report.json"
        failure = {
            "status": "launch_failed", "wall_seconds": 0.001,
            "timeout_seconds": module.TIMEOUT_SECONDS["hd"],
            "stdout_tail": "", "stderr_tail": "missing executable",
            "launch_error": "FileNotFoundError",
        }
        with patch.object(module, "measure", return_value=failure):
            result = module.run_measurements(
                output, ["OLMDistanceGradation"], ["hd"],
                ["--lane", "OLMDistanceGradation"],
            )
        assert result == 1
        report = json.loads(output.read_text(encoding="utf-8"))
        assert report["run_state"] == "FAILED"
        assert report["outcome"] == "FAIL"
        assert report["results"][0]["rss_budget_bytes"] == \
            module.RSS_BUDGET_BYTES["hd"]
        module.verify_report_bindings(report)


def test_missing_structured_driver_cases_cannot_be_published_as_pass() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="perf_missing_cases_") as raw:
        output = Path(raw) / "report.json"
        fake_success = {
            "status": "passed", "returncode": 0, "wall_seconds": 0.001,
            "peak_rss_bytes": 1024, "timeout_seconds": module.TIMEOUT_SECONDS["hd"],
            "rss_budget_bytes": module.RSS_BUDGET_BYTES["hd"],
            "stdout_tail": "", "stderr_tail": "", "time_metrics_tail": "",
        }
        with patch.object(module, "measure", return_value=fake_success):
            result = module.run_measurements(
                output, ["OLMRadialBlur"], ["hd"], ["--lane", "OLMRadialBlur"],
            )
        assert result == 1
        report = json.loads(output.read_text(encoding="utf-8"))
        assert report["results"][0]["status"] == "invalid_evidence"
        assert "structured case count mismatch" in report["results"][0]["reason"]
        module.verify_report_bindings(report)


def test_process_group_timeout_reaps_parent_and_grandchild() -> None:
    if os.name != "posix":
        return
    module = load_module()
    child_program = (
        "import os,signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); "
        "os.close(1); os.close(2); time.sleep(30)"
    )
    program = (
        "import subprocess,sys,time; "
        f"child=subprocess.Popen([sys.executable,'-c',{child_program!r}]); "
        "print(child.pid,flush=True); time.sleep(30)"
    )
    result = module.run_process_group([sys.executable, "-c", program], 0.25)
    assert result["launched"] is True
    assert result["timed_out"] is True
    assert result["timeout_cleanup"]["process_group_reaped"] is True
    assert "SIGKILL" in result["timeout_cleanup"]["signals_sent"]
    assert result["stdout"].strip().isdigit()
    try:
        os.killpg(result["process_group_id"], 0)
    except ProcessLookupError:
        pass
    else:
        os.killpg(result["process_group_id"], 9)
        raise AssertionError("timed-out process group survived cleanup")


def test_successful_parent_with_background_child_is_not_reported_clean() -> None:
    if os.name != "posix":
        return
    module = load_module()
    child_program = (
        "import os,signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); "
        "os.close(1); os.close(2); time.sleep(30)"
    )
    program = (
        "import subprocess,sys; "
        f"subprocess.Popen([sys.executable,'-c',{child_program!r}]); print('parent-done')"
    )
    result = module.run_process_group([sys.executable, "-c", program], 5.0)
    assert result["returncode"] == 0
    assert result["lingering_process_group"] is True
    assert result["lingering_cleanup"]["process_group_reaped"] is True
    assert "SIGKILL" in result["lingering_cleanup"]["signals_sent"]


def test_toondilate_has_exact_hd_uhd_production_drivers() -> None:
    module = load_module()
    for geometry in ("hd", "uhd"):
        command = module.COMMANDS[("OLMToonDilate", geometry)]
        assert command[-2:] == ["--geometry", geometry]
        assert "run_olmtoondilate_generic_production_perf.py" in command[1]
    predicate = module.SUPPORT_PREDICATES["OLMToonDilate"]
    assert "pf8_pf16_pf32" in predicate
    assert "0 <= search_radius <= 100" in predicate


def test_distancegradation_has_independent_hd_and_uhd_production_drivers() -> None:
    module = load_module()
    for geometry in ("hd", "uhd"):
        command = module.COMMANDS[("OLMDistanceGradation", geometry)]
        assert "test_olmdistancegradation_generic_production_beta_20260820.py" in command[-1]


def test_radialblur_has_exact_geometry_release_like_drivers() -> None:
    module = load_module()
    for geometry in ("hd", "uhd"):
        command = module.COMMANDS[("OLMRadialBlur", geometry)]
        assert command[1] == "tools/perf/run_olmradialblur_generic_production_perf.py"
        assert command[command.index("--geometry") + 1] == geometry


def test_directionalblur_perf_rows_select_exact_geometry() -> None:
    module = load_module()
    for geometry in ("hd", "uhd"):
        command = module.COMMANDS[("OLMDirectionalBlur", geometry)]
        assert command[1] == "tools/emulation/test_dblur_generic_deep_geometry_beta_20260820.py"
        assert command[command.index("--geometry") + 1] == geometry
        assert module.CASE_DEPTH_COUNTS[("OLMDirectionalBlur", geometry)] == {
            8: 3, 16: 3, 32: 3,
        }
    predicate = module.SUPPORT_PREDICATES["OLMDirectionalBlur"]
    assert "pf8_pf16_pf32" in predicate
    assert "neutral_single_or_dual_side" in predicate
    assert "at_least_one(front_strength,back_strength)" in predicate
    assert "0 <= front_strength,back_strength <= 4000" in predicate
    assert "3221225472" in predicate
    assert "width*height <= 8847360" in predicate
    assert "edge_clamped_operation_units <= 350000000" in predicate
    assert "per_render_plugin_owned_live_bytes" in predicate
    assert module._parameters("OLMDirectionalBlur", "hd").startswith(
        "neutral_single_dual_front_back_angle37.25_gain0.75_strength2_"
    )


def test_directionalblur_semantic_validator_requires_exact_single_dual_matrix() -> None:
    module = load_module()
    valid = directional_case_results("hd")
    module._validate_case_results({"case_results": valid}, "OLMDirectionalBlur", "hd")

    def must_reject(mutator) -> None:
        candidate = json.loads(json.dumps(valid))
        mutator(candidate)
        try:
            module._validate_case_results(
                {"case_results": candidate}, "OLMDirectionalBlur", "hd"
            )
        except module.EvidenceBindingError:
            return
        raise AssertionError("invalid Directional single/dual case matrix was accepted")

    must_reject(lambda cases: cases[3].update(back_strength=0))
    must_reject(lambda cases: cases[1].update(back_strength=2))
    must_reject(lambda cases: cases[8].update(side="front"))
    must_reject(lambda cases: cases.__setitem__(3, dict(cases[0])))
    must_reject(lambda cases: cases[4].pop("back_strength"))
    must_reject(lambda cases: cases[7].update(front_strength=0))
    must_reject(lambda cases: cases[6].pop("profile_outputs_pairwise_differ"))


def test_kirakira_perf_contract_includes_worst_admitted_ui_length() -> None:
    module = load_module()
    for geometry in ("hd", "uhd"):
        assert module.CASE_DEPTH_COUNTS[("OLMKiraKira", geometry)] == {
            8: 5, 16: 5, 32: 5,
        }
        command = module.COMMANDS[("OLMKiraKira", geometry)]
        assert command[1] == "tools/perf/run_olmkirakira_generic_production_perf.py"
        assert command[command.index("--geometry") + 1] == geometry
        module._validate_case_results(
            {"case_results": kirakira_case_results(geometry)},
            "OLMKiraKira", geometry,
        )
    predicate = module.SUPPORT_PREDICATES["OLMKiraKira"]
    assert "mode3_horizontal_only" in predicate
    assert "1 <= length <= 300" in predicate
    assert "per_render_plugin_owned_bytes <= 1073741824" in predicate
    assert "mode3_work_units <= 12000000000" in predicate
    assert "pf32_finite_sdr_0_1" in predicate
    assert "gaussian_horizontal_length300_rotation1" in module._parameters(
        "OLMKiraKira", "uhd"
    )
    driver = (ROOT / "tools/perf/run_olmkirakira_generic_production_perf.py").read_text(
        encoding="utf-8"
    )
    assert "--single-mode3-length" in driver
    assert '"horizontal_length": 300' in driver
    assert '"rotation_degrees": 1.0' in driver
    assert "GENERIC_ROW.fullmatch" in driver
    assert "def parse_peak_rss" in driver
    assert "len(matches) != 1" in driver
    # Util is an external Adobe-SDK symlink and is bound by the global
    # toolchain-tree identity; repo-relative lane dependencies must not escape.
    dependencies = {path for _, path in module.LANE_DEPENDENCIES["OLMKiraKira"]}
    assert "Util/AEGP_SuiteHandler.cpp" not in dependencies
    assert "Util/MissingSuiteError.cpp" not in dependencies


def test_kirakira_semantic_validator_rejects_profile_and_safety_tampering() -> None:
    module = load_module()
    valid = kirakira_case_results("hd")

    def must_reject(mutator) -> None:
        candidate = json.loads(json.dumps(valid))
        mutator(candidate)
        try:
            module._validate_case_results(
                {"case_results": candidate}, "OLMKiraKira", "hd"
            )
        except module.EvidenceBindingError:
            return
        raise AssertionError("invalid Kira performance case matrix was accepted")

    must_reject(lambda cases: cases[-1].update(horizontal_length=299))
    must_reject(lambda cases: cases[-1].update(rotation_degrees=0.0))
    must_reject(lambda cases: cases[-1].update(tuple="m3_h50_r0"))
    must_reject(lambda cases: cases[-1].update(classic_smart_parity=False))
    must_reject(lambda cases: cases[-1].update(callback_shape="0/0/0/0"))
    must_reject(lambda cases: cases.__setitem__(-1, dict(cases[0])))
    must_reject(lambda cases: cases[-1].pop("wall_seconds"))
    must_reject(lambda cases: cases[-1].pop("peak_rss_bytes"))
    must_reject(lambda cases: cases[-1].pop("returncode"))
    must_reject(lambda cases: cases[-1].pop("dimensions"))
    must_reject(lambda cases: cases[-1].update(workload="labels_only"))
    must_reject(lambda cases: cases[-1].update(wall_seconds=0))
    must_reject(lambda cases: cases[-1].update(peak_rss_bytes=0))


def test_kirakira_inner_rss_parser_requires_one_positive_measurement() -> None:
    path = ROOT / "tools/perf/run_olmkirakira_generic_production_perf.py"
    spec = importlib.util.spec_from_file_location("kira_perf_driver", path)
    driver = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(driver)
    line = "  12345  maximum resident set size\n"
    assert driver.parse_peak_rss(line) == 12345
    assert driver.parse_peak_rss("") is None
    assert driver.parse_peak_rss("0 maximum resident set size\n") is None
    assert driver.parse_peak_rss(line + line) is None


def test_kirakira_driver_row_parser_binds_public_route_contract() -> None:
    path = ROOT / "tools/perf/run_olmkirakira_generic_production_perf.py"
    spec = importlib.util.spec_from_file_location("kira_perf_driver_rows", path)
    driver = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(driver)
    row = (
        "GENERIC tuple=m3_ui_length length=300 rotation=1.0 depth=32 "
        "size=1920x1080 ok=1 content=full callbacks=1/1/1/0 "
        "strides=30736/30768/30800 params=25/25 lifecycle=1 headers=1 "
        "mixed_alpha=1 zero_alpha_rgb=1 predata=1 deleted=1 handles=1"
    )
    parsed = driver.GENERIC_ROW.fullmatch(row)
    assert parsed is not None
    assert parsed.group(10) == "30736/30768/30800"
    assert parsed.group(11) == "25/25"
    assert all(parsed.group(index) == "1" for index in range(12, 19))
    assert driver.GENERIC_ROW.fullmatch(
        row.replace(" zero_alpha_rgb=1", "")
    ) is None
    assert driver.GENERIC_ROW.fullmatch(row + " unchecked=1") is None
    assert {case["parameter_count"] for case in driver.CASES} == {25, 26}


def test_measure_fails_closed_when_peak_rss_is_unavailable() -> None:
    module = load_module()
    completed = {
        "launched": True, "timed_out": False, "returncode": 0,
        "stdout": "ok\n", "stderr": "", "process_group_id": 123,
    }
    with patch.object(module, "run_process_group", return_value=completed):
        row = module.measure(["demo"], "hd")
    assert row["status"] == "rss_unavailable"
    assert row["peak_rss_bytes"] is None


def test_measure_uses_dedicated_outer_time_metrics_not_driver_stderr() -> None:
    module = load_module()
    program = (
        "import sys; "
        "sys.stderr.write('1 maximum resident set size\\n'); "
        "print('driver-ok')"
    )
    row = module.measure([sys.executable, "-c", program], "hd")
    assert row["status"] == "passed", row
    assert row["peak_rss_bytes"] != 1
    assert "1 maximum resident set size" in row["stderr_tail"]
    assert row["time_metrics_tail"].count("maximum resident set size") == 1


def test_colorkeep_has_hd_and_uhd_production_o2_drivers() -> None:
    module = load_module()
    for geometry in ("hd", "uhd"):
        command = module.COMMANDS[("ColorKeep", geometry)]
        assert command[1] == "tools/perf/run_colorkeep_generic_production_perf.py"
        assert command[command.index("--geometry") + 1] == geometry
    predicate = module.SUPPORT_PREDICATES["ColorKeep"]
    assert "pf8_pf16_pf32" in predicate and "1 <= count <= 100" in predicate
    assert "width <= 3840" in predicate and "height <= 2160" in predicate


def test_smoother_v1_hd_and_uhd_use_explicit_pf8_pf16_production_dimensions() -> None:
    module = load_module()
    for geometry, dimensions in module.GEOMETRIES.items():
        command = module.COMMANDS[("OLMSmoother", geometry)]
        assert "run_olmsmoother_v1_generic_production_perf.py" in command[1]
        assert command[command.index("--depth") + 1] == "both"
        assert int(command[command.index("--width") + 1]) == dimensions[0]
        assert int(command[command.index("--height") + 1]) == dimensions[1]
    predicate = module.SUPPORT_PREDICATES["OLMSmoother"]
    assert "pf8 || pf16" in predicate and "key_off" in predicate
    assert "width <= 3840" in predicate and "height <= 2160" in predicate


def test_smoother2_support_predicate_tracks_gamma_colors_beta_lane() -> None:
    module = load_module()
    predicate = module.SUPPORT_PREDICATES["OLMSmoother2"]
    assert "gamma_none" in predicate
    assert "gamma_all" in predicate
    assert "gamma_colors_count_1_5" in predicate


def test_kirakira_perf_harness_has_no_workspace_absolute_include() -> None:
    driver = (ROOT / "tools/perf/run_olmkirakira_generic_production_perf.py").read_text(
        encoding="utf-8"
    )
    harness = (
        ROOT / "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp"
    ).read_text(encoding="utf-8")
    assert "/Users/onmk/" not in harness
    assert "#include KIRA_STRINGS_SOURCE" in harness
    assert "../../mac/OLMKiraKira/OLMKiraKira_Strings.cpp" in harness
    assert 'STRINGS_SOURCE = "mac/OLMKiraKira/OLMKiraKira_Strings.cpp"' in driver
    assert "-DKIRA_STRINGS_SOURCE" in driver
    assert '"-I", str(ROOT)' in driver


def test_lane_and_geometry_can_be_selected_independently() -> None:
    # Keep this stdlib-only: the aggregate gate intentionally has no pytest
    # fixture injection and must execute this real selected-lane smoke.
    with tempfile.TemporaryDirectory(prefix="generic_perf_selected_") as raw:
        output = Path(raw) / "selected.json"
        run = subprocess.run(
            [sys.executable, str(SCRIPT), "--lane", "OLMDistanceGradation",
             "--geometry", "hd", "--output", str(output)],
            cwd=ROOT, text=True, capture_output=True,
        )
        assert run.returncode == 0, run.stdout + run.stderr
        import json
        rows = json.loads(output.read_text())["results"]
        assert len(rows) == 1
        assert rows[0]["lane"] == "OLMDistanceGradation"
        assert rows[0]["geometry"] == "hd"
        assert rows[0]["status"] == "passed"
