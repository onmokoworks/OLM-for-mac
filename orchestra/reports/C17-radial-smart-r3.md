status: blocked

summary:
- Re-measured seed-1 n300 Smart: 241 exact / 0 mismatch / 59 refusal, unchanged from C11.
- PF16 Rotation center admission exposes the existing external expf tail boundary; no admission promoted.
- Type-3 zero-noise neutralization and zero-span hypotheses both fail; paired traces isolate distinct source-span and Zoom prepass boundaries.
- Production source/core are unchanged. All 300 sanitized production replays, eight smoke tests, and all 35 corpus replays pass.
- Committed reproducible negative experiments, typed trace improvements, fixtures, and hash-bound evidence. Three clusters were not closed.

facts:

FACT: Started at `dd7d8fa1f9c457628d2837aed81cce4016399d81` on
`orch/C17-radial-smart-r3`. Read AGENT_GUIDE, the RadialBlur ledger entries,
compatibility plan, GOTCHAS, and the radial triage/fix reports, including C06/C11
and F10/F12 admission methodology. No MAIN/cache/emulator writes, worker rebuild,
release-gate/ledger edit, installation, push, stash, or history rewrite. No tool
permission rejection occurred. Scratch stayed inside this worktree's ticket
state directory, well below 5 GiB; regenerable build directories were removed.

Bindings:
- AEX SHA256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- Pinned worker SHA256: `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`.
- Production `.cpp` SHA256: `d569b69db194cb60734e02eb9cd25d49080021daf998b6f6415e0eb5d7940801`.
- Numerical evidence is raw original-AEX CPU Smart output under the pinned
  Unicorn worker. It is not native Windows UCRT/AE or GPU evidence.
- Archived adapter calibration is still 4/6; the two old PF32 hashes are not
  used as numerical expectations. Each comparison uses its fresh original run.

The baseline command below completed 300 cases in 102.9811 seconds. Original
Smart: 278 ok / 20 reject / 2 timeout. Mac Smart: 241 exact / 0 mismatch / 59
refusal. Neither timeout was a Mac exact case. Original-renderable refusal census:

| Guard | Count |
|---|---:|
| generic-world-not-admitted | 14 |
| smartrender-generic-budget | 8 |
| unadmitted-zoom-profile | 6 |
| type3-zero-noise | 4 |
| zoom-noise-plane-failure | 4 |
| host/no production guard | 1 |

PF16 Rotation center experiment (largest generic-world group):

FACT: Scratch-only removal of PF16 Rotation's in-frame-center restriction made
seed-1 cases 172 and 250 exact. All other 35 original-renderable refused rows
remained refused. All 37 diagnostic renders were sanitizer-clean. This alone
was insufficient for promotion. The independent C11-derived PF16 Rotation
matrix has 36 references / 108 layouts: 105 exact, 3 mismatches, all clean.
All three failures are one input (index 30): 11x7, Center (5.5,-5.75), Quality 1,
Strength 4, Outer/Inner Fade 25/50, Repeat Border off. First differing PF16 word
41 (byte 82): AEX `b049`, Mac `af49`; one word/one byte differs.

FACT: The trace CLI accepts RGBA8 PNGs, so the original arbitrary PF16 matrix
input cannot be transported unchanged. Sixty-five correctly promoted PNG
variants all matched at final PF16 output. They are controls, not traces of the
failing arbitrary typed input. The retained first control nevertheless exposes
upstream differences. Its public session and trace hashes are equal; Mac
instrumented output equals its public Smart output. Dimensions are 360x13.
Polar/scalar/span match. The first differing weight is inner fade, length 10,
word 8: AEX `a5ed653d`, Mac `a4ed653d`; outer fade length 5 matches. Preaccum
has 31 differing words, premax 8, accum 31, max 8, normalized 12.

FACT: Original B680's scalar tail calls expf. The pinned worker binds it to
`f32::exp`. Independent host expf reproduces `a5ed653d`; double-exp-cast
reproduces `a4ed653d`. A scratch-only float-exp substitution for the fade scalar
tail makes all 36 original independent references / 108 layouts exact and clean,
including the arbitrary typed failure. The transported control's eight paired
planes then all match. This substantiates the same external length-10 boundary
as C11; the diagnostic import substitution was NOT applied to production or
used to promote center admission.

Type-3 zero-noise experiments:

FACT: Normalizing Type 3/NV0 to Type 1/NV0 in a scratch source makes cases 96 and
297 exact, but 93 and 239 mismatch. All 37 diagnostic renders are clean.
Case 93: the neutral experiment differs in **281 words / 560 bytes**,
first word 0 AEX `0280`, Mac `ef80`. Case 239: 12 words / 14 bytes, first word 0
AEX `0000`, Mac `4100`. Neither candidate rule was promoted.

FACT: A separately generated, losslessly PNG-transportable case-239 input
reproduces a mismatch. Its Rotation trace has dimensions 1800x14. Polar,
preaccum and premax match; source span is 22 zero floats in the AEX versus 22
ones in the neutral candidate. The sampled scalar plane differs in all 25,200
words; first AEX `00000000`, Mac `0000803f`. Accum differs in 15,672 words,
max in 253, normalized in 9,858.

FACT: A second scratch hypothesis admits Type3/NV0 and initializes its source
span to zero. This makes 96/239/297 exact, but case 93 still differs in 280
words / 554 bytes: first word 0 AEX `0280`, Mac `0000`. All 37 diagnostic
renders are clean. A losslessly transported case-93 input traces through Zoom:
polar, eligibility and span all match; first divergence is now preaccum
(108,124 words) and premax (27,031), retained in accum/max and normalized
(108,124). This moves the boundary upstream of final sampling/writing, without
establishing a safe promotion rule.

FACT: Static AEX `65C0` branches on Type 3 and skips span writes when the layer
pointer at owner +0xA8 is null. `45A0` allocates float storage through PF Handle
Suite; it does not explicitly fill that storage. The retained host allocates
new mapped handle regions. These observations do not prove native AE allocation
contents or the complete Type3/NV0 checkout contract. The diagnostic zero-span
rule is deliberately not production behavior.

Verification and corpus accounting:

| Check | Result |
|---|---|
| Production seed-1 ordinary before / retained production | 241/0/59 → 241/0/59 |
| Production ASan/UBSan replay | 300/300 same, 300/300 clean |
| Existing selected smoke tests | 8/8 pass |
| Corpus Smart before/after | 35 exact → 35 exact, identical hashes |
| Corpus full saved result objects | 35/35 unchanged |
| Production `.cpp` and core | unchanged |

FACT: No corpus was rebaselined because no result changed. No fresh seed is
claimed: all candidate rules were rejected before promotion. No second or third
production cluster commit exists. The report and tools constitute a blocked
investigation deliverable, not a compatibility improvement.

FACT: Development failures are retained in logs: the first PF16 trace rejected
its session/trace hash binding because the inherited conversion used truncation;
the corrected PNG promotion is `(byte*32768+127)//255`, matching worker source.
One instrumentation insertion asserted against two weight-cache sites instead
of one; it now targets the first, paired-prepass site. The 72x1 Zoom trace first
hit the harness's 64-pixel limit, then passed with the same 256-pixel limit as the
fuzz harness. The audit first encountered a relative corpus path and now resolves
it explicitly. Incomplete runs are not acceptance evidence.

inference:

INFERENCE: PF16 Rotation's observed center-matrix failure is caused by the
pinned reference's unresolved expf import convention, not the center predicate.
Changing production math to fit this worker would not resolve native UCRT truth.

INFERENCE: Type3/NV0 is not equivalent to procedural neutral noise. Missing-layer
span initialization and Zoom's distinction between size-factor/prepass ownership
and scatter span require separate work. Treating every observed zero as a general
zero-fill contract would overstate the evidence. The two Type3 hypotheses were
refuted; new stage boundaries were obtained, so this is not a claim that the
literal two-hypotheses-without-new-boundary stop threshold fired. Work stops
blocked because no safe general admission was established; the unresolved host
contract and prepass ownership are explicitly handed off instead of promoting a
partially exact rule.

changed_files:
- `tools/fuzz/probe_radialblur_smart_C17.py`: reproducible scratch-only rejected admission/import hypotheses.
- `tools/fuzz/verify_radialblur_centers_C17.py`: independent PF16 Rotation matrix.
- `tools/fuzz/transport_radialblur_rotation_C17.py`: reproducible typed transport controls/witnesses.
- `tools/fuzz/trace_radialblur_rotation_C11.py`: typed transport, prepass and fade-weight trace comparisons, ticket-independent scratch root.
- `tools/fuzz/trace_radialblur_smart_C06.py`: correct PF16 PNG promotion and 256-pixel diagnostic harness limit.
- `tools/fuzz/audit_radialblur_C17.py`: hash-bound audit and independent expf check.
- `tools/fuzz/fixtures/radialblur_{rotation_control,type3_rotation,type3_zoom}_C17.json`: lossless trace inputs.
- `orchestra/reports/C17-radial-smart-r3.evidence.json` and this report.

