status: done
summary:
- Guarded 47 previously unguarded self-spawning scripts; the existing reference guard remains unchanged.
- Children receive OLM_SELF_SPAWN_CHILD=1; unmatched actions/child fallthrough cannot start parent campaigns.
- Self-spawn subprocess.run calls have 1800-second timeouts; existing Popen wait/communicate timeouts are preserved.
- Added static coverage and nine bounded malformed-child executions across three representative harnesses.
- No campaigns, emulator workers, builds, measurement changes, pool changes, or release-gate changes were run/made.

facts:
- `rg -l -U 'sys\.executable,\s*(str\()?(Path\()?__file__|sys\.executable,\s*sys\.argv\[0\]' tools tests scripts refs/scripts -g '*.py' -g '!**/.venv/**'` found 48 candidates. `handoffs` does not exist in this checkout.
- AST inventory confirms 48 executable self-spawn scripts. The additional tools/perf/run_generic_beta_smoke.py occurrence records invocation provenance, not a spawn. The sys.argv[0] search found argument forwarding/usage, no additional self-spawns.
- The generic beta runner (scripts/run_olm_generic_beta_gate.py) is one of those self-spawners; only its child environment and dispatch guard changed. The release gate scripts and release evidence files were untouched.
- Guard suite: 2 tests PASS in 2.481 seconds; static coverage 48 scripts, nine real subprocess checks all exit 2 (three scripts × missing production payload / unknown action / no arguments).
- In-memory compile of all 48 inventoried scripts succeeds. `git diff --check` succeeds.
- Existing beta-runner unit suite: 20 tests, 19 pass, 1 failure: test_gate_self_and_required_dependency_closures_are_manifested. Missing hashes are Util/AEGP_SuiteHandler.cpp, Util/AEGP_SuiteHandler.h, Util/MissingSuiteError.cpp.
- Re-executing that single failing test with the runner source from `git show HEAD:scripts/run_olm_generic_beta_gate.py` also fails (1 test, 1 failure). This isolates the missing dependency failure from this patch.
- Scratch logs are under orchestra/state/F25-self-respawn-guard (about 200 KiB before final report); no build trees or ongoing background processes remain.

inference:
- The environment guard breaks the observed malformed-child-to-parent recursion even when a child loses its action argument. Explicit unknown-action rejection also protects manual malformed invocations.
- argparse-owned parent options (--full, --timeout, --verify-report and beta-runner options) remain valid; argparse rejects unmatched options and the environment guard blocks child fallback.
- PF16 ellipse dispatch now validates known child actions and argument counts before parsing, so malformed modes reach exit 2.
- The unrelated beta manifest failure is due to absent checkout dependencies, not the self-spawn changes. No numerical conformance claim is made.

changed_files:
- scripts/run_olm_generic_beta_gate.py
- tools/emulation/probe_olmradialblur_edge_noise_endpoints_32x18_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_pf16_quality_repeat_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_pf32_quality_repeat_compare_20260811.py
- tools/emulation/probe_olmradialblur_rotation_dual_strength_32x18_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_rotation_edge_offset_32x18_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_rotation_size_noise_components_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_rotation_size_variation_32x18_size_rotation.py
- tools/emulation/probe_olmradialblur_rotation_size_variation_components_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_zoom_dual_strength_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_zoom_edge_fade_offset_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_zoom_edge_offset_noise_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_zoom_size_noise_components_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_zoom_size_variation_32x18_actual_aex_20260811.py
- tools/emulation/probe_olmradialblur_zoom_size_variation_components_actual_aex_20260811.py
- tools/emulation/test_olmblur_case0006_fullentry.py
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
- tools/emulation/test_olmradialblur_zoom_inner24_probe.py
- tools/emulation/test_olmradialblur_zoom_pf32_ellipse_actual_aex_20260811.py
- tools/emulation/test_olmradialblur_zoom_pf32_noise_32x18_actual_aex_20260810.py
- tools/emulation/test_olmradialblur_zoom_pf32_noise_inner_actual_aex_20260810.py
- tests/test_self_respawn_guard.py
- orchestra/reports/F25-self-respawn-guard.md

verify:
- From this worktree, run:
  `PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' -m unittest tests.test_self_respawn_guard`
  Expected: 2 tests, OK; no campaign launched. The MAIN venv supplies numpy/Unicorn imports only.
- `git diff HEAD^ HEAD --check`
  Expected: no output, exit 0 after this ticket commit.
- Optional existing runner checks:
  `TMPDIR="$PWD/orchestra/state/F25-self-respawn-guard" PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' -m unittest tests.test_run_olm_generic_beta_gate`
  Expected in this checkout: 20 tests, one known missing-Util dependency failure above; other 19 pass.

next:
- Orchestrator review and merge; no full campaign is needed for this ticket.
- Separately provision the missing Util dependencies if the beta manifest unit suite needs to pass in worktrees.
