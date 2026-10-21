status: done

summary:
- Added behavior-neutral `OLM_REFUSAL_TRACE` attribution to `mac/OLMBlur/OLMBlur.cpp` (36 tagged guard/error sites) and per-route capture to the fuzz adapter; every one of the 485 seed-1 refusals is now named.
- Reproduced the T04 baseline exactly: AEX 300/0/0; Classic 0/13/287; Smart 76/26/198; 13 shrunk clusters. Replay stays 39/39 `matches_saved`, and all 300×2 route results plus oracles are byte-identical to the pre-tracing report.
- Three gates account for all refusals: Smart `generic-small-fixture` 198, Classic `classic-nondefault-tuple` 192, Classic `classic-pf32-unowned` 95.
- Gate-off: removing `generic-small-fixture` yields **148 exact / 50 mismatch**; removing the Classic copy tuple yields **13 exact / 179 mismatch**; naive PF32 removal has **no fall-through** (95/95 still refuse via `classic-copy-geometry`).
- Classified the 13 clusters: 2 are confirmed Classic copy-path port bugs, 11 remain unexplained numerical residuals; no paired intermediate AEX/Mac stage exists, so only final-byte statistics are reported.

facts:

Branch `orch/T09-triage-olmblur`, base commit `97ed4fd0b38b3d2abf509346546eb5a99df306e1`. Read `AGENT_GUIDE.md`, the OLMBlur ledger row, `tools/emulation/GOTCHAS.md`, the plan's classification table, T03, T04, and T10 (T05 is absent in this worktree). No release gate, forbidden-action list, other plugin, MAIN, emulator source, or corpus file was changed. No push and no history rewrite. All fuzz runs used `--jobs 2`. Scratch stayed at 4.1 MiB under `orchestra/state/T09-triage-olmblur`.

**Provenance.**
| Item | SHA-256 |
|---|---|
| Production source `mac/OLMBlur/OLMBlur.cpp` | `cf362169e4ca3bd76d06fe59e31c4d07401964bbe5bf19189cd9d142c6da4cf3` |
| Tracing candidate binary | `942d049bbf91dfe262273a0334d598d6bd77b789bc892fda5e0951ad46cf68cb` |
| Oracle AEX `plugins_2025/OLMBlur.aex` | `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b` |
| Retained worker | `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261` |
| `reports/fuzz/olmblur_refusals_20261022.json` | `c5fbe462a75c5f8b9a6320472fc728e879f72a591ea6f333a5a86649075ae2cc` |
| `reports/fuzz/olmblur_trace_replay_20261022.json` | `2c0c6bdc07bb649cde64567d3a50fa380224e21a99f6df98cadd99bd97f279bc` |
| `reports/fuzz/olmblur_triage_20261022.json` | `761e74c940fc1fa99011f329b4320500bf4c7737dc6afede38b3de7ae9881463` |
| `tools/fuzz/triage_olmblur.py` | `93475162965987cdf992157bd1ea7c277e546a34dc5d1b4ca1c441cc3d20ae5f` |

**Instrumentation.** `BlurRefusal(function, tag, line, err)` appends `function:tag@line` to `$OLM_REFUSAL_TRACE` with `O_APPEND` and returns the original `PF_Err` unchanged. The file is opened only when the environment variable is set and only on a failing path. `OLM_BLUR_REFUSAL`/`OLM_BLUR_ERROR` cover Render, SmartPreRender, the generic-beta and exact SmartRender lanes, parameter/world/format checks, staging, commit and OOM returns. The adapter gives each route its own trace file inside the disposable case directory, unlinks it before the run, reads it after the route, and returns the guard list as a third tuple element outside the compared result. `PublicAdapter.candidate` gained an optional `env` argument so the trace path is per-call and thread-safe.

The reason-function refactor (`GenericBetaTupleRefusal`) keeps the original predicate order and error codes; the split SmartRender admissions are the same pure predicates. The one behavioural requirement observed in review is preserved: callback/checkin errors retain their original code, not `PF_Err_BAD_CALLBACK_PARAM`.

