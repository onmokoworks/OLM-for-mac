status: blocked

summary:
- Added paired original-AEX/Mac source, seed, ray, aggregation and pre-writer traces; all nine target traces bind exactly to the retained public AEX worker's final bytes.
- Fixed PF16 aggregation normalization in general code; C28 now matches every traced stage and all 14,040 final bytes.
- Diagnostic fuzz improves Classic 184→198 exact and Smart 85→98 exact; production remains 0 exact / 300 refused on each route.
- Eleven shrunk corpus cases become exact on both routes; 58 changed Classic samples all move to exact. No corpus expectations or admission guards changed.
- Eight other target cases remain mismatches. Their first divergent boundaries are recorded below; full ticket acceptance is not met.

facts:

Base `263aeb424dd04dd2fe39d208aa499828662bb20d`, branch `orch/F09-kira-numeric-first-divergence`.
Read the shared guide, emulator gotchas, compatibility plan, KiraKira ledger restrictions, T06/F03/F04 reports and worker INDEX. MAIN, external emulator source/workers, release gates, ledger and other plugins were not modified. No worker rebuild, native AE install, push or merge.

Machine evidence: `reports/fuzz/olmkirakira_numeric_F09.json`. Its before/after tables retain source/worker identities, complete changed campaign records, every saved/fresh corpus record, stage hashes and first differing words. The reproduction scripts regenerate the observations from committed corpus inputs.

