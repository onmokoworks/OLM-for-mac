status: done

summary:
- Three clusters closed in separate commits: tiny Smart ownership, PF8 Alpha normalization, and scalar Alpha Gaussian Length2–1000.
- Smart seed1: 48 -> 103 -> 130 -> 134 exact; seed4: 40 -> 93 -> 128 -> 131 exact, with zero admitted mismatches throughout.
- All baseline-exact Smart outputs persist; corpus changes only toward exact and strict production replay passes 8/8.
- Independent matrices and final 600-route ASan/UBSan replay pass; Length1 retains a reproducible excluded counterexample.
- The ticket's three-cluster stop condition is met; remaining numerical families need follow-up tickets.

facts:

Base `1b656d418ba44543da2225097108796f0937d9cc`, branch `orch/C04-kira-smart`.
Read AGENT_GUIDE, compatibility plan, GOTCHAS, KiraKira ledger restrictions, T06/F03/F04/F09/F10/F11/F12 and F18. MAIN, original binaries, external emulator sources/workers, release gates and ledger remain unchanged. No rebuild, push or install.

Final cumulative results (exact / mismatch / refusal, n300, jobs2):

| State | Seed1 | Fresh seed4 |
|---|---|---|
| Base |48 / 0 / 252|40 / 0 / 260|
| Tiny ownership, `cc42826f` |103 / 0 / 197|93 / 0 / 207|
| PF8 Alpha, `e7f23f66` |130 / 0 / 170|128 / 0 / 172|
| Scalar Alpha Gaussian, this commit |134 / 0 / 166|131 / 0 / 169|

Detailed later-cluster reports: [PF8](C04-kira-smart-pf8.md), [Gaussian](C04-kira-smart-gaussian.md). Machine records are `reports/fuzz/olmkirakira_smart_C04_{tiny,pf8,gaussian}.json`; each binds its own source revision and evidence. The following first-cluster facts are historical; final results are the table above and the two linked reports.

Machine evidence: `reports/fuzz/olmkirakira_smart_C04_tiny.json` binds source/core/worker/AEX hashes, campaign records and transitions, independent matrices, original-AEX traces, corpus comparisons, negative tests and actual test logs. The reproduction programs never update corpus expectations.

