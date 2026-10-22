status: done
summary:
- Restored ColorKey's hostless ROI gate by defining the missing threaded-rendering flag as SDK bit 27 (0x08000000).
- Production source, PiPL, F18 measured flags, and corpus records are unchanged.
- ROI gate passes; fresh original/Mac flag audit agrees 10/10; corpus replay matches 3/3 saved results.

facts:
- Base: 9a1591014569019245064d11b152ff73470203fa; branch: orch/F24-colorkey-hostless-roi-flag.
- Read AGENT_GUIDE.md, GOTCHAS.md, the plan, and the ColorKey ledger entries/forbidden-action row. MAIN, SDK, original AEX files, and cached workers were read-only; no worker rebuilt.
- Before the fix, the ROI command below failed compilation at mac/OLMColorKey/OLMColorKey.cpp:200:24: undeclared identifier PF_OutFlag2_SUPPORTS_THREADED_RENDERING. No pixels were compared.
- The adapter supplies its own SDK substitutes. Added only the missing numeric flag definition there. Existing unrelated placeholder flags are unchanged; production GLOBAL_SETUP was not edited.
- After the fix, the identical ROI command exits 0. Its one pytest-style test asserts `GENERIC_ROI_TILE pass=1 depths=3 classic=1 smart=1`, including nonzero origins, padded rows, and ASan/UBSan. The runner first prints `Ran 0 tests` for its empty unittest suite, then executes the pytest-style function; this is not a zero-test pass. Compiler output retains three sprintf deprecation warnings.
- F18 audit command below exits 0: plugin_count=10, flags_agree=10, smart=9; ABI control passes. All 20 original and 40 Universal Mac GLOBAL_SETUP calls return zero. ColorKey original PiPL/setup and fresh Mac PiPL/arm64/x86_64 setup agree at OutFlags=0x02000440, OutFlags2=0x08001400. All ten original flag pairs are unchanged from reports/route_flags_F18_after.json.
- Adjusted audit scratch validation to permit any directory inside this worktree's orchestra/state, allowing the required F24 directory; Xcode builds use -jobs 2. Measurements/assertions are unchanged.
- Corpus command below exits 0: requested=3, completed=3, replay_matches_saved=true. All three Smart results are exact. All three forced-Classic mismatches match the saved records (3, 120, 67 differing words respectively). First retained Classic mismatch: case000020, word 1, expected 00000000, actual 381b413f. This is existing diagnostic behavior, not a new mismatch.
- Replay used the corpus-recorded cached worker without overriding its hash check: /Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker; SHA256 544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2.
- Complete fresh measurements are committed in F24-route-flags.json and F24-colorkey-replay.json beside this report, including original/binary/source hashes and individual results.
- git diff --check passes. Generated probe/build trees removed; ticket scratch remains below 5 GiB. All launched commands completed; no background process remains.

inference:
- The regression was a missing declaration in the source-included hostless adapter. Restoring that declaration repairs compilation without altering production capability or pixel behavior.
- The bounded ROI/corpus results do not establish arbitrary-input equivalence or native AE lifecycle/MFR behavior.

changed_files:
- tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py
- tools/emulation/audit_route_flags_F18.py
- orchestra/reports/F24-route-flags.json
- orchestra/reports/F24-colorkey-replay.json
- orchestra/reports/F24-colorkey-hostless-roi-flag.md

verify:
Run sequentially from this worktree (existing MAIN assets and SDK required):

```sh
s="$PWD/orchestra/state/F24-colorkey-hostless-roi-flag"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 scripts/run_olm_generic_beta_gate.py --run-test-file tests/test_olmcolorkey_generic_roi_tile.py > "$s/roi-after.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/emulation/audit_route_flags_F18.py --scratch "$s/audit" --require-agreement --report "$s/flags.json" > "$s/flags.log" 2>&1
python3 tools/fuzz/run.py --plugin olmcolorkey --replay tests/fuzz_corpus/olmcolorkey --jobs 2 --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/unused-corpus" > "$s/replay.log" 2>&1
git diff --check
```

Expected: all commands exit 0; flags summary 10/10 agreement, 9 Smart; replay requested/completed 3/3 and replay_matches_saved=true, Smart exact 3/3 with unchanged Classic diagnostics. Fresh compiled binary hashes may vary.

next:
- Orchestrator can resume I01 integration testing. No remaining F24 work; known Classic diagnostics and native-host coverage remain separate scopes.
