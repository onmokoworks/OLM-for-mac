status: blocked

summary:
- The two alleged Classic copy-path port-bug clusters are a comparator route mismatch: all 13 shrunk members are exact against original AEX Classic, while AEX Smart returns different bytes.
- Original AEX public-selector execution and read-only worker-entry traces prove that Classic reads default Amount 5.0 as integer zero and preserves the initial copy.
- Stopped under ticket acceptance item 1: “cause ... outside the port ... comparator — then document and stop.” No production, admission, corpus, release-gate, ledger, other-plugin, MAIN, or emulator-source changes.
- Seed-1 before/after remains Classic 0 exact / 13 mismatch / 287 refusal and Smart 76 exact / 26 mismatch / 198 refusal under the existing Smart-only comparator; all 300 results are unchanged.
- Corpus replay is 39/39 matches_saved; three existing Classic tests pass. Smart admission promotion remains unperformed.

facts:

Read `AGENT_GUIDE.md`, the OLMBlur ledger rows/forbidden actions, plan classification table, GOTCHAS, T09 and F12 evidence. No push or history rewrite. Scratch is under `orchestra/state/F15-olmblur-small-fixture-promotion`, under 2 MiB; disposable compiled probes are removed automatically. No writes to `/tmp`.

**Route error and independent trace.** `tools/fuzz/adapters/public.py` sets `oracle_route = 'smart'` and `oracle_path = 'smartfx'`; OLMBlur inherits both. Its single oracle is used for both candidate routes. The audit runs the cached original-AEX worker with explicit `--fixture-render-path classic` and `smart`, and compiles the unchanged real-SDK Mac public host. Every new Smart hash equals the saved corpus oracle hash; every new Mac Classic hash equals its saved hash. Thus changing the cached worker did not change these witnesses.

Separately, the retained guarded fixture calls original AEX export `0x18000a970` with selectors 5, 10, 11, 12, 8 for each corpus member. A read-only Unicorn hook at PF8 worker `0x180003710` or PF16 worker `0x180002280` records context `+0x20/+0x24/+0x28`: **Amount 0.0, Smoothness 6553600.0, Repeat 2 in all 13**. Output at worker entry already equals the input hash, and final output still equals it. Each public call returns 0 and invokes copy once; retained assertions verify source/parameters/world/guards and padding. The direct fixture has its own padded world; worker and Mac replay use the corpus's active pixels. No claim equates padding between those independent transports.

Static evidence, read from MAIN without modifying it: `decomp/OLMBlur.aex.c.txt`, `FUN_18000a180` lines 4518–4575, reads slots 1 and 2 as signed integers at `+0x38`. Disassembly at `0x18000a1fd/0x18000a202` (PF16) and `0x18000a2aa/0x18000a2af` (PF8) is `MOVD` then `CVTDQ2PS`. The low dword of the registered float-slider double `5.0` is zero. Both workers return without numerical work when context Amount is zero. This agrees with the live intermediate trace and the existing Classic closure report; T09's “confirmed port bug” diagnosis compared different owners.

**Shrunk cluster diagnostic table.** Production before/after is unchanged in every row. “Smart ΔB” describes the incorrect cross-route comparison; Classic ΔB is against original AEX Classic.

| Seed-1 index | Depth | Geometry | Smart ΔB | Classic ΔB |
|---:|---:|---|---:|---:|
| 5 | 16 | 1×8 | 30 | 0 |
| 8 | 8 | 2×1 | 6 | 0 |
| 74 | 16 | 3×1 | 4 | 0 |
| 114 | 16 | 1×2 | 12 | 0 |
| 122 | 16 | 1×5 | 8 | 0 |
| 128 | 16 | 1×5 | 8 | 0 |
| 159 | 8 | 1×4 | 4 | 0 |
| 181 | 16 | 4×3 | 18 | 0 |
| 191 | 16 | 1×3 | 17 | 0 |
| 203 | 16 | 1×2 | 12 | 0 |
| 230 | 16 | 1×3 | 8 | 0 |
| 234 | 16 | 1×2 | 4 | 0 |
| 271 | 8 | 2×1 | 4 | 0 |

Representative first mismatches against Smart: index 8 at byte 1, AEX Smart `82` vs Mac Classic `ff`; index 114 at byte 2, AEX Smart `3b` vs Mac Classic `86`. Against AEX Classic there is no first mismatch. Full hashes, traces and corpus filenames are committed in `reports/fuzz/olmblur_classic_routes_F15.json`.

**Seed-1 campaign before/after (existing comparator, 300 cases, jobs 2).**

| Route | Before exact / mismatch / refusal | After exact / mismatch / refusal |
|---|---|---|
| Classic | 0 / 13 / 287 | 0 / 13 / 287 |
| Smart | 76 / 26 / 198 | 76 / 26 / 198 |