**Baseline reproduction and neutrality.**
```sh
python3 tools/fuzz/run.py --plugin olmblur --n 300 --seed 1 --jobs 2 --budget-minutes 30 \
  --shrink-attempts 0 --scratch orchestra/state/T09-triage-olmblur \
  --report reports/fuzz/olmblur_refusals_20261022.json \
  --corpus orchestra/state/T09-triage-olmblur/census_corpus2
python3 tools/fuzz/run.py --plugin olmblur --jobs 2 --replay tests/fuzz_corpus/olmblur \
  --scratch orchestra/state/T09-triage-olmblur \
  --report reports/fuzz/olmblur_trace_replay_20261022.json
OLM_FUZZ_INTEGRATION=1 python3 tools/fuzz/test_framework.py
```
Results: census `complete`, 300/300, 10.4 s, `{"aex_ok": 300, "both_routes_exact": 0, "classic_mismatch": 13, "classic_refusal": 287, "pixel_mismatch_cases": 39, "smart_exact": 76, "smart_mismatch": 26, "smart_refusal": 198}`. Replay `replay_complete`, 39/39 `matches_saved`. Integration 8 tests OK. Comparing the new census against the pre-tracing `reports/fuzz/olmblur_20261021.json` gives **0 result differences**: every oracle and both route results (status, error, raw SHA, diff) are identical for all 300 cases.

**Ranked refusal guards.** Counts are unique cases; all 300 inputs are legal declared-range samples and all 300 AEX runs completed. Every refusal event is attributed: Classic 287/287, Smart 198/198 (485/485, 100%).
| Rank | Guard / error | Route | Refused legal cases | AEX ok | Observed boundary |
|---|---|---|---:|---:|---|
| 1 | `SmartRender:generic-small-fixture` / 516 | Smart | 198 | 198 | `width <= 24 && height <= 24` exact-fixture exclusion; depths 8/16/32 = 60/72/66 |
| 2 | `Render:classic-nondefault-tuple` / 516 | Classic | 192 | 192 | `amount != 5.0` 153, `smoothness != 100.0` 137, `repeat != 2` 118; depths 8/16 = 88/104 |
| 3 | `Render:classic-pf32-unowned` / 516 | Classic | 95 | 95 | all depth 32; ARGB128 switch case refuses before the copy tuple |
| — | all remaining tagged guards | — | 0 | — | no other guard fired in this seed |

**Gate-off experiments.** `tools/fuzz/triage_olmblur.py` writes disposable source copies, removes one gate there, and rebuilds; production source is untouched. Sanitized builds use `-fsanitize=address,undefined -fno-sanitize-recover=all` with leak detection off. Counts are per attempt set.
| Disabled gate (scratch) | Route | Attempted | Unblocked | Exact | Mismatch | Refusal | Crash | Sanitizer | Result |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `generic-small-fixture` (O2) | Smart | 198 | 198 | 148 | 50 | 0 | 0 | 0 | 148 legal cases render exactly through the existing generic-beta lane |
| `generic-small-fixture` (ASan/UBSan) | Smart | 198 | 198 | 148 | 48 | 0 | 0 | **2** | UBSan: NaN/inf → `unsigned char`, `core/olmblur_worker8_legacy.cpp:114:52` |
| `classic-nondefault-tuple` (O2) | Classic | 192 | 192 | 13 | 179 | 0 | 0 | 0 | copy fallback is not the AEX operation |
| `classic-nondefault-tuple` (ASan/UBSan) | Classic | 192 | 192 | 13 | 179 | 0 | 0 | 0 | no sanitizer finding |
| `classic-pf32-unowned` naive removal | Classic | 95 | 0 | 0 | 0 | 95 | 0 | 0 | no fall-through: switch reaches `classic-copy-geometry` 95/95 |
| `classic-pf32` + tuple off (compound) | Classic | 95 | 95 | 9 | 86 | 0 | 0 | 0 | copy path reachable only with both gates off |

The two UBSan cases are index 77 (PF8, 18×18, `nan`) and index 112 (PF8, 4×9, `inf`); both were previously refused and are not production-reachable unless the small-fixture gate is widened.