verify:

Run from this worktree. All outputs stay in ticket scratch; use a fresh `$S` if
repeating because diagnostic output directories must not already exist.

```sh
PY='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
W='/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker'
S="$PWD/orchestra/state/C17-radial-smart-r3/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S"
"$PY" tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 2 --worker "$W" --case-timeout 30 --budget-minutes 120 --shrink-attempts 0 --shrink-seconds 0 --scratch "$S/base-build" --corpus "$S/corpus" --report "$S/base.json" > "$S/base.log" 2>&1
for E in centers16 centers16-hostexp type3-zero type3-zero-span; do
  "$PY" tools/fuzz/probe_radialblur_smart_C17.py --experiment "$E" --campaign "$S/base.json" --output "$S/$E" > "$S/$E.log" 2>&1
done
"$PY" tools/fuzz/verify_radialblur_centers_C17.py --source "$S/centers16/experiment.cpp" --independent --output "$S/centers16-independent" > "$S/centers16-independent.log" 2>&1
# Expected exit 1: one reference fails in three layouts. Continue explicitly.
"$PY" tools/fuzz/verify_radialblur_centers_C17.py --source "$S/centers16-hostexp/experiment.cpp" --independent --output "$S/centers16-hostexp-independent" > "$S/centers16-hostexp-independent.log" 2>&1
"$PY" tools/fuzz/trace_radialblur_rotation_C11.py --source "$S/centers16/experiment.cpp" --fixture tools/fuzz/fixtures/radialblur_rotation_control_C17.json --output "$S/rotation-weights-trace2" > "$S/rotation-weights-trace2.log" 2>&1
"$PY" tools/fuzz/trace_radialblur_rotation_C11.py --source "$S/centers16-hostexp/experiment.cpp" --fixture tools/fuzz/fixtures/radialblur_rotation_control_C17.json --output "$S/rotation-hostexp-trace" > "$S/rotation-hostexp-trace.log" 2>&1
"$PY" tools/fuzz/trace_radialblur_rotation_C11.py --source "$S/type3-zero/experiment.cpp" --fixture tools/fuzz/fixtures/radialblur_type3_rotation_C17.json --output "$S/type3-trace" > "$S/type3-trace.log" 2>&1
"$PY" tools/fuzz/trace_radialblur_smart_C06.py --source "$S/type3-zero-span/experiment.cpp" --cases-from tools/fuzz/fixtures/radialblur_type3_zoom_C17.json --indices 93 --no-shrink --output "$S/type3-zoom-trace2" > "$S/type3-zoom-trace2.log" 2>&1
"$PY" tools/fuzz/verify_radialblur_smart_C06.py --campaign "$S/base.json" --smoke --output "$S/production-verify" > "$S/production-verify.log" 2>&1
"$PY" tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --jobs 2 --worker "$W" --case-timeout 30 --scratch "$S/replay-build" --corpus "$S/replay-corpus" --report "$S/replay.json" > "$S/replay.log" 2>&1
"$PY" tools/fuzz/audit_radialblur_C17.py --state "$S" --output "$S/audit.json" > "$S/audit.log" 2>&1
```

Expected: the counts, first words, stage counts, and preserved hashes above.
Oracle timeouts may vary on refused cases; do not reinterpret a timeout as exact.
The audit checks production identity, 241/0/59, independent expf bits, eight
matching diagnostic Rotation planes, sanitized production, and corpus hashes.

next:
- Resolve native-UCRT scalar expf provenance before extending PF16 Rotation center or related PF32 admissions. The full arbitrary-input matrix now has a causal diagnostic.
- Trace Type3/NV0 public layer pointer/allocation initialization and Zoom prepass size-factor ownership using the retained typed witnesses. Keep all Type3 admissions unchanged meanwhile.
- Remaining budget and invalid-noise-index refusals were counted, not relaxed or closed; no third cluster is claimed.
