status: blocked

summary:
- Seeds 1–4, n300 each: 1,175 Smart exact / 0 mismatch / 0 port refusal / 25 uncompared.
- Every uncompared case is the cached reference worker rejecting unsupported `atan2f`, not an AEX-rendered mismatch.
- The ticket's seed-1 premise is corrected: F20 and this run both have 299 exact / 0 mismatch / 1 oracle rejection.
- No production change is justified by these measurements; no numerical cluster was closed.
- Worker rebuilding is outside the authorized scope; a ColorKey-capable reference worker is needed to compare the remaining cases.

facts:

Base: `0e3481cbba7c9b63e3c23480d8abb081fe03733f`, branch `orch/C20-colorkey-smart`.
Read the shared guide, GOTCHAS, ColorKey's ledger decision/forbidden-action row, compatibility plan, T12/F20 triage and fix evidence, and F18/F23/F24 route/replay context. MAIN, original AEX, SDK, emulator source, release gates, forbidden-action lists, and production source were not modified. No worker rebuilt or subagent started.

Commands executed from this worktree, with ticket scratch as TMPDIR/TMP/TEMP and `PYTHONDONTWRITEBYTECODE=1` (the first optimized campaigns set TMPDIR):

```sh
s="$PWD/orchestra/state/C20-colorkey-smart"
w=/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker
# Each seed 1, 2, 3, 4, sequentially:
python3 tools/fuzz/run.py --plugin olmcolorkey --n 300 --seed "$seed" --jobs 1 \
  --shrink-attempts 0 --worker "$w" --scratch "$s/seed$seed" \
  --report "$s/seed$seed.json" --corpus "$s/corpus$seed" > "$s/seed$seed.log" 2>&1
# Repeat each seed with OLM_COLOR_TRIAGE_SANITIZE=1,
# ASAN_OPTIONS=detect_leaks=0, UBSAN_OPTIONS=halt_on_error=1,
# using sanitize$seed scratch/report/log and sanitize-corpus$seed.
python3 tools/fuzz/run.py --plugin olmcolorkey --replay tests/fuzz_corpus/olmcolorkey \
  --jobs 1 --scratch "$s/replay" --report "$s/replay.json" \
  --corpus "$s/replay-unused" > "$s/replay.log" 2>&1
python3 tools/fuzz/summarize_colorkey_C20.py --scratch "$s" \
  --output orchestra/reports/C20-colorkey-smart-evidence.json
bash -n tools/fuzz/verify_colorkey_C20.sh
git diff --check
```

`--jobs 1` follows the hard machine limit rather than the ticket loop's jobs-2 example. All campaigns completed 300 cases without exhausting their time budgets. No shrinking was attempted because there is no Smart mismatch/refusal to reduce. The runner also records forced Classic results; they are not counted as Smart residuals.

| Seed | Smart exact | Smart mismatch | Port refusal | Oracle reject/uncompared | Rejected indices (zero-based) |
|---|---:|---:|---:|---:|---|
| 1 | 299 | 0 | 0 | 1 | 96 |
| 2 | 293 | 0 | 0 | 7 | 15, 36, 105, 145, 166, 273, 299 |
| 3 | 292 | 0 | 0 | 8 | 10, 54, 71, 110, 180, 202, 224, 260 |
| 4 | 291 | 0 | 0 | 9 | 26, 37, 53, 149, 178, 179, 183, 269, 298 |

All 25 original Smart calls exit 1 with exactly:

```text
aex_guest_error: selector SMART_RENDER failed in guest: unsupported Win64 import: api-ms-win-crt-math-l1-1-0.dll!atan2f
```

Every rejected case has color-space slot 5 = 4 and per-component slot 8 = 0 (Lab94 scalar). First rejected case: seed 1/index 96, PF16, 104×1, input SHA256 `4153fafade3e2b2b24f3632cf74389590f25e70994fbe567a28682c715511988`. The Mac Smart call succeeds; its output hash equals that input hash. No original Smart output is available, so **first divergent numerical stage and first mismatching byte are unavailable**, not zero. No paired numerical trace or gate-off experiment is warranted for an oracle rejection.

