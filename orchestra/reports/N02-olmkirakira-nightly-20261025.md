status: done
summary:
- Fix the three retained overnight Smart PF32 scalar box refusals by admitting nonfinite luminance/maximum-RGB source through the existing recovered pipeline.
- Rendering arithmetic, Classic admission, geometry/work limits and R10 reference/fast selection remain unchanged.
- Both routes are recorded; the overnight failures and acceptance measurements concern Smart. Classic still has inherited refusals/mismatches.
- Smart fresh seeds: 1,788 exact / 12 original-unavailable / 0 mismatches / 0 Mac-only refusals; all390 corpus results true, default600 route comparisons unchanged, ref/fast mismatch0.

facts:

Base: `0c12f0ed0932bc85b59dd25b9b45a9641be51ac6`, branch
`orch/N02-olmkirakira-nightly-20261025`. Read AGENT_GUIDE, GOTCHAS, the plugin's
ledger decision row, compatibility plan, P02c/P03b and C38/C55 scalar reports.
No MAIN, ledger, release-gate, other-plugin, emulator-worker or cache-index edits.
No worker rebuild, push, stash or history rewrite. Commands were serial within
each driver, with at most two build/emulator processes across drivers.

### Initial reproduction and cause

Standard `tools/fuzz/run.py --replay` with matching geometry/size flags reproduced
all three Smart `tuple-or-source` refusals (error 516), while the original rendered.
The first odd-even attempt omitted its `--max-size 1080`; the runner correctly
rejected setup. Repeating with both size bounds 1080 reproduced the refusal.
This is recorded in the retained logs, not counted as a successful replay.

| Witness stem | Sampler | Geometry | Channel | Original/final Smart SHA-256 |
|---|---|---|---|---|
|275f210ea901a7ec7270f420|odd-even-v1 + realistic|1x1|luminance|`dfae447895cdf35c835cd3f1f69433e6522da94ba5969a86b01949cbb9a201a4`|
|894b9e527a8549c453de514b|realistic|1x2|luminance|`c39c89eedea071a6a330482b81130da068e66bd20845e2c6d41294a1c87f01d1`|
|f005762cfd5e3a7d4520b293|realistic-v2|1x1|maximum RGB|`374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb`|

All three are PF32/box mode 2 and contain negative infinity. The production
predicate `SmartFilteredInputIsSupported` previously required every scalar-box
source lane to be finite. Allowing its existing scalar brightness box tuple
through the source check makes all three final Smart outputs exact. Classic
continues to refuse all three; no claim of Classic equality is made.

Original constructor/fade evidence is preserved in
`C55-kira-smart-r2/approx/constructor-disassembly.txt`: `1811501b0` returns zero
for zero/unordered input, and `18114ed10..18114ed54` selects maximum RGB, applies
fade/powf and multiplies by alpha. `P03b-evidence/kira-static.txt` records the
original `181156740` clamp's COMISS/CMOVAE and `18115676a MAXSS(value,+0)`.
These existing binary-grounded operations remain unchanged.

`probe.py --witness ... --trace-index 0 --ucrt-math --require-exact` ran three
paired traces. The helper begins after owner geometry setup, so the script
explicitly materializes the witness's X-downsample ray lengths and removes host
geometry before tracing. Each normalized trace is bound to its public AEX
output **and** has the same output hash as the original geometric witness above.
This does not claim that the helper itself traces host rectangle negotiation.

- 275f: first internal difference is seed word 0, a NaN-bit difference; seed
  has one differing NaN word, as do each of rays 0–3.
- 894b: first internal difference is seed; one NaN word differs there, and two
  NaN words differ in each of rays 0–3.
- f005: seed is exact; first internal difference is ray0, with one NaN word
  differing in each of rays 0–3.
- All three have exact glow, glow_full, composition and output. The raw internal
  differences are retained in `summary.json`; they are not tolerance matches.

The trace helper initially failed because its writer insertion marker predates
P02c's output-sized loop and its generated source could not resolve the later
RampEditor header. Both plugin-only harnesses now resolve that header, and the
trace marker follows the actual output loop. No trace failure was counted as
numerical evidence. No uninitialized original read was established; no original
bug was declared and `KNOWN_ORIGINAL_BUGS.md` was not changed.

### Validation

| Sampler / seed | Inputs | Smart exact | Smart mismatch | Smart Mac-only refusal | Smart oracle unavailable | Classic mismatch / refusal |
|---|---:|---:|---:|---:|---:|---:|
|realistic / 2601|200|199|0|0|1|12 / 188|
|realistic / 2602|200|199|0|0|1|14 / 186|
|realistic / 2603|200|199|0|0|1|9 / 191|
|realistic-v2 / 2601|200|197|0|0|3|12 / 188|
|realistic-v2 / 2602|200|198|0|0|2|14 / 186|
|realistic-v2 / 2603|200|199|0|0|1|9 / 191|
|odd-even-v1 / 2601|200|199|0|0|1|15 / 185|
|odd-even-v1 / 2602|200|198|0|0|2|20 / 180|
|odd-even-v1 / 2603|200|200|0|0|0|15 / 185|
|default / 1|300|287|0|0|13|48 / 252|

