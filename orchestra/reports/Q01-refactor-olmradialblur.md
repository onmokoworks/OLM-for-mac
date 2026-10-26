status: blocked
summary:
- Coherent first pass only: extracted scalar math/polar sampling and point diagnostics into two single-TU includes.
- Named three constants using existing AEX provenance, clarified arithmetic order, renamed a parser cursor, removed unused SampleChannel.
- Plugin non-comment/nonblank lines decreased from 6,402 to 6,380; the remaining 5,923-line main file still needs further splitting.
- Gate completion is blocked by oracle-result instability, a reference/fast timeout, and the release runner's ticket-specific scratch restriction. Not release-ready.

facts:

Base: `12622f6881f39150eda238812a32a3c01b2e7d30`, obtained at start with
`git merge-base HEAD codex/public-beta-roi`. MAIN is on `codex/public-beta-roi`,
not the stale local branch named `main`; both this worktree and MAIN started at
that Q00 merge. Source commit: `7e29c03977df456c97a781a6e11f9d0a0524de0e`.
Work branch: `orch/Q01-refactor-olmradialblur`.

Line counts (physical / non-comment, nonblank; block and line comments removed):

| File under mac/OLMRadialBlur | Before | After |
| --- | ---: | ---: |
| OLMRadialBlur.cpp | 6520 / 6055 | 5923 / 5508 |
| RadialMath.inc | 0 / 0 | 350 / 302 |
| RadialDiagnostics.inc | 0 / 0 | 230 / 223 |
| OLMRadialBlur.h | 149 / 137 | 149 / 137 |
| OLMRadialBlurPiPL.r | 33 / 31 | 33 / 31 |
| OLMRadialBlur_Strings.cpp | 47 / 44 | 47 / 44 |
| OLMRadialBlur_Strings.h | 38 / 37 | 38 / 37 |
| RadialScatterSIMD.h | 84 / 72 | 84 / 72 |
| RadialRotationRows.h | 32 / 26 | 32 / 26 |
| Total | 6903 / 6402 | 6886 / 6380 |

Named constants: `kNoiseFixedAngleToRadians` (AEX a2b0, original DOUBLE
coefficient), `kAngleDegreesToRadians` (AEX 8690, original DOUBLE coefficient),
`kAEXFullTurn` (AEX 0x1800212e0, original hexadecimal DOUBLE literal).
No arithmetic, floating widths, bit patterns, or operation order were changed.
Existing FLOAT32 trig bit patterns remain intact; their complete constexpr/provenance
annotation is deferred, not claimed complete.

`SampleChannel` was a static, uncalled bilinear helper: repository searches found
only its definition, including no test/tool references. Removed it, not the used
`ClampFloat` or FFT/convolver implementations. Xcode independently reported the
unused helper in both base architecture builds. Preserved per-depth traits and
SSE arithmetic wrappers because their conversion and NaN-selection behavior differ.
The parser's `p` became `cursor`; no uncertain decompiler names were guessed.

An in-memory reconstruction against `git show 12622f68:mac/OLMRadialBlur/OLMRadialBlur.cpp`
passed: reversing the three constant substitutions and cursor rename, stripping
comments, restoring declaration grouping and the deleted helper reproduces the
base source. `git diff --check` passed. No generated files, reference/fast macros,
parallel limits, Xcode settings, or release-gate files were edited.

Original AEX SHA-256 verified by the adapters:
`ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
G2 uses five recorded hash-bound cached worker builds; none was rebuilt or modified.
G3 uses cached `worker-F52c-geom/aex-guest-worker`, SHA-256
`4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.

Source SHA-256 after refactor:

- `mac/OLMRadialBlur/OLMRadialBlur.cpp`: `91dfb6525c8e61c7533515b68ff8d35d49e9773be8d3fd661a68d347d41c8ae2`
- `mac/OLMRadialBlur/RadialMath.inc`: `2a6f193acfdaf6df43294ef7340f5e803a431f4f694449f6588da69036f957a4`
- `mac/OLMRadialBlur/RadialDiagnostics.inc`: `fd24a769657090d36655fd033026ad875b94bbcf8a37ecd2a5abc02af3d8a773`

Gate results:

- G1: command exit 0; 12,012 comparisons = 3,000 small random + 3 UHD cases
  for each of arm64/x86_64 and reference/fast. 12,012 exact, 0 differences,
  0 refusals, 0 new refusals, 0 execution errors; first differing byte: none.
  All eight harness builds reported the requested architecture. Coverage: each
  depth 4,004 comparisons; default geometry 4,020, realistic-v1 3,996,
  realistic-v2 3,996; default/odd-even sizes 6,008/6,004; 12 UHD comparisons.
  Downsample ratios include 1:1, 1:2, 1:3, 1:4, 1:8 and asymmetric pairs.
  After these builds only trailing empty EOF lines were removed from the two
  includes; tokens and all existing line numbers are unchanged.
- G1 sampler caveat: Q00 sets `color_sampler='float-v1'`, but the RadialBlur adapter
  never reads that attribute. Its 32-bit generator already emits independent float
  channels including HDR/signed/nonfinite profiles; this is not proof of running a
  separate float-v1 sampler. The tool reports these as byte-colours. This requires
  a tool/adapter follow-up outside the plugin-only scope.
- G2: replayed all 243 corpus files (61 default, 180 realistic-v1, 2 realistic-v2)
  on base and head with recorded worker hashes/timeouts. The four C49 sanitizer
  cases were additionally replayed with `OLM_RADIAL_CANDIDATE_SANITIZE=1` on both
  revisions and those results replace their unsanitized observations. Across all
  243 cases, candidate route error codes, raw hashes, rectangles and metadata have
  zero differences. Full result dictionaries differ for `C46_seed1_case000280.json`
  and `C49_seed1_case000117.json`: both sides reject in the Smart AEX oracle but
  crash-snapshot diagnostics differ. The initial unsanitized C49 run also varied
  between oracle success and rejection. Realistic and nightly corpus commands
  exit 0; default/sanitized corpus commands exit 1. No strict full-result PASS.
- G3: both revisions completed seed 909, realistic geometry, 100 cases, jobs 1,
  default geometry oracle, default 10-second timeout, shrinking disabled.
  Candidate route errors/raw hashes/metadata match in all 100 cases. Both have
  65 Classic mismatches, 34 Classic refusals and 1 Classic exact. Smart results:
  base 97 exact + 3 uncompared (2 budgets, 1 rejection); head 98 exact + 2
  uncompared (1 budget, 1 rejection). Full results differ at index 23 (oracle
  budget vs success) and 86 (rejection diagnostics). Index 23's candidate raw
  hash on both sides is `05947ea2f7aa94658ae87149e69d8f80eeb8650b0385776ea4a81671d9e8d8db`.
  First pre-existing Classic mismatch is index 0: byte 2, word 1, expected
  `0000`, actual `8717`, 164 different bytes / 86 words out of 192 bytes, identically
  on both revisions. Both campaign commands exit 0, but strict G3 equality is not met.
- G4: default 200 small + 20 HD + 5 UHD request, thread caps 1/2/8, jobs 1.
  Completed 215 cases / 645 comparisons: 645 exact, 0 mismatches, 0 refusals.
  Then the reference render timed out at 180 seconds on sequence 215, generated
  index 600215, 1920x1080 PF8, retained parameters from
  `tests/fuzz_corpus/radialblur/C45_seed1_case000108.json`.
  Input SHA-256: `1435aa4a6ce266e1f0d739d8f6889dc4cad41733b3ef4c10531eeca00f0d8b92`.
  Exit 1; no first differing byte in completed comparisons; UHD phase not reached.
- G5 Xcode: base and head Debug Universal builds both exit 0.
  UI oracle tool exits 0; RadialBlur has 54 updates / 108 including reload checks,
  0 mismatches. UI handler stays in the main cpp because the tool extracts its
  body from that file without expanding includes.
- G5 package: `scripts/package_mac_plugins.sh` exits 0; all 10 Debug bundles built
  and the Universal package verifier passed. Used MAIN only as the read-only
  reference root, scratch-backed build-directory symlinks, and a scratch-local
  xcodebuild wrapper adding `-jobs 1`. No bundles were installed.
