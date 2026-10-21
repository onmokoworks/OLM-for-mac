status: done

summary:
- Bound all nine dual-route fuzz adapters to matching original Classic/Smart commands; Smoother v1 retains its explicitly documented Classic-only owner.
- Re-ran seed 1, n 300, jobs 2 before/after; all 2,700 inputs and 5,400 Mac results excluding comparison verdict/diff are unchanged, as are all Smart oracle status/hash pairs.
- Migrated 594 corpus records with their previous results retained; final replay is 623/623 including the 29 unchanged Smoother v1 records.
- Promoted bounded OLMBlur Smart non-Legacy integer single-pass/singleton rules: 13 new exact seed-1 cases and 18 fresh seed-2 cases, zero newly admitted mismatches.
- Production validation: 1,200 sanitized campaign routes, 592 exact matrix cases, 18 expected refusals, and 12 retained fixture/lifecycle controls; no sanitizer errors. Existing residuals remain recorded.

facts:

Base: `53715716482c3278e9af0771fad16e30db7261d0`, branch `orch/F17-fuzz-per-route-oracle`. Read AGENT_GUIDE, GOTCHAS, the plan classification table, OLMBlur ledger row, F15/F10/F12 and T04/T07/T08/T09 evidence. MAIN and emulator source were read-only. No release gate, forbidden-action list, other plugin production source, installation, push, or history rewrite was changed. No `/tmp` scratch was used. Regenerable build/corpus directories were removed; remaining scratch logs/reports total 49,180,272 bytes (below 5 GiB).

**Framework contract and original route audit.** `evaluate()` obtains independent references keyed by candidate route, including separate rejection/budget/hash results. Public transport checks the returned `classic`/`smartfx` path. A failing Classic reference cannot borrow Smart pixels. `result.oracles` is authoritative; the old `oracle` member remains a primary-reference compatibility field for historical diagnostic consumers. Smoother v1 explicitly maps both Mac wrappers to its sole original Classic owner, and retains the old single-reference serialization so its unchanged corpus stays replayable. KiraKira diagnostic adapter overrides now retain separate reference files per route; OLMBlur manual triage comparisons also use matching routes.

| Plugin | Original Classic command | Original Smart command | Classic zero destinations in seed 1 |
|---|---|---|---:|
| ColorKeep | Available; 300 successful sessions | Available | 3 |
| OLMBlur | Available; 207 success / 93 reject | Available; 300 success | 0 |
| OLMColorKey | Available; 300 success; numerical ownership untraced | Available | 300 |
| OLMDirectionalBlur | Available; 300 success; numerical ownership untraced | Available | 300 |
| OLMDistanceGradation | Available; 300 success | Available | 14 |
| OLMKiraKira | Available; 300 success; numerical ownership untraced | Available | 300 |
| OLMSmoother2 | Documented no-write command; 300 success | Available | 300 |
| OLMToonDilate | Documented no-write command; 300 success | Available | 300 |
| OLMRadialBlur | Available; 300 success; numerical ownership untraced | Available | 300 |
| OLMSmoother v1 | Sole advertised owner; 91 success / 209 reject | Not advertised | Not audited |

For the two already proven no-write commands, AEX's initially zero destination must remain zero. Successful Mac output must retain its own initially `0xee` destination; this is `no_write`, separate from numerical `exact`. A changed Mac destination is `no_write_violation` and is retained/reduced as a failure. Smoother2's production Classic still refuses. This checks final destination preservation, not intermediate store execution or native AE buffer semantics. All-zero destinations in the four other rows are observations, **not** a newly proven no-write contract; their recorded mismatches must not automatically be called numerical kernel defects.

**Measured route correction, before OLMBlur promotion.** Counts are E/M/R/U/N = exact / mismatch / refusal / uncompared / no-write, each out of 300. Smart is unchanged before→after in every row. Historical T04 counts are not substituted for freshly measured current-source counts.