Hash bindings:

- Original AEX: `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`.
- Cached worker: `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2`.
- Unmodified ColorKey source: `a7a177101066c8939a9716b079af22aed51430578856fe14b7474b544b2794ed`.

The committed evidence retains every generated input hash, Smart result/oracle dictionaries, rejection indices, classifier controls, reference/build/framework provenance, and full retained-corpus replay. Seed-1 Smart oracle and candidate dictionaries equal F20's final evidence **300/300**, including its rejection; all **299 previously exact outputs** are unchanged. Fresh seeds have no preexisting exact baseline beyond the measured unchanged source.

**Validation completed:** all eight generation commands, retained replay, summarizer, shell syntax check, and `git diff --check` exit 0. ASan+UBSan (`-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer`, halt-on-error UBSan) reports **zero diagnostics across 2,400 Mac route executions**, including all 1,200 Smart calls. All **1,200 complete comparison dictionaries** match the optimized campaigns, including forced-Classic diagnostics and reference rejections. Leak checking was disabled. Sanitizers cannot provide missing oracle output.

Retained corpus before/after (no files rebaselined):

| Case | Saved Smart | Replay Smart | Saved result match |
|---|---|---|---|
| seed1_case000020_32358eb88430 | exact | exact | yes |
| seed1_case000099_9b13c27c2f2e | exact | exact | yes |
| seed1_case000126_9b13c27c2f2e | exact | exact | yes |

All three complete saved results, including forced Classic diagnostics, remain unchanged. No newly admitted case or changed pixel output exists in this ticket. Disposable build/run/corpus directories were removed after measurement; reports and logs remain. All launched commands exited; no background process remains.

inference:

- The only observed Smart residual cluster is a reference capability limitation, consistent with F20/T12 and the existing ColorKey controlled-atan2f patch. The cache index lists radial reference variants, not a ColorKey controlled-atan2f worker. Building the existing recipe would violate the explicit no-rebuild constraint.
- There is no evidence here for changing the port. Treating unsupported-import cases as numerical mismatches would conflate missing oracle output with measured inequality.
- Three numerical cluster closures cannot be produced from this population: no AEX-rendered Smart mismatch or port refusal was observed. These measurements do not establish native Windows UCRT/AE equivalence or arbitrary-input coverage.

changed_files:

- `tools/fuzz/summarize_colorkey_C20.py`
- `tools/fuzz/verify_colorkey_C20.sh`
- `orchestra/reports/C20-colorkey-smart-evidence.json`
- `orchestra/reports/C20-colorkey-smart.md`

verify:

```sh
bash tools/fuzz/verify_colorkey_C20.sh
git diff --check
```

The verifier runs all eight campaigns and corpus replay sequentially with jobs 1, validates counts and complete sanitized-vs-optimized result equality, compares all seed-1 Smart results to F20, and writes fresh evidence beneath ticket scratch. Expected final summary:

```text
C20: 1175 Smart exact; 25 atan2f oracle rejects; 0 mismatch/refusal; 2400 sanitized route executions clean; F20 seed1 unchanged 300/300; corpus 3/3 unchanged
```

Its component commands were executed individually; the combined shell was syntax-checked. It deletes its disposable build/run/corpus directories after validation while retaining reports/logs. No production or historical corpus rebaseline is needed.

next:

- Suggested follow-up: authorize building/calibrating a ColorKey Lab94 reference with `atan2f` support, or supply an already hash-bound capable worker. Re-run the 25 retained seed/index inputs and the same 1,200-case census, keeping controlled host math separate from native Windows UCRT proof.
- Resume first-stage numerical tracing only if that reference produces a real Smart mismatch. Do not suppress the 25 rejects, claim 1,200 exact, or modify the port to bypass Lab94.