Original AEX SHA256: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7` at MAIN `plugins_2025/OLMKiraKira.aex`. Retained worker SHA256: `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`, `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`. INDEX indexes RadialBlur workers; this is the unchanged retained KiraKira worker used by the prior tickets.

The initial requested default-shrink campaign reached 300 records but lost indices 71/171 to `PermissionError: [Errno 1] Operation not permitted` in the framework's `os.killpg` timeout cleanup during shrinking. Its 46 exact/252 refusal/2 framework errors are **not** a usable baseline. No tool approval rejection occurred and no permissions were altered. Repeating the full campaign with shrinking disabled and the base source produced 48 exact/0 mismatch/252 refusal, 287 AEX Smart outputs/13 rejects, no framework errors. The failed transcripts are retained in evidence. No fuzz framework code was changed.

F17 now compares each Mac route with its corresponding original route. Accordingly Classic is 48 mismatches/252 refusals for seed 1 and 40/260 for seed 4, unchanged before/after. These differ from historical cross-route F12 numbers. F18 selects Smart as KiraKira's AE target; no Classic numerical fix is claimed here.

| Campaign (n300/jobs2) | Smart exact | Mismatch | Refusal | Uncompared | Original Smart output/reject |
|---|---:|---:|---:|---:|---:|
| seed 1 before | 48 | 0 | 252 | 0 | 287/13 |
| seed 1 consistent owner + tuple gates off, ASan/UBSan | 210 | 77 | 0 | 13 | 287/13 |
| seed 1 after | 103 | 0 | 197 | 0 | 287/13 |
| seed 4 before | 40 | 0 | 260 | 0 | 281/19 |
| seed 4 consistent owner + tuple gates off, ASan/UBSan | 219 | 62 | 0 | 19 | 281/19 |
| seed 4 after | 93 | 0 | 207 | 0 | 281/19 |

The largest pre-change Smart guard cluster was tiny dimensions: 163 seed-1 inputs. Within it, seed 1 has 21 zero-ray and 34 other Alpha/box cases exact with gates off; seed 4 has 12 and 41. Every one is exact after promotion. The old 48/40 exact cases retain their complete Smart result records and all Classic records are identical. All other cases retain refusal status; no missing AEX output is admitted. The verifier independently renders all 600 final Smart campaign cases under ASan/UBSan and compares output hashes with the normal builds.

General rule and cause:

- F04 proved the old request-only bypass normalized tiny requests to the historical 5x3 frame, causing checkout-geometry failure. A consistent owner predicate was needed independently of numerical tuple admission.
- `IsSmartOwnerFullFrameDimensions` now accepts positive dimensions under the existing 4096-side and 4096x2160-area caps. Only Smart dimension extraction, predata and world ownership consume it. Full-frame request containment, 1:1 downsample, zero origins, matching dimensions, storage/format/span/nonoverlap checks and finite-SDR source checks remain.
- Existing zero-ray and PF16/PF32 Alpha/box predicates supply the tiny numerical admission. Other generic Mode 1–4 admissions still use their former geometry predicates; Classic is unchanged. No render arithmetic changed.
- Known 5x3 full-frame requests also carry the generic owner flag, allowing these independently validated tuples while preserving exact-fixture precedence. The numerical matrix explicitly includes 5x3.
- Original `18114c8c0` pre-render is re-executed for 10 geometries x 3 depths: 30/30 original request byte sequences and returned full-frame rectangles match the checkout contract. No numerical function is detoured.
- Independent production matrix: 378 zero-ray cases (7 geometries x 3 depths x 3 modes x 6 channels; both merge modes across the matrix), plus 168 Alpha/box cases (7 geometries x 2 depths x 2 modes x 6 ray patterns). Includes 1x1, row, column, 3x3, 5x3, 8x6, 7x11, independent edge/random pixels, colors/default ramps, gain/angle/length variation and odd byte strides. All 546 outputs match original Smart under ASan/UBSan. Earlier gate-off matrices were 324 zero-ray and 144 Alpha cases before adding the 5x3 row; all passed.
- The retained C60/index148 PF16 9x1 case is traced through **production Mac Smart**. Source, seed, five rays, glow and composed are 9/9 exact; final AEX/public/Mac SHA256 `42d2fa2c4a87995fdb12478d5d894685848cbb65acd71e1329b6029e56b85eda`. The original trace's import-free reader ABI check passes. TLS/allocation/CRT/Python-libm scaffolding is retained; no native AE/UCRT proof is inferred.
- Eight one-away negative cases remain clean refusals: unsupported channel/mode, approximation, non-unit strength/opacities, excluded signed-angle endpoint and PF16 above SDR. An attempted width4097 negative was rejected by the **test host CLI** (exit64), before plugin entry; it is not claimed as plugin cap evidence and was removed from that matrix. Production cap checks remain unchanged.

Corpus before/after:

| Saved input | Fresh Smart before -> after | Expectation action |
|---|---|---|
| production index1 | refusal -> exact, hash `c017c95da10b7e7ee3b2b1708022513c3d537a168094445298ef799e5ffa1cc1` | Updated, previous full result retained |
| T06 shrunk index148 | refusal -> exact, hash above | Historical gate-off expectation retained |
| other 68 | unchanged status and output bytes | Numerical expectations unchanged |
| production indices8/16 | refusal -> refusal; callbacks `0 0 0 0 0` -> `1 1 1 25 25` | Lifecycle metadata explicitly rebased, previous full results retained |

The two metadata changes reflect reaching the balanced parameter checkout/checkin stage after ownership validation; no destination bytes change on refusal. Strict production replay is 5/8 before this explicit rebaseline, **8/8 after**. All original reference records and Classic results stay unchanged. No retained mismatch is reclassified as exact without a fresh original-AEX comparison.

Existing tests: 25 fast tests pass; compiled generic-beta ASan/UBSan test passes (54 internal rows, including HD, 50.201 seconds). Only its read-only SDK root is rebound to MAIN; source and harness remain in this worktree. `git diff --check` passes. Scratch is below 5 GiB and completed build directories are removed by the tools.

Additional boundaries measured during the first cluster (subsequent outcomes are in the linked reports):

- Broad PF8 Alpha/box admission is refuted by independent matrix index48 (5x3, ramp): 1/60 bytes differs, first byte5 AEX `d2`, Mac `d3`. A no-ramp variant matrix is refuted at index72 (7x11): 2/308 bytes differ, first byte53 AEX `d9`, Mac `da`. Both provided new counterexample values; neither was admitted in the first commit. The second commit fixes their first divergent operation before admission. Index72's original full-caller trace binds to the public worker and first differs at **glow**, after exact source/seed/rays.
- Enabling the existing Gaussian operation for positive tiny helper dimensions in a scratch source makes C30/210, C31/23 and C32/232 all captured stages and final bytes exact; all three original traces bind to public Smart. An independent PF16/PF32 directional Gaussian gate-off matrix has 84/84 exact outputs under sanitizers. At this first-cluster stage, production/corpus acceptance had not yet been performed. The third commit supplies it for Length2–1000 and excludes the measured Length1 failure.

inference:

The storage geometry restriction had survived the F11 numeric fixes; those fixes now make the bounded Alpha/box tiny branch promotable. Independent matrices, two seeds, original pre-render behavior and the bound C60 stages support the general ownership/admission change. Finite probes do not establish arbitrary native AE, UCRT, custom ramps, ROI/downsample, HDR or all floating inputs.

Subsequent paired traces establish the PF8 normalization operation and the tiny scalar Gaussian omission as the two additional causes fixed in this ticket. Their detailed reports distinguish observed evidence from unresolved inference. Color seeds, non-unit controls and the Length1 one-word residual remain unproven and are not newly admitted.

changed_files:
- `core/kirakira_gaussian.h`
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/verify_kirakira_smart_C04.py`
- `tools/emulation/trace_kirakira_smart_C04.py`
- `tools/emulation/summarize_kirakira_smart_C04.py`
- `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000001.json`
- `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000008.json`
- `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000016.json`
- `reports/fuzz/olmkirakira_smart_C04_tiny.json`
- `reports/fuzz/olmkirakira_smart_C04_pf8.json`
- `reports/fuzz/olmkirakira_smart_C04_gaussian.json`
- `orchestra/reports/C04-kira-smart.md`
- `orchestra/reports/C04-kira-smart-pf8.md`
- `orchestra/reports/C04-kira-smart-gaussian.md`

