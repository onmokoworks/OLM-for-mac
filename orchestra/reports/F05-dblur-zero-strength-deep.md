status: blocked

summary:
- Implemented the AEX four-control deep-copy predicate and zero-Strength/active-Fade dispatch, core admission and resource accounting.
- Seed 1 / 300: Classic and Smart exact counts each increase **115 → 228**; all 56 existing mismatches and 115 existing exact outputs are unchanged.
- All 115 reduced target cases: **114 exact / 1 refusal** per route; 30 independent small cases and four paired intermediate planes are exact; sanitizer comparisons are clean.
- Case 127 reaches an original-AEX read **16 bytes before a 404-byte noise table**; its safety refusal is retained. Case 274 renders on Mac but its original-size AEX reference remains unavailable.
- Candidate fix and reproducible evidence are committed for review, but the complete acceptance claim remains blocked by those reference boundaries.

facts:

Starting revision: `01cd8d87015e5156cb741c9867d5ce5938ecc5a5`, branch `orch/F05-dblur-zero-strength-deep`. Read `AGENT_GUIDE.md`, `tools/emulation/GOTCHAS.md`, the DirectionalBlur ledger row, the compatibility classification plan, and T10. No MAIN, emulator source, installed bundle, release gate, forbidden-action list, other plugin, or saved corpus was modified. No push, history rewrite or worker rebuild. SDK directories were temporarily linked to MAIN for existing tests and removed afterward. After deleting generated corpora and temporary artifacts, retained scratch measured **5,628,968 bytes**; temporary build directories were removed automatically.

**Provenance.** Original Windows 2025 CPU AEX through Unicorn Smart versus the production Mac `EffectMain` Classic/Smart fake SDK host, arm64 O2, contraction disabled. Raw ARGB16/ARGB32f, full-frame origin zero, unit downsample, time 0/24, no host color conversion, no independent Layer. Nonfinite source cases are input-domain probes, not native AE reachability claims. The reference worker is used by absolute path from the supplied cache index:

- AEX SHA-256: `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
- Worker: `/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker`; SHA-256 `16ab2412c00b6ce5d61cadbf9d1cd3aa3c991f36bc66c6af8c2595c32d075e3c`.
- Before/after campaign Mac executable hashes: `7ca5d3dec8975a1a16a9245f26f91b2432277ebaa066e20abc81198cb4102969` / `0ba06b571843e3275bfdac92bcf80e1d75cc3d9952d8197d7e04de3961cb530e`.
- Decomp/disasm hashes and current source hashes are retained in `reports/fuzz/olmdirectionalblur_zero_strength_20261022.json`.

**Recovered branch, not terminal-return suppression.** AEX PF16 owner `0x180003c90` and PF32 owner `0x1800057b0` first invoke the host copy callback. Their tests at `0x180003dc0` and `0x1800058db` return only when scaled Front Strength, Front Alpha Fade, Back Strength and Back Alpha Fade are all zero. Gain, angle, Size, Tails and Noise are absent from this return test. At unit scale, the new deep-copy branch preserves the source bits even with those controls active. With Fade active, the original rotate → prepass → zero scatter → normalization → inverse rotate → typed writer pipeline executes. Existing prepass/scatter arithmetic already implements zero scatter counts; the core's previous two-Strength-only refusal prevented it from running. No writer, rounding, Gaussian, coordinate correction, Noise wrapping, or PF8 implementation change was made.

The feature dispatcher and Smart preflight now admit zero scatter counts only through the deep feature route. The budget still accounts for fixed work, Fade gathers, work planes, tables, wrapper buffers and Smart staging. Existing world, range, finite-input, noise-index, operation-budget and allocation-budget safeguards remain in place. The copy branch validates world payload spans and active row widths before copying.

**Paired intermediate evidence.** `render-trace-png` uses the unchanged AEX, with memory watches at the typed owner, the last `0x38d0` rowdriver call and the second `0x1ec0` rotation. The Mac observations are inserted only in a disposable core copy. The authored 1×2 source expands to a 7×6 work plane. With Back Fade 3 and both Strengths zero:

| Depth | Stage | Bytes | AEX = Mac SHA-256 |
|---|---|---:|---|
| PF16 | Last rowdriver output, before normalization | 672 | `83c6cc87c3244648769641ae8cad422e45b5ebf61e916ef58e3bb33e0279a70f` |
| PF16 | Normalized plane, before inverse rotation | 672 | `e5aad46aadf215f0f5584f3290ada39cc622071618aa4efc58cd2b95846f9259` |
| PF32 | Last rowdriver output, before normalization | 672 | `6bbac5f71d084d94bb08d0ff64dd5bfe2a047153f1c11c120cf09457daeccac4` |
| PF32 | Normalized plane, before inverse rotation | 672 | `1cee4522eaf0fe70aac6d899e0b008cdf7ff614b7f608a554dde6c29fee6f638` |

Both final outputs also match. The same two depths with Fade zero have no rowdriver/rotation witnesses and return the exact input bytes. Captured four-control words are `(0,0,0,3)` or `(0,0,0,0)`. These are actual branch/intermediate observations; no detoured arithmetic or generated expected pixels were used.

**300-case before/after.** The before run was executed on the starting source; the final run was executed on the committed production changes. Both completed with AEX **298 ok / 2 budget**, indices 274 and 289. Each command used `--n 300 --seed 1 --jobs 2`, scratch corpus, and `--shrink-attempts 0`. The existing saved corpus supplies the separate shrunk mismatch replay; this campaign is a refusal census, not a new minimal-cluster claim.

| Route | Exact before → after | Mismatch before → after | Refusal before → after | Uncompared before → after |
|---|---:|---:|---:|---:|
| Classic | 115 → 228 | 56 → 56 | 128 → 14 | 1 → 2 |
| Smart | 115 → 228 | 56 → 56 | 128 → 14 | 1 → 2 |

All 115 old exact hashes remain identical. All 56 old mismatch result dictionaries remain identical. First existing mismatch remains seed index 0, PF8, byte 24: AEX `54`, Mac `50`, 34 differing bytes; Mac hash `384cbc650d2b4549412230838c01850c9a4b49069615ae4275b7e22cd7a7d667`. No new first mismatch exists in this ticket's successfully compared outputs.

Of the **115 original deep zero-Strength refusals**, 56 are four-zero copies and 59 have Fade active. On original inputs, 113 become exact, case 127 remains a refusal, and case 274 now renders but is uncompared. The one already-exact all-zero deep case is excluded from these 115 target counts.

**Gate/admission and sanitizer experiment.** The new copy implementation plus zero-count Fade admission was run in O2 and `-fsanitize=address,undefined -fno-sanitize-recover=all` builds on all 115 target inputs, both routes: **230/230 identical outcome/active-byte comparisons**, zero sanitizer failures. The unavailable reference at index 274 is not counted as exact. The negative-index safety guard was never disabled. Thus this is positive evidence for the 113 completed newly rendered references, not an assertion that every unblocked original input has an available oracle.

For a reproducible small counterexample set, keep each target's controls and the first pixel of its first one or two rows, producing 1×1 or 1×2 inputs. All 115 still refuse in a scratch build of the starting revision. The changed implementation yields **114 exact / 1 refusal** per route, with **230/230 O2–sanitizer comparisons** equal; the sole refusal is index 127. The reduced index 274 is exact. The additional independent 30-case matrix covers PF16/PF32, 1×1/1×2/3×2, copy/Front Fade/Back Fade/both Fades/combined controls: **60/60 route comparisons exact**, and all 60 sanitized outputs exact. These are authored reductions, not globally minimal cases.

**Saved corpus before/after table.** All 56 saved inputs were actually replayed against both the starting revision (scratch source build) and changed source. The full 56-row before/after table is `corpus_before_after` in the committed JSON; the 300-row campaign table is `before_after`.

| Corpus | Before | After | Changed | Updated files |
|---|---:|---:|---:|---:|
| `tests/fuzz_corpus/olmdirectionalblur`, Classic | 56 saved mismatches reproduced | same 56 result dictionaries | 0 | 0 |
| Same corpus, Smart | 56 saved mismatches reproduced | same 56 result dictionaries | 0 | 0 |

**External boundary 127.** Source 3×61 produces work geometry 65×65; Seed 518, Thickness 10, Noise Offset −399.5963134765625. The actual AEX fixed getter constructs the normalized offset. The unchanged generator `0x1800034e0` allocates a 324-byte noise plane and a 404-byte table. At its **third table read**, `0x1800037f3` uses signed index **−4**, byte offset **−16**. The probe stops immediately before the invalid read; no allocator padding is accepted as an expected output. Before this witness, `aex_witness.leaf_check` executes the transparent prepass at `0x1000`, verifying its destination and stack arguments 5/6 in 31 instructions. The ordinary session worker completes case 127 with hash `dd937d8f8dd2dfd0cf74561abb3026161720ecc94f5524bf8548d01e861ff4e3`; the Mac continues to return error 512 from the existing invalid-noise-index guard. This is direct original-AEX allocation-bound evidence, not a port-generated guessed index.

**Unavailable original-size reference 274.** At 139×240, the ordinary 10-second AEX budget expires. A separate replay with a 120-second subprocess limit still fails inside the cached worker: `execution stopped before the guest returned (RIP=0x600800f0)`. The adapter classifies that second outcome as `reject`, not exact. Both Mac routes and sanitizer builds return identical hash `937af8f4a4355fb525d33d3db02239ef4eb597b06a38917a4a275cf1aafeb054`. The failure diagnostic is retained in `budget_recheck`; this ticket does not claim its root cause is proven or that this full-size output is exact.

**Existing tests.** Passed:

- `test_directionalblur_general_features_effectmain_20261001.py`: its public Classic/Smart native-hash and cleanup test, including 180 retained cases × two routes × O2/sanitizer, plus its failure controls.
- `test_directionalblur_sse_conversion_20261001.py`: SSE conversion/extreme-scatter test in ordinary and sanitized builds.
- `test_directionalblur_general_feature_budget_20261001.py`: checked-budget/rejection test.
- `test_olmdirectionalblur_remaining6_ucrt_expf_request_20260814.py`: the two selected `test_float32_vector_reconstruction_and_boundaries` and `test_report_claim_and_schema_tamper_rejected` tests.

Attempting that entire legacy expf request suite yielded 2 passes, 2 failures and 2 errors because the historical `refs/runtime_trace_packages/olm_runtime_trace_olmdirectionalblur_remaining6_ucrt_expf_20260814` package is absent in this worktree. It was not copied or regenerated. An initial multi-file unittest discovery also hit the existing same-module-name collision between `tests/` and `tools/emulation/`; separate processes/import-by-path were used for the executed tests above. One initial candidate build had a mismatched helper signature and was corrected before numerical testing. The intermediate 198-exact candidate still had the old PF16 core guard; the final candidate changes both deep cores. None of these setup failures is classified as a numerical hypothesis refutation.

inference:

- The cause of the port's deep zero-Strength refusals is the incorrect two-control work predicate. The four-control AEX predicate explains both the copy and Fade-active outcomes, and the paired stages substantiate reuse of the existing arithmetic.
- Case 127's completed emulator output depends on memory outside the AEX-owned table, so that hash cannot establish a portable Windows noise-generator contract. The outside-port/host-allocation boundary is proven; the value native Windows would read and its final output are not proven.
- The candidate adds no observed regressions, but case 274 prevents a blanket “every newly admitted original input is exact” claim. Marked blocked rather than silently counting a missing reference as a successful gate-off result. No two-refuted-hypotheses stop condition occurred; work stops at the explicit reference boundary, with concrete new values recorded.
- Finite fake-host/Unicorn agreement is not native AE, native Windows UCRT, independent Layer, downsampled Fade, arbitrary nonfinite Fade, or all-input compatibility proof.

changed_files:
- `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`
- `core/dblur_frontonly.cpp`
- `core/dblur_generic_budget.h`
- `tools/fuzz/probe_directionalblur_zero_strength.py`
- `tools/emulation/probe_directionalblur_zero_noise_boundary.py`
- `reports/fuzz/olmdirectionalblur_zero_strength_20261022.json`
- `reports/fuzz/olmdirectionalblur_zero_noise_boundary_20261022.json`
- `orchestra/reports/F05-dblur-zero-strength-deep.md`

verify:

Run from this worktree; keep all temporary files below the ticket scratch directory. The Python environment is MAIN's existing venv, referenced by absolute path. Expected counts are subject to oracle time-budget variability; no timeout is exact.

```sh
mkdir -p orchestra/state/F05-dblur-zero-strength-deep
export TMPDIR="$PWD/orchestra/state/F05-dblur-zero-strength-deep"
export PYTHONDONTWRITEBYTECODE=1
```

Reproduce the **before** 300-case run using a scratch build of the starting revision, without changing HEAD:

```sh
python3 - <<'PY' > orchestra/state/F05-dblur-zero-strength-deep/before-recheck.log 2>&1
import sys
sys.path.insert(0,'tools/fuzz')
import run
import adapters.olmdirectionalblur as module
from probe_directionalblur_zero_strength import BaselineAdapter
module.Adapter=lambda options: BaselineAdapter(options,'01cd8d87015e5156cb741c9867d5ce5938ecc5a5')
s='orchestra/state/F05-dblur-zero-strength-deep'
sys.argv=['run.py','--plugin','olmdirectionalblur','--n','300','--seed','1','--jobs','2','--scratch',s,'--worker','/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker','--report',s+'/before-recheck.json','--corpus',s+'/corpus-before-recheck','--shrink-attempts','0']
raise SystemExit(run.main())
PY
```

Expected: exit 0; per route 115 exact / 56 mismatch / 128 refusal / 1 uncompared under the observed two timeouts. The original measured before run used the ordinary `run.py` command with those same arguments while production source was still at the starting revision. The scratch-baseline command above was also executed and independently reproduced these counts.

```sh
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 2 --scratch orchestra/state/F05-dblur-zero-strength-deep --worker /Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker --report orchestra/state/F05-dblur-zero-strength-deep/after-recheck.json --corpus orchestra/state/F05-dblur-zero-strength-deep/corpus-after-recheck --shrink-attempts 0 > orchestra/state/F05-dblur-zero-strength-deep/after-recheck.log 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --jobs 2 --replay tests/fuzz_corpus/olmdirectionalblur --scratch orchestra/state/F05-dblur-zero-strength-deep --worker /Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker --report orchestra/state/F05-dblur-zero-strength-deep/replay-recheck.json --corpus orchestra/state/F05-dblur-zero-strength-deep/corpus-replay-recheck > orchestra/state/F05-dblur-zero-strength-deep/replay-recheck.log 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/fuzz/probe_directionalblur_zero_strength.py --baseline 01cd8d87015e5156cb741c9867d5ce5938ecc5a5 --before orchestra/state/F05-dblur-zero-strength-deep/before-recheck.json --after orchestra/state/F05-dblur-zero-strength-deep/after-recheck.json --replay orchestra/state/F05-dblur-zero-strength-deep/replay-recheck.json --output orchestra/state/F05-dblur-zero-strength-deep/verification-recheck.json > orchestra/state/F05-dblur-zero-strength-deep/verification-recheck.log 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/probe_directionalblur_zero_noise_boundary.py --output orchestra/state/F05-dblur-zero-strength-deep/noise-recheck.json > orchestra/state/F05-dblur-zero-strength-deep/noise-recheck.log 2>&1
```

Expected: after campaign 228 exact / 56 mismatch / 14 refusal / 2 uncompared per route; replay 56/56 `matches_saved`; verification prints `TARGETS 115 SMALL 30 PAIRED 4`, `ok:114 / refusal:1`; reduced-target results 114 exact / 1 refusal per route; noise probe reports index −4, offset −16, allocation 404. All commands exit 0 as validation/evidence collection; that does not override the blocked ticket status.

Existing numerical tests require read-only SDK links in this worktree (remove only the links created here afterward):

```sh
python3 - <<'PY'
from pathlib import Path
root=Path.cwd()
for name in ('Headers','Util','Resources'):
    path=root/name
    if not path.exists(): path.symlink_to(root.parent.parent/name,target_is_directory=True)
