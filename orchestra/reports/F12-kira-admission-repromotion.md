status: done

summary:
- Promoted the general finite-SDR PF16/PF32 Alpha, Strength 100%, Mode 1/2 tuple on Classic and Smart, retaining geometry/storage guards and excluding signed-angle overflow.
- Production exact per route: seed 1 19→48, seed 3 19→52, seed 2 17→46; zero admitted mismatches or uncompared admissions.
- 112 independent AEX cases, 1,800 sanitized campaign route replays, 140 corpus route comparisons and 38 negative route tests pass; three active traces match all nine stages.
- Production corpus expectations 2/3 now record refusal→exact; strict replay is 8/8. Twenty-five fast tests and the existing compiled sanitizer test pass. No renderer arithmetic changed.

facts:

Base: `e3f887b5`, branch `orch/F12-kira-admission-repromotion`. Read the shared guide, KiraKira ledger restrictions, compatibility plan, emulator GOTCHAS, F09/F10/F11 evidence and worker INDEX. No MAIN, external emulator source/worker, release gate, ledger, other plugin, installed bundle or git history was modified. No reference-worker rebuild, merge, push or install.

Machine evidence: `reports/fuzz/olmkirakira_admission_F12.json`. It includes source/core/tool hashes, all admitted campaign records, campaign provenance, independent gate-off/production matrices, overflow counterexamples, stage comparisons, complete corpus before/after records, strict replay and test results. Reproduction tools never update corpus expectations.

Identities:

- Original MAIN `plugins_2025/OLMKiraKira.aex`: SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- Retained public worker: `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`, SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. INDEX lists RadialBlur workers; this is the retained KiraKira worker used by T06/F09/F10/F11.
- Mac source before: `80ac8d977b9ce1409262fc3dc1a8bf54751090b67223d71b976cada25047844f`; after: `a9458db90110ece9d7ca67783b7bd5dda0e339c8e2b10d0069e34f3c89dc92f2`.

Additional admission rule (`IsAlphaBoxTuple`):

- PF16 or PF32, finite SDR source samples; Alpha channel (1), Strength 100%, Blur Mode 1 or 2, Merge Mode 1 or 2, Approximated Input off, Source and Glow Opacity both 100%.
- Brightness Gain in [1,100]. Fade Out is unused by the original Alpha constructor.
- Each directional Length in [0,1000], Highlight Radius in [0,500]. Each active ray uses either an SDR RGB color or the existing default three-stop ramp. Inactive colors/ramps do not contribute. Custom active ramps remain outside this new rule.
- Raw integer rotation strictly greater than −2147483648 and at most 2147483512. The existing adapter's raw-fixed ANGLE mapping is retained; these are the integer degrees consumed by the AEX, not a new UI conversion.
- Existing generic width ≥9, height ≥7, side ≤4096, area ≤4096×2160, equal world dimensions, zero origins, valid positive byte strides/formats and nonoverlap checks remain. Smart retains its complete-frame request, 1:1 downsample and callback lifecycle checks. Existing exact/zero-ray admissions remain intact.
- The normal seed, ray, aggregation, composition and typed-writer code executes. This is neither input copying nor a sample correction. Other tuples/profiles retain their previous policy.

Original-AEX branch, static and trace facts:

1. MAIN `decomp/OLMKiraKira.aex.c.txt`, `FUN_18114edf0` (line 3523632), allocates one float seed channel and computes `powf(alpha, strength)`. At Strength 100%, the materialized exponent is exactly 1. The Fade Out argument used by other constructors is absent here. Channel 3/6's unresolved four-channel representation is excluded.
2. `FUN_18114f4a0` (3523894) zero-initializes five ray planes and dispatches each nonzero length. Its Highlight branch selects one isotropic box pass for Mode 1 and three for Mode 2. `FUN_181150790` (3524565) selects one/three directional box passes between forward/inverse warps. F11's recovered float sin/cos and extent operations now feed this shared workspace branch. Mode 3 is excluded.
3. `FUN_18114fd90` (3524147) accumulates the five rays and normalizes with one reciprocal and three multiplies. The current PF16/PF32 implementation already contains F09's correction; the unresolved PF8 alternative is not promoted.
4. `trace_kirakira_admission_F12.py` runs the original full caller, source reader and typed outer writer, with the F09 TLS/allocation/CRT/import scaffold and its import-free fifth-argument ABI check. C28, seed-2 index 127 and an independent PF32 five-ray case each match **source, seed, all five rays, glow and composed**: 27/27 paired stages. All three final outputs bind byte-for-byte to the retained public AEX Smart worker and the Mac production Classic entry. No numerical AEX function is detoured. The independent case includes Highlight and non-white colors.
5. F10's two former negative witnesses now match on both diagnostic routes: seed-2 index 127 hashes to `ba5e76c8c85ae4a6bedc5a347119d437c5ef1839b2d189bfce5d36ec9711164a`; index 177 to `4062c707a243043797b13aa6e4b68e1444f69d99fc9bdc1e878e5280ad1a9c13`. Both are admitted and exact in the final production campaign.

Rejected full-angle-domain hypothesis and new boundary:

- An initial maximum-length PF16 9×7 matrix case at raw angle −2147483648 mismatches: 213 words / 370 bytes; first AEX `333d`, Mac `cb42`, byte 0. A separate length-7 case at the same angle differs in 223 words / 433 bytes; first AEX `2949`, Mac `164d`. Both routes reproduce these differences with gates off and sanitizers enabled. No failing case was promoted.
- The isolation matrix is angle {−2147483648, 0, 45000000, 2147483512} × length {7,1000}, with Highlight min(length,500). Six non-overflow cases are exact on both routes; the two −2147483648 cases mismatch on both. This separates the observed boundary from large filter lengths.
- Static decomp at line 3524928 converts `(double)-param_6` for the inverse warp. Disassembling the original AEX confirms `181150f3d NEG R15D`, `181150f40 MOVD XMM2,R15D`, `181150f45 CVTDQ2PD XMM2,XMM2`: integer negation precedes double conversion. The port negates a double angle. The new predicate requires the AEX's ray-offset additions and inverse negation to be representable as signed 32-bit integers. It does not patch the exceptional output.
- The final independent matrix includes the admitted endpoints −2147483647 and 2147483512, large positive/negative rotations, maximum directional lengths 1000 and Highlight 500, both depths and modes. These 16 boundary cases and the original 96 cases all pass on both routes with gates off and in production. The original 96 span two geometries, each individual ray and all five together, both merge modes, random SDR colors, default ramps, gains 1/1.25/7.5/100, multiple rotations/lengths, integer/float edge values and odd byte padding.
- This was one refuted admission hypothesis with a new boundary and static explanation, not two refuted hypotheses without new boundary data.

Measured campaigns (`--n 300 --jobs 2`; E/M/R/U = exact/mismatch/refusal/uncompared):

| Seed / campaign | Classic E/M/R/U | Smart E/M/R/U | AEX success/reject |
|---|---|---|---|
| 1 production before | 19/0/281/0 | 19/0/281/0 | 287/13 |
| 1 gate-off ASan/UBSan | 210/77/0/13 | 101/36/163/0 | 287/13 |
| 1 production after | 48/0/252/0 | 48/0/252/0 | 287/13 |
| 3 production before | 19/0/281/0 | 19/0/281/0 | 290/10 |
| 3 gate-off ASan/UBSan | 224/66/0/10 | 110/38/152/0 | 290/10 |
| 3 production after | 52/0/248/0 | 52/0/248/0 | 290/10 |
| 2 production before | 17/0/283/0 | 17/0/283/0 | 291/9 |
| 2 gate-off ASan/UBSan | 224/67/0/9 | 103/40/157/0 | 291/9 |
| 2 production after | 46/0/254/0 | 46/0/254/0 | 291/9 |