| Plugin | Classic before → paired | Smart before = paired |
|---|---|---|
| colorkeep | 205/0/95/0/0 → 74/131/95/0/0 | 205/0/95/0/0 |
| olmblur | 0/13/287/0/0 → 13/0/287/0/0 | 76/26/198/0/0 |
| olmcolorkey | 255/3/41/1/0 → 0/259/41/0/0 | 255/3/41/1/0 |
| olmdirectionalblur | 235/23/40/2/0 → 3/257/40/0/0 | 235/23/40/2/0 |
| olmdistancegradation | 158/132/0/10/0 → 10/290/0/0/0 | 177/65/51/7/0 |
| olmkirakira | 48/0/252/0/0 → 0/48/252/0/0 | 48/0/252/0/0 |
| olmsmoother2 | 0/0/300/0/0 → 0/0/300/0/0 | 292/8/0/0/0 |
| olmtoondilate | 0/300/0/0/0 → 0/0/0/0/300 | 277/23/0/0/0 |
| radialblur | 78/0/221/1/0 → 0/79/221/0/0 | 107/0/192/1/0 |
| olmsmoother (unchanged pairing) | 62/29/95/114/0 → unchanged | 62/29/95/114/0 |

Smart AEX ok/reject/budget: ColorKeep 300/0/0; Blur 300/0/0; ColorKey 299/1/0; DirectionalBlur 298/0/2; DistanceGradation 290/8/2; KiraKira 287/13/0; Smoother2 300/0/0; ToonDilate 300/0/0; RadialBlur 275/20/5. Rejections and time budgets are not pixel residuals. All same-worker before/after Smart status/hash pairs agree, including these failures. No source output changed to obtain the new Classic counts.

The general cached worker is `/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker`, SHA256 `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2`. RadialBlur uses the indexed `radial_offset_bound_reference_20261002/target/release/aex-guest-worker` alias, resolving to the offset worker, SHA256 `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`, for **both** sides. The initial frozen-worker RadialBlur attempt failed calibration 0/6 with unsupported `log2f`; it was not counted as a campaign and no worker was rebuilt. The first two legacy campaigns ran the unmodified runner; subsequent ones used `legacy_campaign_F17.py`, loading the fixed base comparator without checking out source. The final `--blur-before` wrapper was also smoke-tested (n 1, complete).

`reports/fuzz/per_route_oracles_F17.json` contains full before/after provenance, report hashes, transition counts, first mismatch inputs/parameters/diffs, and migrated corpus results. Representative first paired mismatches (byte offsets, little-endian word hex):

| Plugin / route | Seed-1 index | First byte | AEX → Mac |
|---|---:|---:|---|
| ColorKeep Classic | 0 | 8 | `00` → `ff` |
| Blur Smart | 4 | 1 | `81` → `80` |
| ColorKey Classic | 0 | 1 | `00` → `93` |
| DirectionalBlur Classic | 0 | 0 | `00` → `a9` |
| DistanceGradation Classic | 0 | 0 | `00` → `b4` |
| KiraKira Classic | 2 | 2 | `00000000` → `0000803f` |
| Smoother2 Smart | 17 | 419 | `0000c0ff` → `0000c07f` |
| ToonDilate Smart | 15 | 128 | `0000803f` → `dabfd93f` |
| RadialBlur Classic | 0 | 4 | `00` → `1a` |

**Corpus rebaseline.** Only the eight nonempty corpora whose pairing changed were updated. ColorKeep has no corpus cases; Smoother v1's 29 records and KiraKira's separate historical gate-off corpus were untouched. The explicit migration option requires identical candidate hashes and metadata, rejects changed Smart verdicts and transient/invalid oracles, validates the entire replay before writing, and retains `route_oracle_update.previous_result`. Inputs, reductions and operations are unchanged. A mistakenly requested replay of empty ColorKeep was a setup error, not a passing replay; the tool now rejects incomplete/empty migration reports.

| Corpus | Records | Classic saved → paired | Smart result changes |
|---|---:|---|---:|
| Blur | 39 | 13 mismatch → exact; 26 refusal unchanged | 0 |
| DistanceGradation | 145 | 139 exact / 6 mismatch → 100 exact / 45 mismatch | 0 |
| ToonDilate | 300 | 300 mismatch → no_write | 0 |
| Smoother2 | 8 | 8 refusal unchanged | 0 |
| DirectionalBlur | 56 | 37 exact / 19 mismatch → 18 exact / 38 mismatch | 0 |
| ColorKey | 3 | 3 mismatch unchanged (reference/diff updated) | 0 |
| KiraKira | 8 | 3 exact → mismatch; 5 refusal unchanged | 0 |
| RadialBlur | 35 | 23 exact / 1 mismatch / 11 refusal → 24 mismatch / 11 refusal | 0 |