Gate-off mismatch shape for `generic-small-fixture` (50 cases; 12 depth 8, 22 depth 16, 16 depth 32):
| Depth / legacy | Cases | ΔB range | Max native delta | Notes |
|---|---:|---|---|---|
| 8 / 0 | 9 | 1–43 | 1 | |
| 8 / 1 | 3 | 3–39 | 255 | includes both UBSan cases |
| 16 / 0 | 6 | 50–670 | 41 | |
| 16 / 1 | 16 | 2–420 | **32467** | worst index 141 (19×24); index 31 (5×12) 30887 |
| 32 / 0 | 8 | 2–464 | 0.00423956 | float units |
| 32 / 1 | 8 | 15–1620 | 0.253943 | float units |

**Cluster classification.** Signatures are T04's sorted `[stage, nondefault slots, depth]`; membership is the committed `tests/fuzz_corpus/olmblur` (39 files, 13 clusters). Representative = smallest saved shrunk case by active input bytes, then non-default count, then name; a representative is not proof for every member. `ΔB` is differing active bytes, `max` is the largest absolute byte/uint16/float delta, `ch` counts differing channels, and `bbox` is `(minx,miny,maxx,maxy)` zero-based. All 39 saved results have `first_mismatching_stage = null` and no paired AEX/Mac intermediate trace exists, so the first differing numerical stage is **unlocated for every row**.
| Cluster | Members | Rep (index; depth; geometry) | Observed route(s) | ΔB / max / ch; pixels; bbox | First word AEX → Mac | Classification |
|---|---:|---|---|---|---|---|
| `[1,2,5],8` | 1 | 176; 8; 1×43 | Smart mismatch | 12 / 1 / R2 G4 B6; 8; (0,1)-(0,26) | `7f` → `80` | unexplained |
| `[1,3],16` | 1 | 235; 16; 29×1 | Smart mismatch | 2 / 1 / R1 B1; 2; (17,0)-(20,0) | `fd4e` → `fc4e` | unexplained |
| `[1,3],8` | 1 | 236; 8; 8×40 | Smart mismatch | 17 / 1 / R2 G7 B8; 15; (0,1)-(4,36) | `42` → `41` | unexplained |
| `[1],16` | 3 | 268; 16; 1×29 | Smart mismatch | 1 / 1 / G1; 1; (0,11)-(0,11) | `2649` → `2749` | unexplained |
| `[1],32` | 1 | 270; 32; 28×1 | Smart mismatch | 81 / 1.19e-7 / R27 G27 B27; 9; (0,0)-(27,0) | `ffff7f3f` → `0000803f` | unexplained (PF32 ULP) |
| `[1],8` | 1 | 4; 8; 14×30 | Smart mismatch | 24 / 1 / R11 G7 B6; 21; (0,9)-(13,29) | `94` → `95` | unexplained |
| `[2,5],16` | 6 | 115; 16; 26×1 | Smart mismatch | 34 / 3 / R15 G10 B9; 18; (0,0)-(25,0) | `1a1a` → `191a` | unexplained |
| `[2,5],32` | 5 | 120; 32; 26×1 | Smart mismatch | 51 / 1.33e-4 / R12 G22 B17; 11; (8,0)-(23,0) | `bb39aa3e` → `b239aa3e` | unexplained |
| `[2,5],8` | 3 | 244; 8; 1×25 | Smart mismatch | 8 / 1 / G4 B4; 4; (0,1)-(0,19) | `44` → `45` | unexplained |
| `[3],16` | 3 | 261; 16; 1×25 | Smart mismatch | 21 / 26 / R6 G8 B7; 7; (0,13)-(0,19) | `543b` → `6e3b` | unexplained |
| `[],16` | 10 | 114; 16; 1×2 | Classic mismatch; Smart refusal | 12 / 4533 / R4 G4 B4; 2; (0,0)-(0,1) | `3b26` → `8614` | **port bug** (Classic copy path) |
| `[],32` | 1 | 99; 32; 1×31 | Smart mismatch; Classic refusal | 22 / 0.0 / R10 G12; 9; (0,7)-(0,19) | `4623c1ff` → `4523c17f` | unexplained (nonfinite input) |
| `[],8` | 3 | 8; 8; 2×1 | Classic mismatch; Smart refusal | 6 / 125 / R2 G2 B2; 2; (0,0)-(1,0) | `82` → `ff` | **port bug** (Classic copy path) |

