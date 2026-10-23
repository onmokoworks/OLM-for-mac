status: done
summary:
- Built and registered a configurable resident Smart trace worker; all ten C49 original output hashes are unchanged.
- Located the first divergence after exact source expansion; restored general SSE arithmetic/order and unordered branches.
- All ten witnesses match at six complete plane boundaries and final output; final O2/ASan/UBSan checks are 20/20 exact.
- Seed 1/105/fresh 54321 n300: 820 Smart exact, 0 mismatch; 900 sanitizer results agree with O2, 537 previous exact hashes preserved.
- Lifted only generic PF32 finite-input admission; 61 corpus outputs preserved. Missing-layer refusal remains.

facts:

FACT: Base `6deee17af05b59d01ec02fe340b3afda415fa40e`, branch
`orch/C53b-radial-trace-worker`. Read AGENT_GUIDE, GOTCHAS, C53/F49/C49/C44
reports, the compatibility plan and RadialBlur ledger restrictions. No MAIN,
04_Tools/AEXCompat*, release gate, ledger, corpus expectations or other-plugin
implementation changes. No delegation, push, stash or history rewrite.

FACT: Scope is original 2025 CPU AEX in Unicorn versus the public Mac EffectMain
fake SDK host, raw ARGB PF32, origin zero. AEX SHA256:
`ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
The untraced F46 reference worker remains
`6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.

FACT: Ran `python3 tools/emulation/aexcompat_patches/build_C53b.py`, then
`build_C53b.py --rebuild` to enlarge read-only snapshots from 1 MiB to 16 MiB.
The initial worker built successfully; the first larger-limit patch attempt
failed before Cargo because its replacement also changed an old-context line.
Corrected the patch, restored this ticket's first source snapshot, and reran
`--rebuild` successfully. No arithmetic change was involved in either build.
Final build: memory free 45% (initial build 49%), Cargo offline/locked/jobs=1,
exit 0, one existing dead-code warning. Space-free build tree was deleted.

Durable paths, registered under the INDEX lock:

- Source: `~/.cache/olm-emu/src-C53b/reference-guest`
- Worker: `~/.cache/olm-emu/worker-C53b-trace/aex-guest-worker`
- Manifest: `~/.cache/olm-emu/worker-C53b-trace/build.json`
- Worker SHA256: `df51edc461ee13ae826c94e62b29c17b813181ef1c2719388e4d9faf180099a2`

Against F49-v2's verified source manifest, exactly `classic.rs` and `x64.rs`
changed, with no added source files. Changes expose JSON-configured resident
watches and raise the diagnostic read limit. Arithmetic/import/host behavior
is unchanged. Function and direct-call instruction selectors, pointer offsets,
plane sizes, and occurrence selection are configurable. Indirect/arbitrary
instruction hooks remain unsupported and explicitly reported by the existing
engine; see the adjacent usage document.

FACT: Traced seed1 17/89/238/247 and seed105 25/105/148/185/255/291.
The final worker's full-plane run binds all ten inputs to C49 input hashes and
reproduces all ten saved successful original output hashes, with guards intact
and clean sessions. The full run has 101 witnesses; an additional full Rotation
capture has 10 witnesses and the same saved output hash. Selected captures have
zero unhookable watches, dropped witnesses or trace truncation. A separate
1:89 probe verifies an instruction selector at call-site 0x5C1A as well as
function selectors: 9 witnesses, saved output unchanged. The earlier full-run
report has a loop-variable label bug (`worker` labels such as `max`); its worker
hash, trace build identity, executable and all numerical bindings are unaffected.
The committed reproducer fixes that labeling. A final full reproduction run
then binds 10/10 originals, captures 127 witnesses, and compares all sixty full
planes plus ten outputs exactly with the committed diagnostic scripts.

FACT: First measured divergence: source expansion is byte-exact on all ten;
Zoom polar generation differs. For seed1:17, source is 48,032 bytes exact and
polar is 2,361,600 bytes with 152,803 differing words. First differing word is
index 1: AEX `ffc00000`, Mac `7fc00000` (integer bit notation). Across the nine
Zoom cases, baseline polar has 978,210 differing words. Full-plane sizes come
from paired geometry, not guessed byte windows; the largest is 4,608,000 bytes.

FACT: Successive causal boundaries, with original instructions retained:

- Source samplers 1520/9FC0/A270 evaluate zero-weight in-bounds taps, accumulate
  new weighted terms before the destination, preserve accumulated RGB when
  alpha is zero/unordered, and normalize blue with the reciprocal as operand
  one. `sse_add/sub/mul/div` preserve NaN operand selection and invalid sign.
  All nine Zoom polar planes then match completely; final output still differs.
- B150's B25A/B26B UCOMISS/JZ clears all four seed channels for zero/unordered
  alpha or factor. B54C/B550/B55D multiply the scalar before RGB. Restoring
  these yields nine exact prepass planes; five final outputs match.
- A9D0 skips zero/unordered scatter scalar/span, adds contributions before
  existing accumulators, and 5CEC/5CEF normalization takes the zero branch on
  unordered maximum alpha. Nine scatter accumulator, maximum-alpha and
  normalized planes then match; five final outputs still match.
- Final sampler 9D80 uses contribution-first alpha/RGB sums, skips reciprocal
  normalization on unordered alpha, and multiplies blue in the opposite operand
  order. The PF32 owner retains RGB-first multiplication by finite Gain
  (83ED/83F7/8401). All nine Zoom outputs match.
- Rotation 105:148 already has an exact source/polar plane after the common
  sampler fix. Its first prepass difference is word 28,800: AEX `00000000`, Mac
  `7fc12345`; 219,716 prepass words differ. Equivalent ordered tests at
  2885/2892, 2626/2630, contribution-first scatter and 1000 final sampling
  restore all six planes and its output exactly.

`check_radialblur_c53b_evidence.py` verifies 60 full-plane byte comparisons,
ten bound final-output hashes and twenty final-source O2/sanitized results.
Each arithmetic refinement gained an exact boundary; the two-refuted-hypotheses
stop condition was not reached. No tolerance, coordinate rule, expected-value
patch or final-byte adjustment was used. Existing `core/x86_float.h` is reused
without modification.

FACT: Qualification ran with the production arithmetic and scratch-only finite
admission removal before lifting the production gate. All three campaigns
completed 300/300, jobs=1, shrink-attempts=0, 10-second oracle timeout:

| Seed | Smart exact | mismatch | refusal | uncompared |
|---|---:|---:|---:|---:|
| 1 | 275 | 0 | 11 | 14 |
| 105 | 271 | 0 | 9 | 20 |
| 54321 (fresh) | 274 | 0 | 12 | 14 |

Uncompared rows are original rejection/budget results, not numerical passes.
All 272 previous C49 seed1 exact hashes and 265 seed105 exact hashes survive,
including cases whose newly attempted oracle did not complete. The ten newly
admitted originals match their saved references.

FACT: Sanitized replay checks every candidate status/output hash against its
O2 campaign, including refused/uncompared cases: 900/900 agree, zero sanitizer
diagnostics. ASan/UBSan halt-on-error enabled. The first sanitizer configuration
requested LeakSanitizer, unsupported on this macOS runtime; its 300 processes
failed before rendering with that explicit diagnostic. Removed that option and
reran all required checks successfully. This does not claim leak detection or
instrumentation of the pre-existing UCRT static library.

FACT: Corpus replay completed 61/61. All saved candidate output hashes and refusal outcomes are
preserved on both routes; 59 whole result objects match. Original Smart renders
for `C46_seed1_case000280` and `C49_seed1_case000117` reject in this run, making
replay exit 1; their Mac hashes still equal the saved successful originals.
Smart: 59 fresh exact, 2 retained-reference exact, 0 mismatches. Classic remains
outside promotion: 1 exact, 29 historical mismatches, 31 refusals, all preserved.
No corpus expectation was changed, added, or removed. `audit_radialblur_C53b.py`
exits 0 and independently checks preservation, 900 sanitizer matches and zero
campaign mismatches.

FACT: After qualification, removed the finite-only predicate and its two generic
PF32 call sites. Existing storage/parameter/budget and missing-layer checks stay
in place. Final-source ten-witness replay: O2 10/10, ASan/UBSan 10/10 exact.
Both final builds bind source SHA256
`344a4bb535f79181e63b5d77d23bc38a1fe90e42304c896960e058e193516740`.

FACT: Missing-layer static evidence: PF32 owner 8078 selects Type3, 80C3 loads
context+0xA8, and 80CA reads that world's height directly, with no intervening
null-pointer test. The width comparison at 8113 follows; dimension mismatch
clears context+0xA8 at 8120. Later 65C0 checks Type3 and null at 65F1/65F9,
jumping to its return path without populating the span plane. This does not
establish a zero-image or source-substitution rule, nor prove that a real AE
checkout can return the same missing-world fixture. The Mac noise-world refusal
is untouched.