Fresh final replay: all 594 migrated records plus 29 unchanged v1 records match saved results, exit 0. Blur promotion changes none of its 39 saved results; those records still replay 39/39.

**OLMBlur Smart promotion.** The additional small-frame rule is PF8 or PF16, Legacy off, with either Repeat 1 or width=height=1. Existing Amount [1,1000], Smoothness [1,100], Repeat [1,10], Bias 1/2, geometry, layout, work budget, full-frame/downsample, format, staging and callback guards remain. All normal numerical workers execute. The established exact fixture path takes precedence when its complete source/world admission matches, preserving its padding-copy and optional-callback contract. PF32, Legacy, and repeated multi-pixel small frames remain outside this new rule; existing separate fixture admissions remain.

Static facts: original `decomp/OLMBlur.aex.c.txt` lines 1033–1047 and 1622–1636 guard the non-Legacy `powf` decay construction with Repeat > 1; the initial pass uses iteration zero. The current PF8/PF16 worker code implements the same single-pass split. The helper bounds exclude neighboring samples on a singleton. This supports the selected branch/domain; the public comparisons below, not static interpretation alone, are the promotion evidence.

| Seed / production | Classic E/M/R | Smart E/M/R | Newly admitted exact |
|---|---|---|---:|
| 1 before | 13/0/287 | 76/26/198 | — |
| 1 final | 13/0/287 | 89/26/185 | 13 |
| 2 before | 24/0/276 | 63/32/205 | — |
| 2 final | 24/0/276 | 81/32/187 | 18 |

Fresh seed 2 was run before production admission. Gate-off ASan/UBSan runs across all 300 inputs: seed 1 Smart 224 exact / 74 mismatch / 2 sanitizer aborts; seed 2 Smart 221 exact / 79 mismatch. The two seed-1 errors are the retained PF8 Legacy NaN/inf→byte witnesses at indices 77 and 112. Both stay refused in production. Broad removal was already refuted by T09 and is not promoted.

For the **new rule**, every admitted seed-1/2 output equals both the matching AEX Smart output and the sanitized gate-off output. Zero newly admitted mismatches; all earlier successful outputs and Classic results are unchanged. Final ordinary and ASan/UBSan production result dictionaries agree for all 1,200 route executions, with zero sanitizer errors. Existing Smart 26/32 mismatches are retained, not claimed fixed.

The independent matrix is generated by `verify_blur_small_F17.py`: 592 exact gate-off cases and the same 592 exact production cases, plus 18 production refusals. It covers PF8/PF16, singletons/rows/columns/7×5/24×24, Amount 1/5/29.999984741210938/1000, Smoothness 1/100, both Bias values, opaque/mixed alpha, integer endpoints/random channels, extended uint16 through 65535, odd padding, and singleton Repeat 2/10. Negative cases cover neighboring PF32, Legacy and repeated multi-pixel small families. All execute with ASan/UBSan and abort-on-error. Leak checking is disabled and not claimed.

`verify_blur_retained_F17.py` preserves the original positive-control host and its actual-AEX fixture files: six 24×24 depth×Legacy cells with optional pixel checkin present/absent, **12/12 pass**, including active bytes, source/header/guard preservation, padding-copy behavior and callback counts. The fixture manifest, host, source and compiled candidate hashes are retained. Final production source SHA256 is `8512f063e79975dc2f20ab1349df71a05a0a397015f3150280fbbeb46b893241`; original Blur AEX SHA256 is `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`. Full promotion evidence is `reports/fuzz/olmblur_admission_F17.json`.

Unit/regression command: 26 tests discovered, 24 passed and two optional integration tests skipped; the updated real KiraKira three-depth transport anchor was then run separately and passed. Seven of the unit tests are the existing Blur Classic/generic tests (stale generic-source anchors updated). Route tests cover distinct references, no cross-route borrowing after rejection, no-write preservation/violation, invalid no-write reference, single-owner compatibility and atomic migration rejection. `git diff --check` passes.

