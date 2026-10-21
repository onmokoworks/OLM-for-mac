status: done

summary:
- Closed the PF8 unit-strength Alpha/box cluster by restoring reciprocal-multiply glow normalization and admitting its proven Smart tuple.
- Seed 1 Smart improves 103/0/197 to 130/0/170; fresh seed 4 improves 93/0/207 to 128/0/172 (exact/mismatch/refusal).
- Independent 260-case production matrix and 600 production campaign replays are sanitizer-clean; no prior Smart exact changes.
- Paired original/public/production-Smart trace matches all nine stages after the correction; 218 changed corpus samples all move to exact.
- Production corpus index8 is explicitly rebased refusal->exact; strict replay remains 8/8. Other PF8 seed pipelines remain outside this recovery.

facts:

Base: `cc42826f` (the C04 tiny-owner commit). Machine evidence is `reports/fuzz/olmkirakira_smart_C04_pf8.json`; original AEX/worker identities and host limitations are unchanged from `C04-kira-smart.md`.

First divergent stage and general operation:

- Independent `pf8-flat` index72, PF8 7x11, Alpha, Strength100, Mode1, Merge1, gain1, vertical Length1/Rotation0, fixed ray color and no ramps: original/public AEX and Mac source, scalar seed, and all five rays agree. The first divergence is **glow word0**, original little-endian `ccca4a3f`, Mac `cbca4a3f`; 68/308 float words differ. Final output differs at 2/308 bytes, first byte53 original `d9`, Mac `da`.
- Original `FUN_18114fd90` assembly `18114ff33..18114ff54` uses one `DIVSS` reciprocal and three `MULSS` products. Its decomp also records `fVar12 = 1 / alpha` followed by three multiplies. The PF8 port used three separate divisions. This is the first measured divergent operation, not a writer correction.
- The recovered operation now also runs for PF8 when Channel is Alpha and Strength is exactly100%. That is the original scalar seed branch with unit exponent. PF16/PF32 retain their F09 rule. Other PF8 seed branches retain their prior behavior: F09's non-unit-strength index77/sample167 witness is unchanged. This bounded recovery does not claim that separate division is correct for those unresolved branches.
- `IsAlphaBoxTuple` gains an explicit PF8 admission argument enabled only by Smart. All existing finite-SDR, unit strength/opacities, channel/mode/merge, default-ramp/color, angle, length and owner/storage constraints remain. Classic admission is unchanged. No coordinate, sample value, case index or expected output appears in production code.
- The corrected production Smart trace is exact at source, seed, five rays, glow and composed (9/9), independently bound to original public Smart. Final AEX/Mac SHA256: `e1fbb6c6347e3f63cf48822cbddf1f5dba54e7d701279ca47909d600410912ad`. The original ABI leaf check passes; no AEX numerical function is detoured.

| n300/jobs2 campaign | Smart exact | Mismatch | Refusal | Uncompared | AEX Smart output/reject |
|---|---:|---:|---:|---:|---:|
| seed1 before | 103 | 0 | 197 | 0 | 287/13 |
| seed1 corrected arithmetic, tuple gates off | 215 | 72 | 0 | 13 | 287/13 |
| seed1 after | 130 | 0 | 170 | 0 | 287/13 |
| seed4 before | 93 | 0 | 207 | 0 | 281/19 |
| seed4 corrected arithmetic, tuple gates off | 224 | 57 | 0 | 19 | 281/19 |
| seed4 after | 128 | 0 | 172 | 0 | 281/19 |

The full PF8 Alpha rule selects 35 seed1 and 40 seed4 inputs; all are gate-off/public exact, with overlaps in the prior zero-ray admissions. Newly admitted totals are27/35. All previous exact Smart result records are unchanged. All other statuses remain refusals, including every case without an AEX output. Every final campaign case is independently rerendered with ASan/UBSan: 600 routes, no sanitizer findings or admitted mismatch. Normal campaign Classic results remain 48 mismatch/252 refusal and 40/260, respectively, with their separate original Classic oracle.

Independent matrices under ASan/UBSan:

- 120 PF8 cases with default-ramp variations +120 with all ramp flags disabled: 10 geometries (1x1, rows/columns, 3x3, 5x3, 8x6, 7x11, 9x7, 17x11, 31x23), both box modes/merges, individual and combined rays, randomized source/color values, gain/angle/length variation and odd byte padding. All240 are original-Smart exact through production admission.
- 20 boundary cases: both box modes, Length1/1000 and Highlight min(Length,500), five raw angles including -2147483647 and2147483512, independent PF8 pixels/colors/default ramps. All20 are original-Smart exact through production admission.
- Earlier 84+84 tiny gate-off matrices also pass after normalization. Before the fix the ramp matrix stopped at index48 (one-byte difference) and the flat matrix at index72 (two-byte difference); their full counterexamples remain in the first cluster evidence. The failures supplied new boundary values, not two hypotheses rejected without a new observation.