- AEX SHA256: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`, read from MAIN `plugins_2025/OLMKiraKira.aex`.
- Public worker: `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`, SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. INDEX contains RadialBlur workers; this is the retained KiraKira worker used by T06/F03/F04.
- Mac source before: `99c68ea7028cc9b11311476fd0d9f50e11086f0f7591b09cf53fe89bf50297a3`; after: `c3cb49527eaef8f51031487db57d5af56eee5933aa3583f02dd7b9865cd5eaf6`.

Trace transport:

1. The Python Unicorn scaffold runs the original source reader, channel constructor, full caller `18114f4a0`, embedded warp/filter/aggregation functions, and original typed outer writer. A known-answer import-free PF8 reader call checks the fifth Win64 stack argument before tracing. Original CRT initializers run through the existing scaffold; Windows allocation/TLS/handle callbacks and Python libm imports remain host substitutions. No AEX numerical body is detoured.
2. Hooks read the source, seed Mat, helper input/output Mats, all five rays, normalized glow, and XMM pre-writer words. Directional workspace sine/cosine values and Mat shapes are captured separately. Mac observations come from a scratch translation unit using the existing public Classic host, with only final tuple admission bypassed. Production arithmetic is otherwise compiled with the adapter's arm64 `-O2 -fno-fast-math -ffp-contract=off` settings.
3. Each full-caller trace is independently compared with the original resident public Smart worker for the identical committed typed input and parameters. **9/9 final outputs match before and 9/9 after.** The script fails if this binding does not hold. These are CPU/fake-host results, not native Windows UCRT/AE, GPU, ROI or downsample proofs.
4. Early scaffold execution passed individual pixel addresses to the outer writer and faulted; the existing full-caller harness showed that it requires a world. Correcting that ABI produced the public-output binding above. No numerical claim uses the faulted runs.

First divergent boundaries (hex words below are little-endian bytes):

| Cluster / index | Measured first boundary | Result after PF16 change |
|---|---|---|
| C60 / 148, PF16 9×1 | Vertical padded workspace: AEX 13×12, Mac 13×13; 624 versus 676 bytes before forward warp | Still mismatch |
| C61 / 116, PF32 3×3 | Seed word 8: AEX `462381ff`, Mac `4623c1ff` (signaling versus quiet NaN payload) | Still mismatch |
| C62 / 78, PF8 1×9 | Vertical padded workspace: AEX 12×13, Mac 13×13; 624 versus 676 bytes before forward warp | Still mismatch |
| C23 / 157, PF16 1×1 | AEX seed has four float channels, Mac one; first word `bb8bcc3d` versus `0ebc813e` | Still mismatch |
| C24 / 19, PF8 1×1 | AEX seed has four channels, Mac one; first missing Mac word is AEX `2d45433f` | Still mismatch |
| C30 / 210, PF16 1×1 | First ray word `e338763e` versus `0038763f` | Still mismatch |
| C31 / 23, PF32 1×1 | First ray word `7500803e` versus `0000803f` | Still mismatch |
| C32 / 232, PF8 1×1 | First ray word `7500803e` versus `0000803f` | Still mismatch |
| C28 / 3, PF16 39×45 | Source, seed, both active rays and all zero rays exact. First glow difference word 20: `c14ea03f` versus `c04ea03f`; 1,203 differing glow words | All paired stages and final bytes exact |

Additional static/runtime facts:

- The original workspace owner converts angle×radians-per-degree from double to float before calling embedded `18132b2e0`, then uses separate `MULSS`/`ADDSS` operations at `18114f7bd..18114f7e4`. At 90°, captured radians are `db0fc93f`; sine/cosine are `ffff7f3f` / `2ebdbbb3` (0.9999999403953552 / -8.742277657347586e-08). The port instead computes double trigonometry/extents. No canonical-angle override or fitted constant was added.
- Channel 3/6 selects the original color constructor `18114eed0`; its seed builder `18114ef10` allocates four channels and powers RGB with exponent+1, multiplying by alpha. The port's scalar max-of-powers branch does not implement this representation. The shape difference is observed, not an assumed blur issue.
- The Mode-3 shrunk cases reach a 5×5 helper workspace. `mode3_gaussian_admitted` rejects it, and `RotatedAxisBoxBlur` returns the unblurred input. The AEX executes its Gaussian path and produces the ray words above. The admission predicate was not relaxed.
- Original aggregation `18114fd90` is shared by typed owners. Instructions `18114ff33..18114ff54` perform one `DIVSS` reciprocal and three `MULSS` operations. The port previously used this only for PF32. The committed change extends it to PF16, preserving PF8's prior behavior.

C28's final mismatch before the fix was byte 6,998, pixel (16,22), blue: AEX `125a`, Mac `115a`. Before Mac SHA256 `911bbe5662b0f0dda25483e577665a3998fa815d0d86508345dcddd80bf91689`. After Mac and AEX both hash to `d5e90cfe01d82d4de4c3d224086165c921855f6ecb157de5df45b2c51deec0bb`. All 7,020 glow words and all pre-writer words now match, not just the final differing byte.

Rejected experiment: extending reciprocal normalization to PF8 as well yielded diagnostic counts 203 Classic / 100 Smart exact. However shrunk index 77 changed 17 samples: 16 moved to exact and sample 167 moved away from exact (total differing bytes 21→6). The strict sample audit rejected it. That all-depth candidate was narrowed; the final PF16-only code leaves this PF8 output unchanged. This is an unresolved PF8 dependency between arithmetic stages, not evidence for a per-case correction. The rejection log is retained in machine evidence.

Campaign results, `n=300 --seed 1 --jobs 2` (E/M/R/U = exact/mismatch/refusal/uncompared):

| Campaign | Classic E/M/R/U | Smart E/M/R/U |
|---|---|---|
| Fresh production before | 0/0/300/0 | 0/0/300/0 |
| Fresh production after | 0/0/300/0 | 0/0/300/0 |
| All gates off before, ordinary build | 184/103/0/13 | 85/52/163/0 |
| All gates off after, ASan/UBSan | 198/89/0/13 | 98/39/163/0 |

Every campaign has 287 successful AEX outputs / 13 AEX rejections. No previously exact route regresses. All 300 complete production records are unchanged. The final diagnostic run has zero sanitizer aborts/errors. In the unshrunk diagnostic campaign, indices 115/210/260/268 retain mismatches with changed output; no broader claim of per-sample monotonicity is made for those unshrunk inputs.

Corpus replay before/after (expectations remain unchanged):

| Shrunk index | Classic | Smart | Changed Classic typed samples |
|---|---|---|---:|
| 3 | mismatch → exact | mismatch → exact | 1 |
| 13 | mismatch → exact | mismatch → exact | 1 |
| 29 | mismatch → exact | mismatch → exact | 1 |
| 97 | mismatch → exact | mismatch → exact | 7 |
| 115 | mismatch → exact | mismatch → exact | 30 |
| 122 | mismatch → exact | mismatch → exact | 1 |
| 191 | mismatch → exact | mismatch → exact | 1 |
| 230 | mismatch → exact | mismatch → exact | 1 |
| 252 | mismatch → exact | mismatch → exact | 1 |
| 260 | mismatch → exact | mismatch → exact | 13 |
| 268 | mismatch → exact | mismatch → exact | 1 |
| Other 51 shrunk cases | unchanged | unchanged | 0 |

The separate before/after sample audit rebuilt both revisions and replayed 62 shrunk Classic cases plus both routes of all eight production cases: **78 route replays; all 58 changed samples now equal AEX; zero changes away from exact**. Sanitized shrunk Classic/Smart replay independently confirms the table. Strict saved-result replay exits 1 with 51/62 matches because 11 expected mismatches are now exact; no expectation was silently updated.

Production corpus retains the inherited F03 metadata drift: 6/8 complete saved results match; indices 2 and 3 remain refusals on both routes but Smart COUNTS are `1 1 1 25 25` / `1 1 1 26 26` instead of saved `1 1 1 0 0`. The new source change makes **no** difference between fresh before/after production corpus results. Strict replay still exits 1. This worker did not reconcile those saved records.

Fast existing tests: **25 passed**, namely generic-beta lane (9), merge2 float oracle (6), outer compose oracle (9), bounded typed-writer ownership assertion (1). `git diff --check` passes.

inference:

- PF16's separate divisions were a port operation-order error. Exact matching through the rays, the original assembly, and exact aggregation/compose/output after the correction support the fix independently of final-byte similarity.
- C60/C62 require recovery of the embedded float sine/cosine and extent arithmetic. Replacing only workspace sizes at observed angles would be a case-specific patch and was not attempted.
- C61's first bit difference is NaN handling; it is not yet proven to explain every downstream mismatch. C23/C24 need a color-plane pipeline, and C30–C32 need separately validated tiny Gaussian admission. None is proven outside the port.
- The paired transport fulfills the ticket's permitted KIRA-F08 evidence deliverable. Overall status is blocked because eight named target cases remain unresolved, production still refuses the sampled cases, and historical production corpus metadata remains unreconciled. There were no two refuted numerical hypotheses without new boundary data; the all-depth candidate rejection itself supplied sample 167 as a new boundary.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `tools/emulation/audit_kirakira_numeric_corpus_F09.py`
- `tools/emulation/summarize_kirakira_numeric_F09.py`
- `reports/fuzz/olmkirakira_numeric_F09.json`
- `orchestra/reports/F09-kira-numeric-first-divergence.md`

verify:

Run from this worktree. All writes stay in ticket scratch. Commands below are the measured commands; the alternate source argument also makes the before trace and corpus audit reproducible without changing the checkout.

```sh
s="$PWD/orchestra/state/F09-kira-numeric-first-divergence"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 263aeb424dd04dd2fe39d208aa499828662bb20d:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"