inference:
- The route correction removes false residuals and exposes others. A Classic zero-filled result alone does not establish a numeric algorithm or a no-write stub. The four untraced all-zero Classic families require owner/dispatch investigation before changing production algorithms.
- The measured single-pass and singleton branch coverage supports this bounded Smart admission. It is finite CPU-AEX/fake-host evidence, not all-input equivalence, native Windows UCRT, native Mac/Windows AE, GPU, ROI or arbitrary lifecycle certification.
- This ticket does not assert that all admitted Blur output is exact: the pre-existing 26/32 Smart residuals remain. Only the additional rule has zero measured admitted mismatches.

changed_files:
- `mac/OLMBlur/OLMBlur.cpp` — bounded Smart admission, exact-fixture precedence; numerical core unchanged.
- `tools/fuzz/core.py`, `run.py`, `adapters/public.py`, `adapters/radialblur.py`, `adapters/olmsmoother.py`, `adapters/olmsmoother2.py`, `adapters/olmtoondilate.py` — per-route references, explicit exceptions and counters.
- `tools/fuzz/rebaseline_corpus.py`, `test_route_oracles.py`, `test_adapters.py`, `README.md` — audited migration, regressions and current route documentation.
- `tools/fuzz/triage_olmblur.py`, `triage_kirakira.py`, `probe_kirakira_tiny_owner_F04.py` — route-aware direct comparison/adapter overrides.
- `tools/fuzz/legacy_campaign_F17.py`, `summarize_routes_F17.py`, `blur_admission_campaign_F17.py`, `verify_blur_small_F17.py`, `verify_blur_retained_F17.py`, `summarize_blur_admission_F17.py` — reproducible measurement/verification scripts.
- `tests/test_olmblur_generic_beta_lane_20260820.py`.
- 594 JSON records under the eight `tests/fuzz_corpus/` directories in the corpus table; prior results retained.
- `reports/fuzz/per_route_oracles_F17.json`, `reports/fuzz/olmblur_admission_F17.json`.
- `orchestra/reports/F17-fuzz-per-route-oracle.md`.

verify:

Run from this worktree. These commands reproduce the measurement stages without modifying MAIN, production source, or corpus expectations. Logs and generated corpora stay in ticket scratch. The first-stage Blur snapshots use the fixed pre-promotion revision so route correction and admission remain separately reviewable. The route migration itself was performed using `rebaseline_corpus.py --route-correction --plugin NAME --corpus tests/fuzz_corpus/NAME --report "$s/replay-NAME.json"`; it need not be repeated on the committed corpus.