The two `port bug` clusters contain all 13 Classic mismatches (10 PF16, 3 PF8). Every member has the default tuple (amount 5.0, smoothness 100.0, repeat 2, bias 1, legacy 0), the Mac Classic route returns a byte copy of the input, and the actual AEX returns different bytes. The other 11 clusters are Smart generic-beta residuals; none can be assigned to Windows UCRT, host/settings, or comparator error from the available evidence.

inference:
- The Classic "copy-only owner" comment is refuted as a general rule: 13/300 legal default-tuple cases are counterexamples, including a 1×2 PF16 case with a 4533-count sample delta. This is a Mac implementation gap, not a harness artifact; treating it as `port bug` follows the plan's table because the actual AEX bytes and the Mac copy path are directly comparable.
- `generic-small-fixture` currently hides a large compatible domain: 148/198 refused cases already render exactly through the generic-beta lane. Widening the admission is the highest-value change, but it must come after the 50 residuals (especially the 16bpc legacy max 32467 and the PF8 NaN/inf UB) are fixed; enlarging the fan-out without that would convert refusals into mismatches.
- The Classic non-default gate is not a safety guard; it is the absence of a Classic numeric owner. Removing it only exposes the input copy: 179/192 new mismatches and 13 accidental exact no-ops. A fix must implement the actual Classic PF8/PF16 operation, not widen the copy.
- PF32 Classic has no fall-through implementation at all: removing the `ARGB128` return lands in `classic-copy-geometry` with a zero `pixel_bytes`. The compound experiment (86 mismatch/9 exact) shows even a copy-style fallback is not the AEX behavior.
- The 16bpc legacy residuals are the largest numerical signal (32467/30887 on 5–24 px fixtures), while 32bpc residuals are float-ULP scale. This points at the legacy 16bpc store/normalization path, but without paired stages it remains a hypothesis, not a located first difference.
- The two UBSan findings are real undefined behavior in shared core code, but they are reachable only through the scratch gate-off; production currently refuses those inputs. They are prerequisities for admission work, not production regressions.
- No claim is made about native Windows UCRT, native AE, GPU, full-domain compatibility, or global minimality. Counts are for seed 1, the retained worker and this tracing build; wall-time budget/uncompared counts can move by one under load.

changed_files:
- `mac/OLMBlur/OLMBlur.cpp` — optional refusal tracing; `GenericBetaTupleRefusal` reason split; no admission predicate or arithmetic changed.
- `tools/fuzz/adapters/olmblur.py` — per-route trace capture outside the compared result.
- `tools/fuzz/adapters/public.py` — optional per-call `env` argument for `candidate`.
- `tools/fuzz/triage_olmblur.py` (new) — reproducible guard ranking, scratch gate-off builds, sanitizer probes and cluster byte statistics.
- `reports/fuzz/olmblur_refusals_20261022.json` (new) — full attributed seed-1 census.
- `reports/fuzz/olmblur_trace_replay_20261022.json` (new) — 39/39 replay neutrality evidence.
- `reports/fuzz/olmblur_triage_20261022.json` (new) — gate-off counts, per-case details, sanitizer diagnostics and cluster representatives.
- `orchestra/reports/T09-triage-olmblur.md` — this report.

verify:

Run from this worktree. Keep `--jobs 2` and a scratch corpus destination so `tests/fuzz_corpus/olmblur` is not rewritten.
```sh
mkdir -p orchestra/state/T09-triage-olmblur
OLM_FUZZ_INTEGRATION=1 python3 tools/fuzz/test_framework.py
python3 tools/fuzz/run.py --plugin olmblur --n 300 --seed 1 --jobs 2 --budget-minutes 30 \
  --shrink-attempts 0 --scratch orchestra/state/T09-triage-olmblur \
  --report orchestra/state/T09-triage-olmblur/verify-census.json \
  --corpus orchestra/state/T09-triage-olmblur/verify-corpus
python3 tools/fuzz/run.py --plugin olmblur --jobs 2 --replay tests/fuzz_corpus/olmblur \
  --scratch orchestra/state/T09-triage-olmblur \
  --report orchestra/state/T09-triage-olmblur/verify-replay.json
python3 tools/fuzz/triage_olmblur.py --census reports/fuzz/olmblur_refusals_20261022.json \
  --report orchestra/state/T09-triage-olmblur/verify-triage.json \
  --scratch orchestra/state/T09-triage-olmblur --jobs 2
```
Expected: 8 tests OK; census `complete` with AEX 300 ok, Classic 13 mismatch / 287 refusal, Smart 76 exact / 26 mismatch / 198 refusal, 485/485 refusals attributed; replay 39/39 `matches_saved`; triage gate counts `148/50`, `13/179`, `95/95 refusal via classic-copy-geometry`, `9/86`, and sanitizer `148/48/2`.

