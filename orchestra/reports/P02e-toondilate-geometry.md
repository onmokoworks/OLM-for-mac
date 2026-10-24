status: done
summary:
- Smart pre-render forwards the requested rectangle without a Mac-only halo.
- Smart rendering uses input-sized distance propagation and bounded local output accesses, matching the AEX.
- Radius uses float32 X numerator/denominator and float32 multiplication before ceiling.
- Realistic seeds 1 and 20261024: each 100/100 exact, 0 mismatch/refusal/unavailable; default 300/300 exact before and after.
- All 323 historical and 236 new labelled corpus cases replay Smart-exact; unit outcomes unchanged.

facts:
- Read AGENT_GUIDE, emulator GOTCHAS, ToonDilate ledger entries and compatibility plan. Classic public owner remains its existing no-op; release gate, ledger, MAIN, emulator source and installed bundles were not changed.
- Baseline command: `python3 tools/fuzz/run.py --plugin olmtoondilate --geometry realistic --seed 1 --n 100 --jobs 1 --shrink-attempts 0 --scratch "$TMPDIR/before-realistic" --report "$TMPDIR/before-realistic.json" --corpus "$TMPDIR/baseline-corpus"`. Smart 63 exact / 37 mismatch / 0 refusal / 0 unavailable. First index 0: oracle rect [5,4,6,5], candidate [0,0,11,7].
- Removing halo expansion alone gave 68 exact / 32 pixel mismatches. First index 0 then had matching bounds but 3 differing bytes; first byte 1, oracle d6 versus candidate 29. This exposed the separate local-coordinate rule, rather than refuting the rectangle fix.
- Read MAIN `disasm/OLMToonDilate.aex.asm.txt` (recorded F52c SHA d6bf7f8e5760b555f16ad1ce58ca1b9cfb09c15bb050c9ae85dd6a856c79607f). At 0x1801a5ad4..0x1801a5b26: CVTDQ2PS/DIVSS/MULSS followed by truncation and positive-fraction increment. At 0x1801a5b29..0x1801a5b36 the input height/width define the distance plane. At 0x1801a5dd1..0x1801a5e1d output width/height bound local source/destination addresses. Copy helper 0x1801ac8b0 returns without writing when either address is null.
- Full fix: same realistic command with seed 1 and seed 20261024, each n100, serial jobs=1: Smart 100 exact, 0 M/R/U. Final-source `geometry_witnesses.py` repeated both seeds and 36 boundary/request cases: 236 exact. `run.py --replay tests/fuzz_corpus/olmtoondilate_P02e_realistic` independently replayed all 236 exact.
- `run.py --plugin olmtoondilate --seed 1 --n 300 --jobs 1 --shrink-attempts 0` before and after: 300 Smart exact, no non-exact cases. Generic replay of `tests/fuzz_corpus/olmtoondilate` and `olmtoondilate_T13`: 300 + 23 Smart exact. Saved-object comparisons are false for historical records; these contain older refusals/metadata and are not rewritten. Classic remains no-write.
- Oracle F52c SHA: 4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e. Final plugin source SHA: 15ec41c52d9da9872cad1ccd573006da4fc6d316eaa1de50050101c31fd4e8b2. Full provenance, report hashes and first failures are in `P02e-evidence/campaigns.json`; cases retain input/oracle/candidate hashes.
- Initial unit invocation with MAIN emulation Python failed because pytest was absent. Created a ticket-local venv and installed pytest/numpy/pillow; no MAIN environment changes. `OLM_TEST_JOBS=1 "$TMPDIR/venv/bin/python" -m pytest -q tests/test_olmtoondilate*.py`: before **12 failed, 53 passed, 13 errors**; final **12 failed, 53 passed, 13 errors**, identical failing test IDs. Full lists/diagnostics are in `P02e-evidence/unit-comparison.json`, `unit-before.log`, `unit-final.log`. Failures concern historical source/report hashes, missing installed plugin/AEX or historical artifact paths, and prior capture-gate claims. No additional failure remains.
- Updated three plugin unit tests' obsolete halo/origin/source-text assertions. ROI ASan/UBSan test additionally checks oversized output, odd stride, ignored extreme origins, and untouched padding/outside-plane bytes. Both generic sanitizer and ROI sanitizer tests pass. `git diff --check` passes.

inference:
- The original does not spatially crop by world origin: its geometry is local to each world. Input-sized propagation plus skipped out-of-output neighbor copies explains the observed ROI differences; rendering a full temporary image and cropping it is not equivalent.
- X downsample determines radius; Y scale, extent and pixel aspect do not enter this worker's observed pixel arithmetic. This is supported by disassembly and the bounded realistic witnesses, not a claim over all possible host states.
- Expanded requests in these negotiated tests produce clipped result rectangles. Oversized output allocation has source/sanitizer coverage, not independent expanded-allocation AEX evidence. Native AE remains untested.

changed_files:
- mac/OLMToonDilate/OLMToonDilate.cpp
- mac/OLMToonDilate/tests/geometry_witnesses.py
- tests/test_olmtoondilate_generic_beta.py
- tests/test_olmtoondilate_roi_safety.py
- tests/test_olmtoondilate_typed_core.py
- tests/fuzz_corpus/olmtoondilate_P02e_realistic/* (236 cases and README)
- orchestra/reports/P02e-toondilate-geometry.md and P02e-evidence/*

verify:
Run from this worktree (all fuzz jobs serial):
```sh
export TMPDIR="$PWD/orchestra/state/P02e-toondilate-geometry"
export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$TMPDIR"
python3 mac/OLMToonDilate/tests/geometry_witnesses.py > "$TMPDIR/verify-witnesses.log" 2>&1
# Expected: 236 exact; exit 0. Rewrites only this labelled corpus.
python3 tools/fuzz/run.py --plugin olmtoondilate --seed 1 --n 300 --jobs 1 --shrink-attempts 0 --scratch "$TMPDIR/verify-default" --report "$TMPDIR/verify-default.json" --corpus "$TMPDIR/verify-default-corpus" > "$TMPDIR/verify-default.log" 2>&1
# Expected: 300 Smart exact, 0 mismatch/refusal/unavailable.
for corpus in olmtoondilate olmtoondilate_T13 olmtoondilate_P02e_realistic; do
  python3 tools/fuzz/run.py --plugin olmtoondilate --jobs 1 --replay "tests/fuzz_corpus/$corpus" --scratch "$TMPDIR/verify-$corpus" --report "$TMPDIR/verify-$corpus.json" > "$TMPDIR/verify-$corpus.log" 2>&1
done
# Expected Smart exact counts: 300, 23, 236; saved-object equality is not the acceptance metric.
python3 -m venv "$TMPDIR/venv"
"$TMPDIR/venv/bin/pip" install pytest numpy pillow > "$TMPDIR/verify-pip.log" 2>&1
"$TMPDIR/venv/bin/python" -m pytest -q tests/test_olmtoondilate*.py > "$TMPDIR/verify-unit.log" 2>&1
# Expected: 53 passed, 12 historical failures, 13 historical errors.
git diff --check
```

next:
- Native AE Smart preview/ROI confirmation and independent expanded-allocation AEX testing are separate follow-ups. No install or release claim is made here.