The active rule's campaign subsets are 38/38, 45/45 and 37/37 exact on each route for seeds 1, 3 and 2 respectively; some overlap F10's zero-ray rule. Every admitted output equals its gate-off and AEX hash. All previous exact cases remain exact and all other previously refused cases still refuse. AEX rejections are never counted as exact. Sanitized production replay checks all **1,800 route executions** against the ordinary campaigns. No sanitizer abort/error occurs.

The independent matrix checks **112 AEX cases / 224 exact production route renders** under ASan/UBSan. Nineteen one-away settings/profiles/geometries produce **38 clean refusals**, including both signed-angle overflow boundaries, PF8 active rays, unsupported channels/modes, opacity/strength/gain changes, out-of-range lengths, non-SDR input and tiny dimensions. The public host checks source/padding preservation, unchanged destination on refusal and balanced parameter callbacks.

Corpus before/after and expectation updates:

| Corpus cases | Fresh Classic before→after | Fresh Smart before→after | Saved expectation action |
|---|---|---|---|
| Production indices 2, 3 | refusal→exact | refusal→exact | Updated; previous complete results retained with this report link |
| Other 6 production cases | unchanged | unchanged | None |
| T06 shrunk 3, 13, 97, 122, 191, 230, 252, 268 | refusal→exact | refusal→exact | Historical diagnostic expectations retained |
| Other 54 T06 shrunk cases | unchanged refusal | unchanged refusal | None |
| All 70 cases, final tuple gates off | all statuses/bytes unchanged | all statuses/bytes unchanged | None |

These are **140 production and 140 diagnostic route comparisons**, each run at both revisions under sanitizers. Exactly 20 production route results improve; no rendered sample changes away from exact. C28/index 3 is now admitted on both routes, retaining AEX hash `d5e90cfe01d82d4de4c3d224086165c921855f6ecb157de5df45b2c51deec0bb`. C60/C62 remain outside the tiny-frame production boundary; their current diagnostic final bytes are exact after F11. The supplementary F09 trace preserves C62's PF8 intermediate glow difference rather than concealing it. Other unresolved F09 families remain refused.

Production index 2 now hashes to `2492c35739b1ea797c16a53870fbe8ee15438dbdf8ae709ffefeb4dd9ad1c60b`; production index 3 to `4ba7ff962215656f13e77538c39b743747cae3718284184c984da77ebd60a575`. These unshrunk production cases differ from T06's shrunk cases with the same indices. Strict production replay is initially 6/8 saved results (exit 1); after updating only these two improvements it is **8/8, exit 0**. Their previous refusal metadata, including inherited F03 Smart COUNTS drift, remains in `expectation_update.previous_result`.

Existing tests: **25 passed** (generic-beta lane 9, merge2 float oracle 6, outer compose oracle 9, bounded typed-writer ownership assertion 1). Existing compiled generic-beta ASan/UBSan test: **1 passed**, including its 54 clean/deterministic rows and 1920×1080 cases. Only that test module's SDK root is set to MAIN; HARNESS and SOURCE remain this worktree, and outputs use ticket scratch. `git diff --check` passes. Regenerable builds are removed; scratch is below 5 GiB.

inference:

- F09's PF16 normalization and F11's geometry recovery remove the sampled blockers for this Alpha/box branch. Paired stages, branch structure, three fuzz seeds and independent matrices support the bounded rule; seed-1 success alone was not used as authorization.
- The extreme negative-angle difference is consistent with the original signed integer inverse negation. Its representability guard is a general arithmetic-domain boundary, not a coordinate/case exception or output adjustment. Reproducing wrapped-angle arithmetic is a separate numerical ticket.
- These are exact CPU emulation/fake-host observations with retained import substitutes. They do not prove arbitrary native Windows UCRT/AE, GPU, custom ramps, ROI/downsample, all image sizes or all floating inputs. No all-input equivalence claim is made.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/verify_kirakira_admission_F12.py`
- `tools/emulation/trace_kirakira_admission_F12.py`
- `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000002.json`
- `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000003.json`
- `reports/fuzz/olmkirakira_admission_F12.json`
- `orchestra/reports/F12-kira-admission-repromotion.md`

verify:

From this worktree, use ticket scratch for every temporary/build/corpus artifact. Original before campaigns used ordinary `run.py` before editing; the alternate-source wrapper below reproduces them without changing the checkout. Final campaigns were repeated after narrowing the angle guard and bind to the final source hash above.

```sh
s="$PWD/orchestra/state/F12-kira-admission-repromotion"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show e3f887b5:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 3 2; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/before-seed$seed.json" --corpus "$s/before-seed$seed-corpus" > "$s/before-seed$seed.log" 2>&1
  python3 tools/fuzz/triage_kirakira.py --experiment all --sanitizers --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/gateoff-seed$seed.json" --corpus "$s/gateoff-seed$seed-corpus" > "$s/gateoff-seed$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/after-seed$seed.json" --corpus "$s/after-seed$seed-corpus" > "$s/after-seed$seed.log" 2>&1
done
python3 tools/emulation/verify_kirakira_admission_F12.py --probe --scratch "$s/probe-final" --report "$s/probe-final.json" > "$s/probe-final.log" 2>&1
python3 tools/emulation/verify_kirakira_admission_F12.py --overflow-evidence --scratch "$s/overflow" --report "$s/overflow.json" > "$s/overflow.log" 2>&1
python3 tools/emulation/verify_kirakira_admission_F12.py --before-source "$s/before.cpp" --campaign-dir "$s" --scratch "$s/verify" --report "$s/verification.json" > "$s/verification.log" 2>&1
"$py" tools/emulation/trace_kirakira_admission_F12.py --scratch "$s/active-traces" --report "$s/active-traces.json" > "$s/active-traces.log" 2>&1
"$py" tools/emulation/trace_kirakira_numeric_F09.py --indices 3 148 78 --scratch "$s/target-traces" --report "$s/target-traces.json" > "$s/target-traces.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/replay-production.json" --corpus "$s/replay-corpus" > "$s/replay-production.log" 2>&1
PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820 test_olmkirakira_merge2_float_oracle_20260728 test_olmkirakira_outer_compose_oracle_20260728 test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.Mode4FullCallerHostlessExactTests.test_mac_production_owns_the_bounded_highlight_and_typed_writer > "$s/fast-tests.log" 2>&1
PYTHONPATH=tests python3 - <<'PY' > "$s/sanitizer-test.log" 2>&1
import pathlib, unittest
import test_olmkirakira_generic_beta_sanitizers_20260820 as test
test.ROOT = pathlib.Path('/Users/onmk/Documents/Projects/Personal/OLM as')
result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(test))
raise SystemExit(not result.wasSuccessful())
PY
git diff --check
```

Expected: campaign table above; both matrix runs PASS with 112 exact cases per route; verifier PASS with 1,800 sanitized campaign routes, 140 production/140 diagnostic corpus comparisons and 38 clean refusals; overflow-evidence PASS retaining two diagnostic mismatches per route and six exact cases per route; three active traces all nine stages exact and public-bound; production replay 8/8; 25+1 tests pass. The verifier removes its builds on completion. It records historical saved corpus results but compares freshly rendered before/after outputs, so updating the two expectations does not weaken the audit.

next:
- Recover signed 32-bit ray-angle wrapping/inverse negation if admitting the excluded raw-angle domain is desired; preserve the new overflow witnesses.
- Separate tickets remain for PF8 normalization, four-channel color seeds, non-unit strength/opacity conversion, Mode 3/tiny geometry, approximation/custom ramps, and native AE/UCRT/ROI/downsample coverage. Do not infer these from this promotion.