- G5 release v2: invocation with Q01 scratch exits 2 before running any stages:
  `state must be inside this ticket scratch`. The runner hard-codes R09 and resolves
  the path before checking it; Q01's hard scratch restriction forbids that location.
  Did not modify/bypass the runner or write under R09. Its seven stages are unrun.
- G6: Universal Xcode log warning lines 388 -> 386; compiler warnings alone
  386 -> 384 (two unchanged build-system warnings excluded). No new warning kind;
  exactly the two architecture-specific `SampleChannel` unused-function warnings
  disappeared. Successful fuzz builders capture compiler output internally, so
  this warning comparison is specifically the clean Xcode build pair.

inference:

The source reconstruction and native/candidate equality support behavior preservation
for this partial refactor. They do not establish original-AEX equivalence or resolve
existing Classic mismatches. Oracle-only diagnostic/budget differences are consistent
with oracle instability/resource sensitivity; the cause was not proven or changed.
The G4 timeout is an incomplete test, not a numerical mismatch or evidence of a new
performance regression. There were no behavioral repair hypotheses or tolerance changes.

Suspicious existing code deliberately left alone:

- `RotationGaussianWeights` ignores `apply_case0010_aex_ulp`; the name implies a
  behavior that the body does not perform. This is misleading legacy API surface,
  not proof that a correction should be reintroduced.
- Existing fixture-specific admission paths and PF8 fallback `rgb_epsilon` remain.
  Their provenance/eligibility deserves a separate behavior/evidence audit; this
  refactor does not broaden them or add final-byte adjustments.
- `RadialRefusal` passes snprintf's would-have-written length to write without
  clamping it to its 384-byte buffer. Inference: a sufficiently long future tag
  could over-read the buffer. No triggering current tag was demonstrated; unchanged.

changed_files:
- mac/OLMRadialBlur/OLMRadialBlur.cpp
- mac/OLMRadialBlur/RadialMath.inc
- mac/OLMRadialBlur/RadialDiagnostics.inc
- orchestra/reports/Q01-refactor-olmradialblur.md

verify:

Run from the ticket worktree. Use a fresh scratch suffix because native_diff refuses
an existing run directory. All long-command output should go into these logs.

```sh
ROOT="$PWD"
MAIN='/Users/onmk/Documents/Projects/Personal/OLM as'
BASE=12622f6881f39150eda238812a32a3c01b2e7d30
S="$ROOT/orchestra/state/Q01-refactor-olmradialblur/verify"
mkdir -p "$S"
export TMPDIR="$S" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
scripts/setup_ae_sdk_links.sh > "$S/sdk-links.log" 2>&1
python3 tools/refactor/native_diff.py --plugin radialblur --base "$BASE" \
  --cases 3000 --seed 909 --arch both --build both --jobs 1 \
  --scratch "$S/g1" > "$S/g1.log" 2>&1
```

G1 expected: 12,012 exact comparisons, 0 differences/new refusals/execution errors. The float-v1 limitation above still applies.

Prepare a read-only baseline source snapshot for G2/G3/G5/G6 (no MAIN edits):