- Fresh sampler total: **1,800 inputs, 1,788 Smart exact, 12 original-unavailable,
  zero Smart mismatches and zero Smart Mac-only refusals**. Seeds 2601/2602/2603,
  n200/jobs1 each; same sampler flags and 1080x1080 odd-even bounds as the witness.
- Default seed1/n300 before and after: **600 route comparisons unchanged**,
  zero exact-to-non-exact transitions; input hashes and parameter lists agree.
- Standard saved-result replay: **390/390 true**, including 8 main, 62 gate-off,
  272 P02c, 41 older reductions, four T15b and three new N02 witnesses. Both routes
  are recorded. The three new witnesses also replay true with `--reference-build`.
- Sanitized independent matrix: **384/384 exact**, covering both scalar channels,
  both box modes, both merges, 1x1/3x5/7x11, +infinity/-infinity/qNaN/sNaN in each
  ARGB component, with varying strength/fade/rays/Highlight. Earlier experiments
  separately measured 8/8 and 96/96 exact (the 96-case file is named `matrix192`
  from its initial scratch label; the measured count is 96, not 192).
- `tools/perf/ref_vs_fast.py --plugin olmkirakira --jobs 1`: **675 comparisons**
  across small/HD/4K and caps1/2/8: 648 exact, 27 identical refusals, zero mismatch.
- `git diff --check` and syntax parsing of the three new Python drivers pass.

The full per-route first failures, oracle/candidate identities, raw reports and
logs are committed compressed under `N02-kirakira-evidence/`. The original AEX
SHA-256 is `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
Final production source SHA-256: `ab7a507a548b10a6e660fbc0b50010699b4882389c00bacffaf6870821b184d9`.
All generated build directories were removed after these measurements.


The nightly runner explicitly selects `a.routes = (route,)`; the three retained
witnesses record only Smart. Current standard run.py additionally executes
Classic. Campaigns return exit 0 on completed measurements even with Classic failures; those failures are preserved in the reports,
not hidden or reclassified as original refusals. All newly-labelled corpus
entries record both observed routes. Historical corpus expectations are untouched.

inference:

The cause is an overly restrictive scalar-box source admission predicate, not a
missing renderer operation. The existing original-style aggregation/composition
clamps remove the observed internal NaN-bit differences. The fix admits that
existing PF32 full-resolution box tuple and retains its constructor, fade,
parameter, ramp, geometry and workload bounds. Other scalar Gaussian/approximation
nonfinite admissions are not inferred from this evidence. This is CPU-emulator
and source-host evidence, not a new native-AE validation or all-input proof.

changed_files:

- `mac/OLMKiraKira/OLMKiraKira.cpp`: scalar box nonfinite source admission only.
- `tools/emulation/trace_kirakira_numeric_F09.py`: current writer marker and local header resolution.
- `tools/emulation/verify_kirakira_admission_F10.py`: local header resolution for source-included probes/baseline.
- `tests/fuzz_corpus/olmkirakira_N02_nightly/`: three labelled witnesses and README.
- `orchestra/reports/N02-kirakira-evidence/`: reproduction drivers, compressed raw reports/logs and summary.
- This report.

verify:

Run from this worktree. Drivers use jobs 1 and redirect each underlying long
command to a ticket-local log. Run these serially; do not launch all phases in
parallel. Campaigns/default baseline return exit 0 on completion even with inherited Classic
failures; judge the recorded per-route results and the default comparison,
not the wrapper's exit status alone.

```sh
s="$PWD/orchestra/state/N02-olmkirakira-nightly-20261025"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
git show 0c12f0ed0932bc85b59dd25b9b45a9641be51ac6:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
python3 orchestra/reports/N02-kirakira-evidence/verify.py campaigns
python3 orchestra/reports/N02-kirakira-evidence/verify.py baseline
python3 orchestra/reports/N02-kirakira-evidence/verify.py replays
python3 orchestra/reports/N02-kirakira-evidence/verify.py nested
python3 orchestra/reports/N02-kirakira-evidence/verify.py reference-witnesses
python3 orchestra/reports/N02-kirakira-evidence/verify.py perf
python3 orchestra/reports/N02-kirakira-evidence/probe.py --require-exact --scratch "$s/recheck-matrix" --report "$s/recheck-matrix.json" > "$s/recheck-matrix.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
for witness in tests/fuzz_corpus/olmkirakira_N02_nightly/*.json; do
 name=$(basename "$witness" .json)
 "$py" orchestra/reports/N02-kirakira-evidence/probe.py --witness "$witness" --trace-index 0 --ucrt-math --require-exact --scratch "$s/recheck-trace-$name" --report "$s/recheck-trace-$name.json" > "$s/recheck-trace-$name.log" 2>&1
done
git diff --check
```

Expected: 384 matrix exact, three public-bound output-exact traces (internal
NaN differences as recorded), all 390 saved corpus results true, and 675
reference/fast comparisons with zero mismatches. Fresh-seed/default counts and
remaining route limitations are in Validation above. The inherited nested
`other_reductions` corpus uses its original SHA-bound worker path; standard
replay verifies that hash. No reference worker was rebuilt or copied.

next:

Review/merge this Smart nightly fix. Classic geometry,
admission and existing output differences remain a separate follow-up; preserving
its old behavior here is not a claim that those cases are compatible. No two
numerical hypotheses were refuted; the stop-rule threshold was not reached.
