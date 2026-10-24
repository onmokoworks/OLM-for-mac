status: done
summary:
- Restored original Classic output-extent iteration for both key-mask and smoothing passes; copies and contour access retain world dimensions.
- Realistic-v1 seed 1/n100: 65 exact, 0 mismatches, 0 Mac-only refusals, 35 unavailable; fresh seed 20261024: 63/0/0/37.
- Default seed 1/n300: 205 exact, 95 unavailable, no exact→non-exact or output-hash regressions; all 29 existing corpus cases remain exact.
- Added 224 separately labelled realistic/boundary corpus records; standard replay matches all 224 saved results.
- Unit baseline and final totals: 39 tests, same 4 failures and 4 errors; PF32 refusal and non-original Smart policy retained.

facts:

The baseline commit was `5a3670853c13989907203bf8aed3bd78289b4419`.
Only the Smoother production source, plugin-specific verification scripts, corpus,
and this report/evidence were changed. No oracle rebuild, MAIN write, ledger,
release gate, push, or other plugin source edit was performed.

Static evidence read from MAIN `disasm/OLMSmoother.aex.asm.txt`:

- PF16 `0x18000122c..0x180001253`: output extent bottom minus top; host copy
  receives null source/destination rects. `0x180001260..0x180001297` allocates
  from source dimensions.
- PF16 `0x1800012f0..0x180001322` passes output world+0x2c (extent) to key-mask
  iteration, and `0x180001346..0x180001399` passes the same extent to smoothing.
- PF8 `0x18000144c..0x1800014b7`, `0x180001510..0x180001542`, and
  `0x180001566..0x1800015b9` have the corresponding copy/allocation/iteration flow.
- Suite forwarding at `0x1800068b0..0x180006975` preserves the area argument.
  Read-only F52c host `x64/iterate_and_suites.rs:411` reads that area, checks its
  bounds, and iterates its rectangle. This is host-model evidence, not native AE.

The implementation uses output extent only to select callback centers, including
for the temporary key-mask world. It does not crop contour reads or neighbouring
writes. Classic ignores input extent, downsample and aspect metadata for its
pixel arithmetic; supplied world dimensions already describe sampled pixels.
Smart's existing validation/dispatch defaults remain unchanged. Out-of-bounds
output extent is validated; empty extent performs copies with no iteration.
Empty-extent original output is **not** established by this oracle (see below).

Commands actually run (long output redirected under ticket scratch):

1. `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/verify_olmsmoother_P02g.py --label before`
   ran serially before the source edit. It uses the same `sample(...,'realistic')`
   and adapter/evaluate functions as `measure_F52c.py`, with a fresh seed and
   Classic-only comparisons. The initial driver did not yet include the 24
   focused boundary inputs.
2. `... verify_olmsmoother_P02g.py --label after --retain`, then
   `... verify_olmsmoother_P02g.py --label final --retain` after adding boundaries
   and refining comments. The final run covers 553 inputs (200 realistic, 300
   default, 29 existing corpora, 24 focused boundaries).
3. `... run_olmsmoother_P02g_units.py` with `OLM_TEST_JOBS=1`, ticket-local
   `TMPDIR/TMP/TEMP`, and serial unittest loading. The initial script filename
   was `test_olmsmoother_P02g_units.py`, renamed to avoid discovery side effects.
   Before/after class runs: **34 tests, 4 failures, 3 errors**, respectively
   44.971/45.130 seconds. Five module-level function tests were then run with
   `--functions-only`, and against the original source with
   `--functions-only --baseline-source 5a3670853c13989907203bf8aed3bd78289b4419`:
   **same 1 error** in both. The complete final runner: **39 tests, 4 failures,
   4 errors**, 45.448 seconds. Logs are retained below.
4. `python3 tools/fuzz/run.py --plugin olmsmoother --jobs 1 --replay tests/fuzz_corpus/olmsmoother_P02g_realistic --scratch orchestra/state/P02g-smoother-geometry/replay --report orchestra/state/P02g-smoother-geometry/replay.json --budget-minutes 30`
   returned `replay_complete`, **224/224 match saved**, in 5.6871 seconds.
5. `git diff --check` passed. Before/final records were compared by group,
   seed/index, status and raw output hash: **0 exact regressions**, **0 existing
   corpus hash changes**, **no first mismatch**.

| Campaign | Before E/M/R/U | Final E/M/R/U |
|---|---:|---:|
| realistic seed 1/n100 | 31/0/34/35 | 65/0/0/35 |
| realistic seed 20261024/n100 | 32/0/31/37 | 63/0/0/37 |
| default seed 1/n300 | 205/0/0/95 | 205/0/0/95 |
| existing corpus (all 29) | 29/0/0/0 | 29/0/0/0 |
| focused boundary/key cases | not run | 20/0/0/4 |