```sh
s="$PWD/orchestra/state/F17-fuzz-per-route-oracle"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
w=/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker
rw=/Users/onmk/.cache/olm-emu/radial_offset_bound_reference_20261002/target/release/aex-guest-worker
base=53715716482c3278e9af0771fad16e30db7261d0
for p in olmblur olmdistancegradation olmtoondilate olmsmoother2 olmdirectionalblur olmcolorkey colorkeep olmkirakira radialblur olmsmoother; do
  worker="$w"; [ "$p" != radialblur ] || worker="$rw"
  extra=(); [ "$p" != olmblur ] || extra=(--blur-before)
  python3 tools/fuzz/legacy_campaign_F17.py "${extra[@]}" --plugin "$p" --seed 1 --n 300 --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --worker "$worker" --scratch "$s" --report "$s/before-$p.json" --corpus "$s/before-$p-corpus" > "$s/before-$p.log" 2>&1
  [ "$p" != olmsmoother ] || continue
  script=tools/fuzz/run.py; extra=(); suffix=""
  if [ "$p" = olmblur ]; then script=tools/fuzz/blur_admission_campaign_F17.py; extra=(--blur-source-revision "$base"); fi
  [ "$p" != radialblur ] || suffix=-offset
  python3 "$script" "${extra[@]}" --plugin "$p" --seed 1 --n 300 --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --worker "$worker" --scratch "$s" --report "$s/paired-$p$suffix.json" --corpus "$s/paired-$p-corpus" > "$s/paired-$p$suffix.log" 2>&1
done
python3 tools/fuzz/summarize_routes_F17.py --scratch "$s" --report "$s/verify-routes.json" > "$s/verify-routes.log" 2>&1

python3 tools/fuzz/blur_admission_campaign_F17.py --blur-source-revision "$base" --plugin olmblur --seed 2 --n 300 --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --worker "$w" --scratch "$s" --report "$s/blur-before-seed2.json" --corpus "$s/blur-before-seed2-corpus" > "$s/blur-before-seed2.log" 2>&1
for seed in 1 2; do
  python3 tools/fuzz/blur_admission_campaign_F17.py --blur-source-revision "$base" --blur-small-off --blur-sanitize --plugin olmblur --seed "$seed" --n 300 --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --worker "$w" --scratch "$s" --report "$s/blur-gateoff-seed$seed.json" --corpus "$s/blur-gateoff-seed$seed-corpus" > "$s/blur-gateoff-seed$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmblur --seed "$seed" --n 300 --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --worker "$w" --scratch "$s" --report "$s/blur-after-seed$seed.json" --corpus "$s/blur-after-seed$seed-corpus" > "$s/blur-after-seed$seed.log" 2>&1
  python3 tools/fuzz/blur_admission_campaign_F17.py --blur-sanitize --plugin olmblur --seed "$seed" --n 300 --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --worker "$w" --scratch "$s" --report "$s/blur-sanitized-seed$seed.json" --corpus "$s/blur-sanitized-seed$seed-corpus" > "$s/blur-sanitized-seed$seed.log" 2>&1
done
python3 tools/fuzz/verify_blur_small_F17.py --diagnostic --scratch "$s/matrix" --report "$s/blur-matrix-gateoff.json" > "$s/blur-matrix-gateoff.log" 2>&1
python3 tools/fuzz/verify_blur_small_F17.py --scratch "$s/matrix" --report "$s/blur-matrix-production.json" > "$s/blur-matrix-production.log" 2>&1
python3 tools/fuzz/verify_blur_retained_F17.py --scratch "$s/retained" --report "$s/blur-retained.json" > "$s/blur-retained.log" 2>&1
for p in olmblur olmdistancegradation olmtoondilate olmsmoother2 olmdirectionalblur olmcolorkey olmkirakira radialblur olmsmoother; do
  worker="$w"; [ "$p" != radialblur ] || worker="$rw"
  report="$s/verify-$p.json"; [ "$p" != olmblur ] || report="$s/blur-final-replay.json"
  python3 tools/fuzz/run.py --plugin "$p" --jobs 2 --replay "tests/fuzz_corpus/$p" --worker "$worker" --scratch "$s" --report "$report" --corpus "$s/replay-corpus" > "$s/verify-$p.log" 2>&1
done
python3 tools/fuzz/summarize_blur_admission_F17.py --scratch "$s" --report "$s/verify-admission.json" > "$s/verify-admission.log" 2>&1
python3 tools/fuzz/test_route_oracles.py > "$s/route-unit.log" 2>&1
PYTHONPATH=tests python3 -m unittest test_olmblur_generic_classic_beta_20260822 test_olmblur_generic_beta_lane_20260820 > "$s/blur-tests.log" 2>&1
git diff --check
```

Expected: tables above; route summarizer asserts 300 unchanged inputs/600 unchanged candidate observations per changed plugin and no Smart oracle status/hash changes in the recorded run; promotion summarizer prints `PASS` with seed 1:13 / seed 2:18 new exact, 1,200 sanitized route executions, 592 exact matrix cases, 18 refusals, 12 retained controls, corpus 39/39. All corpus replay commands exit 0 (623 total). Route unit tests 6/6 and Blur tests 7/7 pass. Wall-time budgets can vary with machine load; explicit budget/rejection rows remain separate from numerical verdicts. Build/report hashes with temporary paths/timestamps can vary; compare behavior and bound source/AEX/worker identities.

next:
- Investigate original Classic dispatch/write semantics for ColorKey, DirectionalBlur, KiraKira and RadialBlur before interpreting their 300 zero destinations as numerical owners. Keep these separate from their unchanged Smart residuals.
- Separate numerical tickets can address the remaining Blur Smart 26 seed-1 / 32 seed-2 residuals, PF8 Legacy NaN/inf conversion, repeated multi-pixel small frames, and PF32/Legacy admission. This promotion supplies no blanket widening evidence for them.
- Native AE/UCRT/ROI/downsample and broader lifecycle proof remain separate from this CPU emulation/fake-host ticket.