"$py" tools/emulation/trace_kirakira_numeric_F09.py --source "$s/before.cpp" --scratch "$s/before-trace" --report "$s/before-trace.json" > "$s/before-trace.log" 2>&1
"$py" tools/emulation/trace_kirakira_numeric_F09.py --scratch "$s/after-trace" --report "$s/after-trace.json" > "$s/after-trace.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --before-source "$s/before.cpp" --scratch "$s/corpus-audit" --report "$s/corpus-audit.json" > "$s/corpus-audit.log" 2>&1

python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 2 --scratch "$s" --report "$s/after-production.json" --corpus "$s/after-corpus" > "$s/after-production.log" 2>&1
python3 tools/fuzz/triage_kirakira.py --experiment all --sanitizers --plugin olmkirakira --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/after-gateoff.json" --corpus "$s/after-gateoff-corpus" > "$s/after-gateoff.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/replay-production.json" --corpus "$s/replay-corpus" > "$s/replay-production.log" 2>&1
# Expected exit 1 above (inherited metadata); continue explicitly.
python3 tools/fuzz/triage_kirakira.py --experiment all --sanitizers --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira_gate_off_T06 --scratch "$s" --report "$s/replay-gateoff.json" --corpus "$s/replay-gateoff-corpus" > "$s/replay-gateoff.log" 2>&1
# Expected exit 1 above (11 improvements); continue explicitly.
PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820 test_olmkirakira_merge2_float_oracle_20260728 test_olmkirakira_outer_compose_oracle_20260728 test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.Mode4FullCallerHostlessExactTests.test_mac_production_owns_the_bounded_highlight_and_typed_writer > "$s/fast-tests.log" 2>&1
git diff --check
```

Expected: 9 bound traces per revision, C28 first divergence `glow`→`None`; 78 audited routes / 58 samples toward exact; production 0 exact / 300 refusals each; diagnostic 198/89/0/13 Classic and 98/39/163/0 Smart; strict replays 6/8 and 51/62; 25 tests pass.

The before campaigns were the corresponding commands with `before-*` paths run before editing the source (without sanitizers for the diagnostic baseline). The evidence summarizer consumes those original scratch reports plus the commands above:

```sh
python3 tools/emulation/summarize_kirakira_numeric_F09.py --scratch "$s" --report reports/fuzz/olmkirakira_numeric_F09.json
```

To reproduce the rejected all-depth experiment's decisive corpus check without editing production, generate a scratch source from current code replacing `if (bitdepth != 8)` with `if (true)`, then pass it as `--after-source` to the audit script. Expected: exit 1 at shrunk index 77, `changed_samples=17`, `changed_not_to_exact=[167]`. This is an experiment only, not an accepted fix.

next:
- Recover embedded `18132b2e0` float sine/cosine plus the float32 extent operation order; replay C60/C62 and independent angles/geometries before changing general geometry.
- Trace C61 NaN seed/warp propagation with word-preserving values; do not equate a quiet-bit difference with the cause of all final differences.
- Implement and validate the original four-channel color seed/ray/aggregation path for C23/C24.
- Validate tiny Mode-3 Gaussian execution with gate-off exact output and sanitizers before relaxing its helper admission.
- Keep PF8 normalization unchanged until its upstream differences are reconciled; retain index 77/sample 167 as a regression witness.
- Orchestrator may review the bounded PF16 fix and trace transport independently. Corpus expectation changes, the two historical refusal metadata records, native AE and broader parameter/geometry coverage remain separate work.
