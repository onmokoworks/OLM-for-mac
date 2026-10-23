status: blocked

summary:
- F46 seed-1 n300 Smart: 257 exact / 0 mismatch / 40 refusal / 3 uncompared.
- Seven AEX-rendered noise-plane refusals reach negative table indices; kept the safety check.
- Two scratch nonfinite-admission hypotheses both produce four mismatches, with no exact gains.
- All 257 baseline exact hashes survive both sanitized experiments; production and corpus are unchanged.
- Stopped under the two-refuted-hypotheses rule; zero clusters promoted.

facts:

FACT: Starting HEAD `0a17ec49803a6487b5bff048d020606bc9415b7f`, branch
`orch/C44-radial-smart-r7`. Read AGENT_GUIDE, GOTCHAS, compatibility plan,
Radial ledger row and prior C11/C17/C35/C41/F41/F29 reports. No MAIN, emulator,
release gate, ledger, other-plugin, or production changes; no worker rebuild,
push, stash, history rewrite, or delegation.

FACT: F46 worker SHA256
`6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`;
AEX SHA256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
Production Radial source remains SHA256
`ec002eced181a0fcbda78cb8f1242ab9a9958df08697b716b80053b59de3242f`.
Full baseline report SHA256
`ab3a1cb4a4d20a0ea60508ec04446210ba7e64d9961997383be2e6fc4f536bd9`.

FACT: Ordinary requested n300/seed1/jobs1 measurement exited 0 and completed
300 cases, using default 10-second oracle limits and default shrinking.
Smart oracle: 276 rendered / 20 rejected / 4 budget. Mac Smart: 257 exact,
40 refusal, 3 uncompared, zero mismatch. Uncompared indices 4/62/298 are
oracle budgets; the ticket's 258/0/40/2 count is not reproduced because index62
is uncompared in this run. No claim of an exact loss is inferred from timeout.
Historical calibration is 4/6, not treated as new exact evidence.

FACT: Among AEX-rendered refusals: noise-plane failure7 (76/77/108/123/144/214/282),
Type3/NV0 five (93/96/239/280/297), nonfinite generic-world/Zoom-profile four
(17/89/238/247), Smart generic budget two (48/148), host/no guard one (248).
`triage_radialblur_C44.py` instruments only a scratch copy of the current
noise generator at its existing invalid-index check. All seven noise failures
reach first indices respectively -1/-1/-6/-1/-2/-1/-1. All seven diagnostic
processes exit0 with empty sanitizer stderr and never perform the invalid read.
Parameter conversion uses the production signed AD-to-radian constant and
FLOAT32 MT stream. This diagnoses the Mac refusal; original out-of-allocation
reads at RVAs 95CD/95D8 are grounded by the existing C11 report, not a newly
captured native memory trace. No lower wrap or clamp was invented.

FACT: C17's existing paired Type3 evidence leaves missing-layer allocation
contents and Zoom prepass ownership unresolved. Those five cases were not
rerun with an assumed zero-fill rule. They remain outside this promotion.

FACT: Hypothesis 1: with the current F46 UCRT imports, removing only the
finite-input admission predicate might suffice. Sanitized replay of all 300
baseline inputs refutes this: 257 exact / 4 mismatch / 36 refusal / 3 uncompared.
Mismatch indices 17/89/238/247. Lost baseline exact hashes: zero; sanitizer
failures: zero. Every mismatch's original Smart output was freshly rerendered
and required to match the baseline oracle hash.

FACT: Static disassembly of the original source sampler at RVA1520 shows
contribution-first SSE destinations (e.g. 161B,1632,1641,1646), and
`UCOMISS`/`JNE` at 1798/179B that also exits on unordered alpha. This is static
evidence, not a measured first-divergent public stage. Hypothesis 2 adds the
prior C35 zero-weight/zero-alpha corrections, generated-invalid sign handling,
destination-first NaN selection in the four RadialF32 helpers, and those
source-sampler operand/branch differences. Its sanitized full replay still
has the same four mismatches and identical status totals. Zero baseline exact
hash losses and zero sanitizer failures. These scratch changes are unpromoted.