```sh
mkdir -p "$S/base"
git archive "$BASE" mac core cli tools ucrtmath \
  reports/radialblur_public_getters_aligned_20261001.json | tar -xf - -C "$S/base"
for name in Headers Util Resources; do ln -s "$MAIN/$name" "$S/base/$name"; done
for side in base head; do
  T="$ROOT"; [ "$side" != base ] || T="$S/base"
  V="$T/orchestra/state/Q01-refactor-olmradialblur/verify"
  mkdir -p "$V"
  for corpus in radialblur radialblur_realistic_P02d radialblur_N02-nightly-20261025; do
    python3 "$T/tools/fuzz/run.py" --plugin radialblur --jobs 1 --main "$MAIN" \
      --replay "$ROOT/tests/fuzz_corpus/$corpus" --scratch "$V/$corpus" \
      --report "$V/$corpus.json" > "$V/$corpus.log" 2>&1
  done
  python3 "$T/tools/fuzz/run.py" --plugin radialblur --jobs 1 --main "$MAIN" \
    --seed 909 --geometry realistic --n 100 --shrink-attempts 0 \
    --scratch "$V/fresh" --report "$V/fresh.json" --corpus "$V/fresh-corpus" \
    > "$V/fresh.log" 2>&1
  for case in C49_seed1_case000117 C49_seed105_case000150 C49_seed1_case000148 C49_seed105_case000071; do
    OLM_RADIAL_CANDIDATE_SANITIZE=1 python3 "$T/tools/fuzz/run.py" \
      --plugin radialblur --jobs 1 --main "$MAIN" \
      --replay "$ROOT/tests/fuzz_corpus/radialblur/$case.json" \
      --scratch "$V/$case-sanitized" --report "$V/$case-sanitized.json" \
      > "$V/$case-sanitized.log" 2>&1
  done
  xcodebuild -project "$T/mac/OLMRadialBlur/Mac/OLMRadialBlur.xcodeproj" \
    -configuration Debug -jobs 1 ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO \
    MACOSX_DEPLOYMENT_TARGET=11.0 OBJROOT="$V/xcode/objects" \
    SHARED_PRECOMPS_DIR="$V/xcode/pch" CONFIGURATION_BUILD_DIR="$V/xcode/products" \
    build > "$V/xcode.log" 2>&1
 done
```

Compare G2 `replays[].result` keyed by corpus filename, substituting the four
sanitized observations; compare G3 `cases[].result` keyed by index. Candidate
`routes` have identical fields after excluding the oracle-derived `status` label
(exact/mismatch/uncompared). Preserve error codes and hashes; this is an explanatory
comparison, not a waiver of G2/G3's strict whole-result requirement. Oracle diagnostics
and wall-time budget outcomes can vary. Expected native differences: 0.
Xcode expected: both succeed; warnings do not increase.

```sh
python3 tools/perf/ref_vs_fast.py --plugin radialblur --jobs 1 \
  --scratch "$S/g4" > "$S/g4.log" 2>&1
python3 tests/ui_oracle/compare_mac.py --scratch "$S/ui" > "$S/ui.log" 2>&1
python3 scripts/run_olm_release_gate_v2.py --state "$S/release" \
  > "$S/release.log" 2>&1
```

Expected: G4 may reproduce the recorded 180-second timeout (no claimed full PASS);
UI RadialBlur 108 checks / 0 differences; release v2 rejects the scratch path.

Universal packaging reproduction (remove only the temporary build symlinks created
by this procedure afterwards; do not replace existing build directories):

```sh
mkdir -p "$S/bin" "$S/package-build"
printf '%s\n' '#!/bin/sh' 'if [ "${1:-}" = -version ]; then exec /usr/bin/xcodebuild "$@"; fi' \
  'exec /usr/bin/xcodebuild -jobs 1 "$@"' > "$S/bin/xcodebuild"
chmod +x "$S/bin/xcodebuild"
for project in mac/*/Mac/*.xcodeproj; do
  name="$(basename "$project" .xcodeproj)"
  mkdir -p "$S/package-build/$name"
  ln -s "$S/package-build/$name" "$(dirname "$project")/build"
done
OLM_REFERENCE_ROOT="$MAIN" PATH="$S/bin:$PATH" scripts/package_mac_plugins.sh \
  --output "$S/plugins.zip" > "$S/package.log" 2>&1
```

Expected: exit 0, ten packaged Universal plug-ins. Scratch build trees and zip are
regenerable and should be deleted after verification; keep logs/reports.

next:
- Q00/tool follow-up: reconcile release-runner scratch validation with per-ticket
  scratch rules, provide explicit RadialBlur float-colour sampler coverage, make UI
  source extraction include-aware, and define comparison of unstable oracle diagnostics
  without weakening raw-output/refusal checks. Investigate the G4 reference timeout.
- Q01 continuation: finish math literal provenance/constexpr naming and split admission,
  polar production, per-depth conversion, Zoom/Rotation render stages, and Smart/Classic
  entry code. The main cpp still violates the approximately 1,000-line target; no claim
  that spec points 1/2/4 are complete. Preserve one translation unit and operation order;
  rerun G1 after each structural step, then all gates. Current includes are both under
  1,000 lines. No durable oracle bundle/worker was produced by this ticket.
