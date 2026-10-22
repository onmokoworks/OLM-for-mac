status: done
summary:
- Capped all 59 pool constructors across 46 test/probe/fixture runners with min(existing, int(os.environ.get("OLM_TEST_JOBS", "2"))).
- Both named ellipse siblings already have F25 child environment, timeout, and no-fallthrough guards at the starting revision; preserved them and added explicit coverage.
- Broadened self-command recognition to concatenated argument lists and locked coverage of nested str(Path(__file__)) commands.
- Added AST pool inventory coverage, including aliases, qualified/context factories, omitted limits, and positional limits.
- Only safety tests and bounded malformed-invocation smoke checks ran; no gates, campaigns, builds, or measurement logic changes.

facts:
- Starting HEAD: 5dd559f8e677357cb31f803006c943ab037f0edc, branch orch/F26-test-pool-cap-and-ellipse.
- Read AGENT_GUIDE.md, emulation GOTCHAS, compatibility plan, F25/I02 reports, and RadialBlur ledger contract.
- `rg -n 'ThreadPoolExecutor|ProcessPoolExecutor|\bPool\(' tests tools/emulation -g '*.py'` plus AST constructor inventory found 59 sites in 46 files (58 ThreadPoolExecutor and one ProcessPoolExecutor). No multiprocessing Pool sites were present. Included the run_* fixture harness so the directory-wide safety test has no runner-name exemption.
- Both rotation_pf32_ellipse and zoom_pf32_ellipse already pass env=dict(os.environ, OLM_SELF_SPAWN_CHILD="1"), timeout=1800, and reject child fallback with SystemExit(2) before main(). The I02 report describes an older state than this checkout.
- Verification command below: 6 tests PASS in 8.194 seconds. Static self-spawn inventory: 48 scripts; pool inventory: 59 constructors. No first mismatch/failure.
- Runtime checks: 15 child invocations across five harnesses (missing production payload, unknown action, no arguments) all exit 2; three fast affected ellipse-script parent invocations with malformed --production also all exit 2. Each subprocess has a 10-second timeout. No actual-AEX entry was invoked.
- AST comparison against `git show HEAD:<path>` for all 46 runner files, normalizing only the added min cap and standalone os imports, found identical trees; in-memory compilation passed for all 46. This establishes measurement code was preserved.
- `git diff --check`: exit 0, no output. Scratch: 20 KiB; no build trees or background processes remain.

inference:
- Default pool concurrency is now at most two; OLM_TEST_JOBS=1 further reduces it. Explicit larger environment values can raise it up to the original limit, as required by the ticket formula. Invalid/nonpositive values fail during conversion/pool construction.
- The safety checks cover the reported recursive-dispatch and uncapped-constructor classes; this is not numerical conformance or a complete integration safety certification.

changed_files:
- orchestra/reports/F26-test-pool-cap-and-ellipse.md
- tests/test_pool_job_cap.py
- tests/test_self_respawn_guard.py
- tools/emulation/probe_olmradialblur_edge_noise_endpoints_32x18_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_pf16_quality_repeat_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_pf32_quality_repeat_compare_20260811.py
- tools/emulation/probe_olmradialblur_rotation_dual_strength_32x18_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_rotation_edge_offset_32x18_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_rotation_size_noise_components_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_rotation_size_variation_32x18_size_rotation.py
- tools/emulation/probe_olmradialblur_rotation_size_variation_components_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_zoom_edge_fade_offset_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_zoom_edge_offset_noise_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_zoom_size_noise_components_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_zoom_size_variation_32x18_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_zoom_size_variation_components_actual_aex_20260811.py
- tools/emulation/probe_radialblur_offset_promote_20261002.py
- tools/emulation/run_olmradialblur_type3_aexcompat_fixture_20260812.py
- tools/emulation/test_olmradialblur_brightness_size_noise_components_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_dual_strength_noise_32x18_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_dual_strength_size_components_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_dual_strength_size_noise_components_actual_aex_20260812.py
- tools/emulation/test_olmradialblur_inner_offset_pairwise_probe.py
- tools/emulation/test_olmradialblur_inner_size_edge_noise_components_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_noise_type1_pf16_pairwise_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_noise_type1_pf8_combo_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_noise_type2_block_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_offcenter_brightness_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_offset_matrix_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_pf16_ellipse_combo_20260811.py
- tools/emulation/test_olmradialblur_pf32_ellipse_32x18_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_pf8_quality_repeat_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_rotation_dual_size_noise_offset_components_actual_aex_20260812.py
- tools/emulation/test_olmradialblur_rotation_edge_offset_noise_components_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_rotation_offset_noise_components_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_rotation_pf32_edge_fade_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_rotation_pf32_edge_fade_intersections_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_rotation_pf32_ellipse_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_rotation_pf32_offset_mode3_noise_type1_actual_aex_20260810.py
- tools/emulation/test_olmradialblur_rotation_pf32_size_noise_combo_actual_aex_20260810.py
- tools/emulation/test_olmradialblur_rotation_pf32_strength5_noise_type1_actual_aex_20260810.py
- tools/emulation/test_olmradialblur_rotation_size_offset_components_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_rotation_typed_edge_32x18_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_size_edge_components_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_size_edge_noise_components_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_transform_worker_intersections_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_zoom_pf32_ellipse_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_zoom_pf32_noise_32x18_actual_aex_20260810.py
- tools/emulation/test_olmradialblur_zoom_pf32_noise_inner_actual_aex_20260810.py

verify:
- From the worktree, run:
  `mkdir -p orchestra/state/F26-test-pool-cap-and-ellipse`
  `TMPDIR="$PWD/orchestra/state/F26-test-pool-cap-and-ellipse" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=2 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' -m unittest tests.test_pool_job_cap tests.test_self_respawn_guard > orchestra/state/F26-test-pool-cap-and-ellipse/safety-tests.log 2>&1`
  `tail -10 orchestra/state/F26-test-pool-cap-and-ellipse/safety-tests.log`
  Expected: 6 tests, OK. Includes the three fast affected ellipse-script smoke checks, without campaigns.
- `git diff HEAD^ HEAD --check`
  Expected: exit 0, no output after this ticket commit.

next:
- Orchestrator review/merge, then retry I02 with OLM_TEST_JOBS=2 and its separate integration safeguards. No gate/evidence files were modified.