PY
python3 -m unittest discover -s tests -p test_directionalblur_general_features_effectmain_20261001.py -v > orchestra/state/F05-dblur-zero-strength-deep/general-tests.log 2>&1
python3 -m unittest discover -s tests -p test_directionalblur_sse_conversion_20261001.py -v > orchestra/state/F05-dblur-zero-strength-deep/sse-tests.log 2>&1
python3 -m unittest discover -s tests -p test_directionalblur_general_feature_budget_20261001.py -v > orchestra/state/F05-dblur-zero-strength-deep/budget-tests.log 2>&1
python3 - <<'PY' > orchestra/state/F05-dblur-zero-strength-deep/expf-selected-tests.log 2>&1
import importlib.util, unittest
spec=importlib.util.spec_from_file_location('f05_tests','tests/test_olmdirectionalblur_remaining6_ucrt_expf_request_20260814.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
names=('test_float32_vector_reconstruction_and_boundaries','test_report_claim_and_schema_tamper_rejected')
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(m.DirectionalRemainingSixUcrtRequestTest(n) for n in names))
raise SystemExit(not result.wasSuccessful())
PY
git diff --check
```

Expected: the five selected unittest methods pass; `git diff --check` is clean. Use MAIN's venv interpreter for these commands if the system Python lacks Pillow or Unicorn.

next:
- Orchestrator: review the candidate diff and the explicitly limited acceptance evidence; do not promote the two original-size reference exceptions to exact.
- Negative Noise Offset follow-up: use case 127's actual allocation-bound witness to determine the native allocator/undefined-input policy. Do not invent lower-bound wrapping or read-before-buffer behavior in the Mac port.
- Emulator/reference follow-up: obtain a completed original-size reference for case 274 (139×240), explaining the cached worker's failure first. Its reduced 1×2 case is already exact; no extra numerical patch is justified by the missing full-size oracle.