Both campaigns complete with AEX 300/300 ok; comparing all `cases[i].result` dictionaries gives zero changes. Corpus replay completes with `completed=39`, `replay_matches_saved=true`. No corpus expectation is updated; 39/39 stay unchanged. These baseline counts intentionally retain the faulty comparator, rather than silently relabeling results as a production improvement.

**Identity.**

| Artifact | SHA-256 |
|---|---|
| Unchanged production `mac/OLMBlur/OLMBlur.cpp` | `cf362169e4ca3bd76d06fe59e31c4d07401964bbe5bf19189cd9d142c6da4cf3` |
| Mac public candidate | `942d049bbf91dfe262273a0334d598d6bd77b789bc892fda5e0951ad46cf68cb` |
| Original AEX | `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b` |
| Route audit cached worker | `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2` |
| Existing campaign/replay default retained worker | `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261` |
| Audit script | `5b13939b70fb4b6534cc97b1859062d30ed5e948879ac42decf85c8c107482fc` |
| Audit JSON | `be96ba501a6ca48f7a5e9eb9f8dad5fe4ab84c7b1e7f843a3af4d3ded073ac90` |

inference:
- The confirmed defect is the test's route binding, not these Classic output bytes. Implementing Smart blur in Classic to satisfy this comparator would break observed original Classic behavior.
- This does not prove arbitrary nondefault Classic tuples, PF32 Classic, or native AE/UCRT behavior. The direct and resident observations are local original-AEX emulation evidence.
- The separate Smart generic-small-fixture residuals remain unresolved. No guard was relaxed, no sanitizer-clean admission is claimed, and no fresh-seed promotion campaign was run after the explicit stop condition.

changed_files:
- `tools/emulation/audit_olmblur_classic_routes_F15.py` — reproducible route-specific original-AEX/Mac comparison plus read-only Classic intermediate traces.
- `reports/fuzz/olmblur_classic_routes_F15.json` — 13 cases, hashes, intermediate values and provenance.
- `orchestra/reports/F15-olmblur-small-fixture-promotion.md` — this report.

verify:

Run from this worktree. These are the commands used (the audit was repeated after adding saved-hash assertions). The baseline/replay commands use the existing default retained worker as T09 did; the audit defaults to the cache INDEX's absolute frozen-reference worker path. All long-command output goes to scratch logs.

```sh
s="$PWD/orchestra/state/F15-olmblur-small-fixture-promotion"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/audit_olmblur_classic_routes_F15.py \
  --scratch "$s" --report "$s/verify-routes.json" > "$s/verify-routes.log" 2>&1
for phase in before after; do
  python3 tools/fuzz/run.py --plugin olmblur --n 300 --seed 1 --jobs 2 \
    --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" \
    --corpus "$s/$phase-corpus" --report "$s/$phase.json" > "$s/$phase.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmblur --jobs 2 --replay tests/fuzz_corpus/olmblur \
  --scratch "$s" --corpus "$s/replay-corpus" --report "$s/replay.json" > "$s/replay.log" 2>&1
PYTHONPATH=tests python3 -m unittest test_olmblur_generic_classic_beta_20260822 > "$s/tests.log" 2>&1
python3 - <<'PY'
import json
from pathlib import Path
s = Path('orchestra/state/F15-olmblur-small-fixture-promotion')
b, a, r = [json.loads((s / name).read_text()) for name in ('before.json', 'after.json', 'replay.json')]
assert b['completed'] == a['completed'] == 300
assert [v['result'] for v in b['cases']] == [v['result'] for v in a['cases']]
assert r['completed'] == 39 and r['replay_matches_saved']
print(a['summary'], 'all 300 results unchanged; replay 39/39')
PY
git diff --check
```

Expected: `PASS_COMPARATOR_ROUTE_SPLIT`, 13 Classic exact / 13 Smart cross-route mismatches, depth split 3 PF8 + 10 PF16; campaign counts in the table; replay 39/39; three tests OK; clean diff check. No sanitizer run is required for this evidence-only change, and it supplies no basis to relax an admission guard.

next:
- Correct OLMBlur fuzz oracle binding to compare Classic with original Classic and Smart with original Smart; capture route-specific provenance and migrate expectations with an explicit before/after table. Audit other adapters separately, outside this ticket.
- Reissue Smart small-fixture admission as an independent fix ticket after comparator correction. Require gate-off evidence on seed 1 and a fresh seed, zero newly admitted mismatches, and ASan/UBSan clean; retain T09's PF8 NaN/inf sanitizer counterexamples.
- Do not implement the proposed Classic copy-path change from these two clusters: both are already exact under the correct route contract.