| Case | Gate-only differing words | SSE/source differing words | First word | AEX word (LE hex) | Both candidate words |
|---|---:|---:|---:|---|---|
| 17 | 1262 | 923 | 0 | 0000807f | 4623c1ff |
| 89 | 324 | 267 | 0 | 00000000 | 4623c1ff |
| 238 | 237 | 140 | 40 | 9beb483e | 4623c1ff |
| 247 | 562 | 527 | 4 | 68e9513d | 4623c1ff |

FACT: Both hypotheses fail without a new paired intermediate boundary value.
Numerical experiments stopped here. No fresh-seed promotion qualification was
run because seed1 already rejects both rules. The first attempt to build the
gate-only diagnostic exited1 because its scratch snapshot omitted the Strings
translation-unit symlink; the committed reproducer fixes that plumbing. This
was not a permission rejection or a numerical hypothesis result.

FACT: Full unchanged corpus replay exited0: 36/36, `replay_matches_saved=true`,
using the recorded F45 worker. Rebaseline table: 36 unchanged saved records,
zero modified records. This is saved-result stability, not a claim of Classic
conformance. ASan/UBSan candidate executions: 600, zero reported failures.
AST parsing passes. The staged whitespace check found trailing spaces in the
disassembly text; a follow-up commit removes them, and the final diff check passes. All started sessions finished;
regenerable build directories removed. Retained scratch 5,325,991 bytes,
well below 5GiB. No permission rejection occurred.

inference:

INFERENCE: AEX output after a negative noise-table index depends on memory
outside the owned table; exact output alone does not establish a safe general
port rule. Keep these refusals. Type3 allocation needs a separate host contract.
For nonfinite input, lower mismatch counts do not prove that any individual
arithmetic change is sufficient or safe. F46 math parity plus source-sampler
NaN handling does not close the public pipeline. The next experiment needs
lossless typed paired stage values, starting with source unpack/polar and then
preaccumulation/normalization, before changing later sampling or writers.

changed_files:
- `tools/fuzz/probe_radialblur_C44.py`: reproducible scratch-only hypotheses and sanitized per-case baseline comparison.
- `tools/fuzz/triage_radialblur_C44.py`: safe first-invalid-index attribution.
- `orchestra/reports/C44-evidence/`: full baseline/candidate/replay results, noise attribution, original sampler disassembly.
- This report. No production or corpus changes.

verify:

Run from this worktree; all output/builds stay in a new ticket scratch directory.
The two probe commands intentionally exit1 on their four known mismatches.

```sh
s="$PWD/orchestra/state/C44-radial-smart-r7/recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 1 --scratch "$s/baseline" --corpus "$s/corpus" --report "$s/baseline.json" > "$s/baseline.log" 2>&1
python3 tools/fuzz/triage_radialblur_C44.py --campaign orchestra/reports/C44-evidence/baseline.json --output "$s/noise" > "$s/noise.log" 2>&1
python3 tools/fuzz/probe_radialblur_C44.py --experiment gate-only --campaign orchestra/reports/C44-evidence/baseline.json --output "$s/gate-only" > "$s/gate-only.log" 2>&1
python3 tools/fuzz/probe_radialblur_C44.py --experiment sse-source --campaign orchestra/reports/C44-evidence/baseline.json --output "$s/sse-source" > "$s/sse-source.log" 2>&1
python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --jobs 1 --scratch "$s/replay" --report "$s/replay.json" > "$s/replay.log" 2>&1
git diff --check
```

Expected: baseline300 completed, zero Smart mismatches (timeouts may change
exact/uncompared counts); noise7 invalid indices above; each probe four
mismatches, zero lost exact, zero sanitizer failures; corpus36 saved matches.
Original measured commands used `baseline`, `noise-triage`, `gate-only-retry`,
`sse-source`, and `replay` directly under ticket scratch instead of `recheck`.

next:
- No cluster closure commit is available; review this blocked diagnostic commit only.
- Obtain F46-bound typed raw full-stage nonfinite traces; do not transport NaN inputs through PNG or silently switch to an older watch worker.
- Separately resolve the Type3 missing-layer allocation contract and two Smart budget refusals; retain invalid-index safety checks.
- After a grounded fix, seed1 plus a fresh seed, exact-hash preservation, sanitized admission, and corpus replay remain mandatory.