FACT: Diagnostic scaffold attempts initially hit an overly broad insertion
marker, missing Strings symlinks, and a helper inside an inactive test seam;
these failed before measurement and were corrected. All successful evidence
comes from the later named runs. Scratch is approximately 1.4 GiB, below 5 GiB;
regenerable worktree and cache build trees were deleted. All started processes
completed. No permission rejection occurred. Python syntax and whitespace checks
pass. Evidence includes complete traces, paired final planes, experiments,
qualification reports/logs, build manifest and uncompressed SHA256 manifest.

inference:

INFERENCE: These measured boundaries support general SSE operation/branch
semantics for the generic PF32 implementation, rather than case-specific
admission. Finite fuzz coverage, the ten retained nonfinite inputs and existing
corpus do not prove every float payload or native Windows/AE behavior. The
missing-layer worker skips population after its nullable internal state; owned
allocation contents and actual host checkout semantics still require evidence.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `tools/emulation/aexcompat_patches/{build_C53b.py,C53b-resident-watches.patch,C53b-resident-watches.md}`
- `tools/emulation/{probe_radialblur_c53b_trace.py,probe_radialblur_c53b_mac.py,compare_radialblur_c53b.py}`
- `tools/emulation/{capture_radialblur_c53b_static.py,archive_radialblur_c53b.py,check_radialblur_c53b_evidence.py}`
- `tools/fuzz/{verify_radialblur_C53b.py,audit_radialblur_C53b.py}`
- `orchestra/reports/C53b-evidence/*`
- This report.

verify:

Fast committed-evidence and final public witness checks (no worker rebuild):

```sh
S="$PWD/orchestra/state/C53b-radial-trace-worker/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/emulation/check_radialblur_c53b_evidence.py
python3 tools/fuzz/verify_radialblur_C53b.py --witnesses --output "$S/witnesses" > "$S/witnesses.log" 2>&1
python3 tools/emulation/probe_radialblur_c53b_mac.py --experiment rotation --output "$S/mac" > "$S/mac.log" 2>&1
python3 tools/emulation/probe_radialblur_c53b_trace.py --mac-planes "$S/mac" --output "$S/trace" > "$S/trace.log" 2>&1
python3 tools/emulation/compare_radialblur_c53b.py --trace "$S/trace" --mac "$S/mac" --output "$S/planes.json"
git diff --check
```

Expected: 60 exact full planes, ten bound original outputs, 20/20 final public
witnesses; live paired comparisons have zero differing words and ten exact
outputs. Diagnostic Mac replay explicitly reads the pinned starting revision
and applies the measured transformations; the separate witness command tests
the current production source.

Full qualification (run sequentially; fresh output directories):

```sh
for seed in 1 105 54321; do
  python3 tools/fuzz/verify_radialblur_C53b.py --seed "$seed" --output "$S/seed$seed" > "$S/seed$seed.log" 2>&1 || exit
done
python3 tools/fuzz/verify_radialblur_C53b.py --sanitize-campaign "$S/seed1/campaign.json" --output "$S/san1-fixed" > "$S/san1.log" 2>&1
for seed in 105 54321; do
  python3 tools/fuzz/verify_radialblur_C53b.py --sanitize-campaign "$S/seed$seed/campaign.json" --output "$S/san$seed" > "$S/san$seed.log" 2>&1 || exit
done
python3 tools/fuzz/verify_radialblur_C53b.py --replay tests/fuzz_corpus/radialblur --output "$S/corpus" > "$S/corpus.log" 2>&1
python3 tools/fuzz/audit_radialblur_C53b.py --state "$S"
```

Expected: 0 Smart mismatches, 900 sanitizer matches, 537 previous exact hashes
and all 61 corpus candidate outputs preserved. Oracle availability and exact/
uncompared counts can vary; corpus replay can exit 1 on the two noted original
stops. The audit must still pass. Original qualification used `--admit-nonfinite`
for the scratch gate-removal phase; the final source no longer needs it.

next:
- Nonfinite generic PF32 ticket is complete for the measured emulator/SDK scope.
- Separate ticket: missing-layer checkout, internal allocation lifetime/contents
  and null-vs-empty-world semantics; keep the existing refusal until proven.
- Native AE/Windows and wider arbitrary-payload/host coverage remain separate.