Compact evidence check without rebuilding:
```sh
python3 - <<'PY'
import json
r=json.load(open('reports/fuzz/olmblur_trace_replay_20261022.json'))
c=json.load(open('reports/fuzz/olmblur_refusals_20261022.json'))
t=json.load(open('reports/fuzz/olmblur_triage_20261022.json'))
assert r['replay_matches_saved'] and len(r['replays'])==39
assert c['summary']=={'aex_ok':300,'both_routes_exact':0,'classic_mismatch':13,'classic_refusal':287,
                      'pixel_mismatch_cases':39,'smart_exact':76,'smart_mismatch':26,'smart_refusal':198}
assert sum(g['events'] for g in t['guards']['classic'].values())==287
assert sum(g['events'] for g in t['guards']['smart'].values())==198
g=t['gate_off']
assert g['smart-small-fixture-off']['counts']=={'exact':148,'mismatch':50}
assert g['classic-nondefault-tuple-off']['counts']=={'exact':13,'mismatch':179}
assert g['classic-pf32-naive-off']['counts']=={'refusal':95}
assert g['classic-pf32-copy-off']['counts']=={'exact':9,'mismatch':86}
assert len(t['clusters'])==13
assert all(c['routes']['smart']['status']!='error' for c in t['clusters'])
print('PASS: replay, attribution, gate-off and 13 clusters')
PY
git diff --check
```

next:

Proposed fix/investigation tickets (one scope each; none implemented here):
- **BLUR Classic default-tuple copy counterexamples:** investigate the 13 default-tuple legal cases (indices 5, 8, 74, 114, 122, 128, 159, 181, 191, 203, 230, 234, 271) where AEX does not copy; representatives `1×2` PF16 (ΔB 12, max 4533) and `2×1` PF8 (ΔB 6, max 125). Evidence: 2 clusters, both `port bug`.
- **BLUR Classic non-default PF8/PF16 owner:** 192 refusals; gate-off copy gives 179 mismatch / 13 exact. Recover the Classic numeric path (boundary: amount≠5 153, smoothness≠100 137, repeat≠2 118).
- **BLUR Classic PF32 ARGB128 owner:** 95 refusals; naive removal has no fall-through (95/95 `classic-copy-geometry`), compound copy gives 86 mismatch / 9 exact. Need the actual Classic PF32 owner.
- **BLUR Smart tiny-fixture admission:** 198 refusals; gate-off `generic-small-fixture` gives 148 exact / 50 mismatch. Widen only after the residuals below; this is the largest immediate exact win.
- **BLUR 16bpc legacy generic residual:** 16 gate-off mismatches, max sample deltas 32467 (idx 141, 19×24) and 30887 (idx 31, 5×12); cluster `[2,5],16` ΔB 34 / max 3. Pair legacy normalization/store words with AEX.
- **BLUR PF8 legacy NaN/inf conversion:** UBSan `core/olmblur_worker8_legacy.cpp:114:52` on idx 77 (18×18, NaN) and idx 112 (4×9, inf); define the original conversion semantics before admitting these inputs.
- **BLUR generic-lane residual census:** 50 gate-off mismatches and 11 unexplained clusters, ΔB 1–1620, 32bpc float-ULP scale. Add paired pre-store RGB / post-normalization capture so the first differing stage can be named; do not add tolerance.
- **BLUR PF32 nonfinite residual:** cluster `[],32` idx 99 (1×31 nonfinite), ΔB 22, all differing words nonfinite, max finite delta 0.0; recover NaN payload/propagation, no clamping or look-matching.

Final scratch size before deleting regenerable build outputs: **4.1 MiB**.
