status: blocked
summary:
- Rebound both retained PF32 inputs to new original-AEX public Smart expectations, preserving all old binary files.
- Default and F30 workers agree exactly; current Mac Smart passes both new fixtures.
- Scoped the retained test and DG runner away from legacy Classic, citing F18.
- Required full-suite green is blocked by installed identity drift, missing historical assets and stale evidence bindings outside this ticket.

facts:
- Base: `e0045b48d21ab44511de0b6903dc57cabdef1add`, branch `orch/F35-dg-fixture-rebind`.
- `PYTHONDONTWRITEBYTECODE=1 python3 orchestra/reports/F35-generate-fixtures.py` exited 0. It imports and runs F34's harness with scratch redirected to F35, then copies only `default-smart.raw` into the new expected files after byte equality with `F30-smart.raw`. Neither expected file is generated from Mac output.
- Original AEX SHA256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
- Default worker SHA256: `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`; F30: `8b51d0456ff55aa2034a0bbb00b822bd2339cbe27247021c289170a78a3fb53b`. Workers and original AEX used by absolute path; no rebuild/copy.
- Each input/output is 2992 bytes, ARGB FLOAT32, 17x11, rowbytes 272, origin zero, downsample 1:1. All 12 controls and worker runtime statuses are in each fixture's provenance JSON.
- Zero-input new output SHA256: `a793be73e5af89ff7572bcd6750c102ad3ccf6fa8c7a055c5f8cef4574947679`. Controlled-input new output: `766f4fbde7835110aa3bf782024beec13f9cd2afe2c932fd83c63fcdde603034`.
- Both workers vs Mac Smart: 0 mismatched bytes for both inputs (4 comparisons); first mismatch: none. Against obsolete expectations, Smart differs by 748 bytes for zero input (first offset 2, alpha 1.0 vs 0.0), and 1818 bytes for controlled (first offset 4, red words `0x3de0e0e1` vs `0x3f800000`).
- DG fixed-fixture runner exited 1: 22 commands, 2 pass / 20 fail. Rebound PF32 test passes both fixtures; runner integration unit module also passes. First failure: installed executable hash `ce48b9ebf92bb1b66db9e3da1c0c17f4b176553a4f5097fed0b5f5630d6cb1e5` differs from pinned `9a97a076c118fd1015f40d922bf7f21be7a041f1f049a0e465cc0bc9cd1cd349`. Further failures include worktree-local missing original AEX/disassembly, historical handoff binaries/runtime packages, and old source-hash bindings. No installed identity or gate was altered.
- DG unittest discovery exited 1: `Ran 140 tests in 19.662s`, `FAILED (failures=12, errors=60)`. First error is `test_pinned_live_closure` in the actual-AEX powf closure suite. Full failed test names, runner commands, and log hashes are retained in `F35-validation.json`; local full logs are in ticket scratch.
- No production, release gate, ledger, other-plugin code, or MAIN files changed. Original fixture binaries remain unchanged. All subprocesses completed. Scratch build removed; remaining logs/raw evidence occupy less than 1 MiB.

inference:
- The F35 expectation mismatch is resolved under the exact public Smart contract. Full-suite failures expose older installation/evidence/environment dependencies, not a mismatch in these new fixture bytes. Repairing or repinning those unrelated contracts would exceed this ticket, so the required all-pass outcome is not claimed.
- These are original-AEX Unicorn CPU results with host callbacks, not native Windows/AE validation.

changed_files:
- `orchestra/reports/F35-generate-fixtures.py`: reproducible F34-based generation.
- `orchestra/reports/F35-validation.json`: actual validation summaries and log hashes.
- `orchestra/reports/F35-dg-fixture-rebind.md`: report.
- `refs/fixtures/olmdistancegradation_pf32_owner_17x11_public_smart_20261023/{source_argb_f32.bin,output_argb_f32.bin,provenance.json}`.
- `refs/fixtures/olmdistancegradation_pf32_owner_17x11_controlled_source_public_smart_20261023/{source_argb_f32.bin,output_argb_f32.bin,provenance.json}`.
- Both old fixture directories' `README.md`: superseded notes citing F34.
- `tools/emulation/test_olmdistancegradation_pf32_effectmain_fixture_20260805.py`: public Smart replay via the existing production adapter; explicit controls and provenance hashes checked.
- `scripts/run_olm_mac_fixed_fixture_regression_20260805.py`: exclude 12 legacy DG Classic probes with F18 explanation; retain scripts as historical diagnostics.

verify:
```sh
mkdir -p orchestra/state/F35-dg-fixture-rebind
export TMPDIR="$PWD/orchestra/state/F35-dg-fixture-rebind"
export TMP="$TMPDIR" TEMP="$TMPDIR" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 orchestra/reports/F35-generate-fixtures.py > "$TMPDIR/generate.log" 2>&1
# Expected exit 0, two worker-identical outputs with hashes above.
python3 tools/emulation/test_olmdistancegradation_pf32_effectmain_fixture_20260805.py > "$TMPDIR/fixture.log" 2>&1
# Expected exit 0, 2 x 2992 bytes, zero mismatches.
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' scripts/run_olm_mac_fixed_fixture_regression_20260805.py --plugin distancegradation > "$TMPDIR/regression.log" 2>&1
# Current environment: exit 1, 20 failures; rebound fixture passes.
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' -m unittest discover -s tests -p 'test_olmdistancegradation*.py' > "$TMPDIR/unit.log" 2>&1
# Current environment: exit 1, 140 tests, 12 failures / 60 errors.
git diff --check
# Expected exit 0.
```

next:
- Orchestrator review/merge the fixture rebind separately from suite repair.
- Follow-up ticket: make historical DG validations worktree-aware using MAIN assets read-only, and adjudicate stale installed/source/evidence bindings. Do not silently repin identities or suppress failures to claim full-suite green.