verify:

Run from this worktree; use scratch for all temporary files and logs:

```sh
s="$PWD/orchestra/state/C04-kira-smart/recheck-final"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 1b656d418ba44543da2225097108796f0937d9cc:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/base.cpp"
for seed in 1 4; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/base.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/before-seed$seed.json" --corpus "$s/before-seed$seed-corpus" > "$s/before-seed$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/after-seed$seed.json" --corpus "$s/after-seed$seed-corpus" > "$s/after-seed$seed.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --family zero --before-source "$s/base.cpp" --scratch "$s/recheck-zero" --report "$s/recheck-zero.json" > "$s/recheck-zero.log" 2>&1
for family in alpha pf8 pf8-flat pf8-boundary gaussian-all gaussian-boundary; do
  python3 tools/emulation/verify_kirakira_smart_C04.py --family "$family" --scratch "$s/recheck-$family" --report "$s/recheck-$family.json" > "$s/recheck-$family.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/base.cpp" --campaign-dir "$s" --campaign-only --scratch "$s/recheck-campaigns" --report "$s/recheck-campaigns.json" > "$s/recheck-campaigns.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --gaussian-negatives --scratch "$s/recheck-negative" --report "$s/recheck-negative.json" > "$s/recheck-negative.log" 2>&1
"$py" tools/emulation/trace_kirakira_smart_C04.py --corpus-index 148 --production --require-exact --scratch "$s/recheck-trace" --report "$s/recheck-trace.json" > "$s/recheck-trace.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/recheck-replay.json" --corpus "$s/recheck-replay-corpus" > "$s/recheck-replay.log" 2>&1
```

Expected: baseline 48/0/252 and 40/0/260; final 134/0/166 and 131/0/169. All baseline-exact records unchanged. The seven independent matrix families execute 378+168+120+120+20+180+30 = 1,016 exact comparisons (not a claim of unique inputs across families). Seventy cumulative corpus comparisons have no numerical regression; 600 sanitized campaign routes pass; 10 negative refusals; 9 exact tiny trace stages/public binding; strict replay 8/8. The linked reports give the PF8/Gaussian paired traces and fixed-admission sample-audit commands, including the expected-red Length1 witness.

Existing fast tests and compiled sanitizer (final measured results: 25 tests pass; 54 internal sanitizer rows pass, including HD):

```sh
PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820 test_olmkirakira_merge2_float_oracle_20260728 test_olmkirakira_outer_compose_oracle_20260728 test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.Mode4FullCallerHostlessExactTests.test_mac_production_owns_the_bounded_highlight_and_typed_writer > "$s/fast.log" 2>&1
PYTHONPATH=tests python3 - > "$s/sanitizer.log" 2>&1 <<'PYTEST'
import pathlib, unittest
import test_olmkirakira_generic_beta_sanitizers_20260820 as test
test.ROOT = pathlib.Path('/Users/onmk/Documents/Projects/Personal/OLM as')
r = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(test))
raise SystemExit(not r.wasSuccessful())
PYTEST
git diff --check
```

next:
- Stop after the three closed clusters. Final seed1 has 166 refusals: 13 lack original Smart output, and 153 have an AEX-rendered reference. Gate-off diagnostic results for those 153 are 84 exact / 69 mismatch; the 84 need general branch proofs before admission.
- Largest remaining diagnostic parameter group is Channel1/Mode2 (27 cases). Trace non-unit control/seed/opacity materialization next; these group labels are not established root causes.
- Separate follow-ups: four-plane color seeds, Mode3 Length1 and Highlight, approximation, native AE/UCRT, custom ramps, HDR and ROI/downsample. No push was performed.