E/M/R/U mean exact/mismatch/Mac-only-refusal/oracle-unavailable; U has precedence.
All 72 realistic U cases are the original's advertised PF32 depth rejection.
The four focused U cases use empty extents: host rejects them before plugin
execution with `aex_guest_error: rectangle outside sampled world`. Nonempty
focused cases cover PF8/PF16, key off/on, full/interior/corner/one-column extents,
1/4 sampling, 10:11 aspect and odd 3-byte row padding. **All 20 outputs differ
from their input**, so these are active-effect comparisons, not copy-only tests.

First former refusal: seed 1/index 0,
`ValidatePublicWorlds:world-extent-not-full-frame@4025`.
Input SHA-256 `520d9aa3b64b43a5ce60fcccff69daeed0ccfb1ef608ead13779018f49caa831`;
final original/Mac output SHA-256
`40513e050e56c5d0d968c35946fdad48a8758cb8925d72012b01a8aacc1991d1`.
Full case and before/after results: [comparison.json](P02g-evidence/comparison.json).

Bindings:

- Original AEX: `6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82`.
- Cached F52c worker: `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.
- Source before: `6b64edfc16c5e513ca9fe9e6bdffe83bbb7c8debac80082668ff14c33b80a129`.
- Source final: `eaac5c4585a54d6d7d675ca0ff05d8738a3094721472b101b486064d1f86091c`.
- Final candidate: `079077b0d0ddb7a92f66a405c9cd9b1b21ef9108e5828c8bc6ef4bc7052141e5`.

Historical unit failures/errors retained, identical before/after:

- `RealSdkSuiteLifecycle.test_v1_world_suite` and `.test_v2_world_and_color_suites`:
  missing local SDK includes (`AE_Effect.h`, `AEConfig.h`, etc.). The existing
  shared module also runs a Smoother2 read/build test; no Smoother2 file was edited.
- `CandidateIdentity.setUpClass`: absent historical handoff `build_identity.json`.
- `V1InstalledAdmissionUnion.test_default_live_read_only`: installed bundle absent.
- `V1InstalledAdmissionUnion.test_hashes`: pre-existing generator hash drift.
- `OLMSmootherV1CurrentInstalledPublicTest.test_canonical_hashes`: pre-existing
  generator hash drift; `.test_default_live_read_only`: worktree Util file absent.
- `test_contract_and_run5_identities_are_pinned`: absent historical request JSON.

The external-report function returns without validating a report when its file
is absent; this is not promoted to an original-output proof. Current optimized,
ASan/UBSan, HD/UHD determinism, Classic/Smart parity and synthetic-stack tests pass.
System Python and MAIN's emulation venv lack pytest; the committed runner also
loads the five module-level test functions, including their `tmp_path` argument.

inference:

- The refusal was an unnecessary full-frame admission restriction. The causal
  correction is restoring the original iteration rectangle as well as admitting
  it; no numerical kernels or final bytes needed adjustment.
- Exact comparisons support ignoring downsample/aspect metadata in this Classic
  arithmetic over sampled worlds. They do not establish native AE host scheduling
  or all-input equivalence. No two-refuted-hypothesis loop occurred.

changed_files:

- `mac/OLMSmoother/Mac/OLMSmoother_port.cpp`
- `tools/fuzz/verify_olmsmoother_P02g.py`
- `tools/fuzz/run_olmsmoother_P02g_units.py`
- `tests/fuzz_corpus/olmsmoother_P02g_realistic/` (224 records)
- `orchestra/reports/P02g-smoother-geometry.md`
- `orchestra/reports/P02g-evidence/` (compressed before/final rows, provenance,
  summaries, comparison and unit logs)

verify:

From this worktree, run:

```sh
export TMPDIR="$PWD/orchestra/state/P02g-smoother-geometry"
export TMP="$TMPDIR" TEMP="$TMPDIR" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$TMPDIR"
python3 tools/fuzz/verify_olmsmoother_P02g.py --label verify --geometry realistic --jobs 1 --expect-fixed > "$TMPDIR/verify.log" 2>&1
python3 tools/fuzz/run_olmsmoother_P02g_units.py > "$TMPDIR/verify-units.log" 2>&1
python3 tools/fuzz/run.py --plugin olmsmoother --jobs 1 --replay tests/fuzz_corpus/olmsmoother_P02g_realistic --scratch "$TMPDIR/verify-replay" --report "$TMPDIR/verify-replay.json" --budget-minutes 30 > "$TMPDIR/verify-replay.log" 2>&1
git diff --check
```

Expected campaign counts are the final table; `--expect-fixed` exits zero.
Unit command intentionally exits 1 on the listed historical failures/errors.
Standard corpus replay: `replay_complete`, `replay_matches_saved: true`, 224 cases.
Candidate build hashes may depend on checkout/compiler; raw output equality is
required, without tolerance. Regenerable scratch build products were removed.

next:

No measured acceptance failures remain. Native AE confirmation, empty-extent
oracle delivery, and independently sized Classic source/output worlds remain
separate boundaries. Smoother v1 advertises no Smart/PreRender route, so this
Classic campaign has no `result_rect`-negotiated output allocation claim. Existing
unequal-dimension and resource safety guards are retained; no evidence here
promotes those unmeasured boundaries. Repair historical environment/fixture unit
failures in a separate ticket, without rewriting release-gate evidence.