Corpus audit/rebaseline:

| Input | Smart production before -> after | Separate diagnostic arithmetic audit |
|---|---|---|
| production index8 | refusal -> exact | no output produced before admission |
| T06 shrunk index78 (C62) | refusal -> exact | final bytes already exact and unchanged |
| T06 shrunk index42 | refusal -> refusal | 1 changed sample per route, mismatch -> exact |
| T06 shrunk index104 | refusal -> refusal | 108 changed samples per route, mismatch -> exact |
| all others | unchanged status/output | unchanged samples |

The standalone arithmetic audit holds admissions fixed and compares140 route renders: **218 changed samples, all now equal original Smart; zero away from exact**. The independent sanitized production corpus audit compares70 inputs with no numerical regression. Production index8 now hashes to `c9756ce9c0788c621582829142ee12038dbc71a632a0e3517fc53b09bdb0fbe5`; T06 index78 to `1218e7890e7fe362ea583290b3613f6cb3535e7de046a9d69d378870442a9c19`. Only production index8's result is updated, with its prior complete record retained under `C04_PF8_expectation_update`. Strict production replay is7/8 before,8/8 after. T06 remains a historical diagnostic corpus.

The25 existing fast tests pass (0.005s); `git diff --check` passes. MAIN, external emulator/source/workers, ledger/release gates and other plugins are untouched; no push/install/rebuild. Completed builds are removed before final delivery; scratch remains below5GiB.

inference:

Exact upstream planes, original instruction order, restoration of all glow words, and independent/fresh-seed/corpus results establish a port operation-order cause in the unit-strength scalar Alpha branch. Keeping the unresolved non-unit and color-seed pipelines outside this incremental normalization recovery preserves the required sample-level monotonicity. This does not establish arbitrary native UCRT/AE, custom ramps, HDR, ROI/downsample or other PF8 branches.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/verify_kirakira_smart_C04.py`
- `tools/emulation/summarize_kirakira_smart_C04.py`
- `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000008.json`
- `reports/fuzz/olmkirakira_smart_C04_pf8.json`
- `orchestra/reports/C04-kira-smart-pf8.md`
- `orchestra/reports/C04-kira-smart.md` (progress summary)

verify:

At this cluster commit, from the worktree (logs and builds remain in ticket scratch):

```sh
s="$PWD/orchestra/state/C04-kira-smart"
mkdir -p "$s/pf8-campaigns"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show cc42826f:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/tiny.cpp"
for seed in 1 4; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/tiny.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/pf8-campaigns/before-seed$seed.json" --corpus "$s/pf8-before-seed$seed-corpus" > "$s/pf8-before-seed$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/pf8-campaigns/after-seed$seed.json" --corpus "$s/pf8-after-seed$seed-corpus" > "$s/pf8-after-seed$seed.log" 2>&1
done
for family in pf8 pf8-flat pf8-boundary; do
  python3 tools/emulation/verify_kirakira_smart_C04.py --family "$family" --scratch "$s/recheck-$family" --report "$s/recheck-$family.json" > "$s/recheck-$family.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/tiny.cpp" --campaign-dir "$s/pf8-campaigns" --scratch "$s/recheck-pf8-campaign" --report "$s/recheck-pf8-campaign.json" > "$s/recheck-pf8-campaign.log" 2>&1
"$py" tools/emulation/trace_kirakira_smart_C04.py --production --require-exact --scratch "$s/recheck-pf8-trace" --report "$s/recheck-pf8-trace.json" > "$s/recheck-pf8-trace.log" 2>&1
```

Expected: table above;120+120+20 matrix exact;70 corpus comparisons and600 sanitized campaign routes pass;9 exact trace stages and final hash above. For the separate fixed-admission arithmetic audit, construct an after-source from current code with `IsAlphaBoxTuple(info, format, true)` changed only at the Smart call to `IsAlphaBoxTuple(info, format)` and run `audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/tiny.cpp" --after-source <that scratch file> --scratch <ticket scratch subdir> --report <ticket scratch JSON>`. Expected140 routes/218 samples toward exact. The originally measured arithmetic-only scratch source had identical executable arithmetic and unchanged admissions.

next:
- Third cluster: tiny scalar Mode3 Gaussian, with its first-ray fallback boundary already paired against original AEX. Exclude the newly observed five-tap Length1 residual until separately traced/recovered.
- Non-unit PF8 strength/opacities and four-channel color seeds remain unresolved; retain F09 index77/sample167.
