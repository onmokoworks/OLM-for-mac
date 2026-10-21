status: done

summary:
- Promoted the general all-rays-disabled tuple, retaining finite-SDR, full-frame, size, layout and lifecycle guards.
- Production Classic/Smart exact counts rise 0→19 each for seed 1 and 0→17 each for seed 2; zero admitted mismatches.
- Both gate-off campaigns and production sanitizer replays are clean; an independent 324-case AEX matrix is exact on both routes.
- Only production corpus case 38 changes behavior, refusal→exact on both routes; its expectation update is recorded below.
- Active-ray promotion is rejected by fresh seed-2 counterexamples. Tiny frames and other unsupported families remain refused.

facts:

Base: `51b739b4cd7cf4751c0d01ef17f8a8ac54733e10`, branch `orch/F10-kira-admission-promotion`.
Read `AGENT_GUIDE.md`, the KiraKira ledger rows, the compatibility plan, emulator GOTCHAS, F09/T06 evidence and worker INDEX. No release gate, ledger, other plugin, MAIN source, external emulator source, installed bundle or worker was changed. No rebuild of the reference worker, install, push or merge.

Machine evidence: `reports/fuzz/olmkirakira_admission_F10.json`. Reproduction and assertions: `tools/emulation/verify_kirakira_admission_F10.py`. All campaigns used `--jobs 2`, original AEX Smart output and Mac public Classic/Smart entry points, with raw typed comparison and no tolerance. These are CPU emulation/fake-host results, not native AE/UCRT, GPU, ROI or downsample proofs.

Identities:

- AEX, MAIN `plugins_2025/OLMKiraKira.aex`: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- Retained public worker: `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`, `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. INDEX lists RadialBlur workers; this is the retained KiraKira worker used by T06/F09.
- Source before: `c3cb49527eaef8f51031487db57d5af56eee5933aa3583f02dd7b9865cd5eaf6`; after: `63ffa39be7a954fe2a8e17153c94d83929b0abfa7b61f635f9d5385c3fd6fe2e`.

Admission rule:

- Vertical, Horizontal, Diagonal and Diagonal-2 Length, and Highlight Radius, are all exactly zero.
- Approximated Input is off; Source Opacity is exactly 100%; Glow Opacity is in its legal 0–10000% range.
- Channel 1–6, Blur Mode 1–3 and Merge Mode 1–2. Seed controls, ray colors, ramp flags and Rotation do not affect zero rays.
- Existing finite SDR input checks remain: PF16 samples ≤32768; PF32 samples finite and in [0,1]. No source-image matching or per-case index predicate.
- Existing generic dimensions remain width ≥9, height ≥7, each ≤4096, and area ≤4096×2160. Existing equal dimensions, zero origins, nonoverlap, valid positive byte strides/formats, full-frame Smart requests and callback lifecycle checks remain.
- This enters the existing renderer and typed writer. It does **not** copy input pixels or bypass composition. No arithmetic was changed.

Original-AEX branch and trace facts:

1. MAIN `decomp/OLMKiraKira.aex.c.txt`, `FUN_18114f4a0` (line 3523894): five ray planes are zero-initialized; each helper is under `iVar6 != 0`. Zero lengths avoid directional geometry, warp/filter and Highlight execution. `FUN_18114fd90` skips zero rays and leaves zero glow. The color constructor's four-channel representation also stays zero on this branch; the independent matrix exercises all six public Channel choices.
2. `FUN_18114e860` (line 3523470) stores source/glow opacity using float multiplication by `DAT_181486c10`. Reading the AEX constant gives bytes `0ad7233c` (float32 0.009999999776482582). At Source Opacity 40 and 97, AEX multiplication produces `cccccc3e` / `eb51783f`, while the port's double division then float conversion gives `cdcccc3e` / `ec51783f`. At 100, both give `0000803f`. Fractional-opacity admission is therefore excluded; conversion repair is separate work.
3. Independent PF8/PF16/PF32 original full-caller traces are bound to the retained public Smart worker and Mac production output. The import-free source-reader ABI check passes. Source, scalar seed, all five zero ray planes and zero glow are exact; no directional sin/cos call occurs.
4. PF32 edge input exposes a **trace-boundary difference**, not an output mismatch. The first verification run exited 1 at `composed`: ten words differ, first AEX `00000000` versus Mac `0000c07f`. The AEX hook is after `FUN_181156740`; assembly `18115676a MAXSS XMM0,XMM1` maps unordered values to zero. The Mac hook precedes the existing `PixelTraits::WriteAexTruncate`/`Clamp01`. Comparing the already-rendered PF32 bytes after that clamp, reordered ARGB→RGBA without arithmetic, is exact. The verifier retains the pre-clamp difference and requires exact post-clamp/output bytes. Neither renderer was adjusted to erase the observation.
5. Python traces retain the existing Windows allocation/TLS/CRT/import scaffold and Python libm substitutions; no AEX numerical function is detoured. Public-worker output binding is required for every trace.

Measured campaigns (E/M/R/U = exact/mismatch/refusal/uncompared):

| Seed / campaign | Classic E/M/R/U | Smart E/M/R/U | AEX success/reject |
|---|---|---|---|
| 1 production before | 0/0/300/0 | 0/0/300/0 | 287/13 |
| 1 gate-off, ASan/UBSan | 198/89/0/13 | 98/39/163/0 | 287/13 |
| 1 production after | 19/0/281/0 | 19/0/281/0 | 287/13 |
| 2 production before | 0/0/300/0 | 0/0/300/0 | 291/9 |
| 2 gate-off, ASan/UBSan | 209/82/0/9 | 98/45/157/0 | 291/9 |
| 2 production after | 17/0/283/0 | 17/0/283/0 | 291/9 |

All newly admitted route outputs equal their gate-off and original-AEX hashes. All previously refused cases outside the predicate still refuse. Sanitized production replay checks all **1,200 route executions** against the ordinary campaigns. No sanitizer abort/error, admitted mismatch, or admitted case without successful AEX output occurred. AEX rejections are not treated as exact.

The independent matrix is the Cartesian product of three geometries (9×7, 17×11, 31×29), three depths, two merge modes, three blur modes and six channels: **324 AEX cases / 648 exact Mac route renders** under ASan/UBSan. It varies otherwise inactive legal gain/strength/fade/rotation/colors/ramp controls and Glow Opacity, includes zeros, signed zero, subnormal/normal PF32 boundaries and values next to one, and uses 3-byte input / 5-byte output padding. Fourteen one-away settings/profiles/layout sizes yield **28 clean refusals**, with destination storage untouched. The host also checks source/padding preservation and balanced parameter checkouts/checkins.

Rejected broader candidate:

- Finite-SDR PF16/PF32, Channel 1, Strength 100, Mode 1/2, no approximation, both opacities 100%, existing generic dimensions: seed 1 is **38/38 exact**, but seed 2 is **35/37 exact** on Classic. Thus seed-1 success alone does not justify promoting active rays.
- Seed 2 index 127, PF32 9×19: 170 words / 502 bytes differ; first byte 20, AEX `26106c3f`, Mac `ce26663f`.
- Seed 2 index 177, PF32 13×12: 118 words / 314 bytes differ; first byte 8, AEX `49957d3f`, Mac `9f557d3f`.
- These new output boundaries are retained by the reproducible seed-2 campaign. No active-ray guard was relaxed and no numerical hypothesis was patched to these values.

Corpus before/after and expectation updates:

| Corpus cases | Fresh Classic before→after | Fresh Smart before→after | Saved expectation action |
|---|---|---|---|
| Production index 38, PF16 10×7 | refusal→exact | refusal→exact | Updated both results; retained previous result and linked this report |
| Other 7 production cases | unchanged refusal | unchanged refusal | None |
| All 62 T06 shrunk cases | unchanged production refusal | unchanged production refusal | None |
| Same 70 cases with final tuple guard off | all outputs/statuses unchanged | all outputs/statuses unchanged | None |

There are **140 production route comparisons and 140 diagnostic route comparisons**, each run at both source revisions under sanitizers. Only case 38 changes production behavior; it now hashes to the original AEX `dc1f53a1188bef8f7391b7f0856a98b98fc74e806335150ab60211d9e79f43bb`. Its input remains `7336db664495f66ea772ead9912d6ef9f071d9dcc37717f19d59ea415806395c`. No rendered sample changed away from exact. The named F09 active-ray shrunk cases are deliberately not promoted by this rule; their diagnostic results remain unchanged.

Strict saved-result production replay initially matches 5/8 (new improvement plus inherited metadata drift). After updating only case 38 it matches **6/8**, exit 1: indices 2 and 3 remain refusals, but their inherited Smart COUNTS are `1 1 1 25 25` / `1 1 1 26 26` instead of saved `1 1 1 0 0`. This is the pre-existing F03/F09 metadata issue, not a new pixel or refusal regression. The alternate-source campaign wrapper reproduces **8/8 fresh baseline result objects** for these cases.

Fast existing tests: **25 passed**: generic-beta lane (9), merge2 float oracle (6), outer compose oracle (9), bounded typed-writer ownership assertion (1). `git diff --check` passes.

inference:

- Zero-ray admission is supported by the original branch structure, zero plane traces, both independent fuzz seeds, the independent parameter matrix and sanitizer checks. It avoids rather than assumes resolution of the active scalar/color/Gaussian/geometry differences.
- Source Opacity 100% isolates an exactly shared conversion value. This is a general public-control tuple, not a correction to expected samples.
- Finite coverage and branch recovery support this bounded production admission; they do not establish all-input/native-host compatibility. The old minimum dimensions and all other families remain conservative boundaries.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/verify_kirakira_admission_F10.py`
- `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000038.json`
- `reports/fuzz/olmkirakira_admission_F10.json`
- `orchestra/reports/F10-kira-admission-promotion.md`

verify:

Run from this worktree. All long-command output goes to ticket scratch. Original before campaigns used ordinary `run.py` before editing; `--campaign-source` reproduces that source without changing the checkout.

```sh
s="$PWD/orchestra/state/F10-kira-admission-promotion"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 51b739b4cd7cf4751c0d01ef17f8a8ac54733e10:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 2; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --scratch "$s" --report "$s/before-seed$seed.json" --corpus "$s/before-seed$seed-corpus" > "$s/before-seed$seed.log" 2>&1
  python3 tools/fuzz/triage_kirakira.py --experiment all --sanitizers --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/gateoff-seed$seed.json" --corpus "$s/gateoff-seed$seed-corpus" > "$s/gateoff-seed$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --scratch "$s" --report "$s/after-seed$seed.json" --corpus "$s/after-seed$seed-corpus" > "$s/after-seed$seed.log" 2>&1
done
"$py" tools/emulation/verify_kirakira_admission_F10.py --before-source "$s/before.cpp" --campaign-dir "$s" --scratch "$s/verify" --report "$s/verification.json" > "$s/verification.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/replay-production.json" --corpus "$s/replay-corpus" > "$s/replay-production.log" 2>&1
# Expected exit 1 / 6 of 8 saved results above; continue explicitly.
PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820 test_olmkirakira_merge2_float_oracle_20260728 test_olmkirakira_outer_compose_oracle_20260728 test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.Mode4FullCallerHostlessExactTests.test_mac_production_owns_the_bounded_highlight_and_typed_writer > "$s/fast-tests.log" 2>&1
git diff --check
```

Expected: campaign counts as above; verification `PASS`, 324 independent exact cases, 28 negative refusals, three bound traces (PF32 pre-clamp difference retained, post-clamp exact), unchanged diagnostic corpus bytes, only case 38 improving in production; 25 tests pass. The verifier deletes its regenerable builds on completion. Scratch remains well below 5 GiB.

next:
- Recover active-ray geometry/float trigonometry, color-plane seeds, tiny Gaussian behavior and opacity materialization before broader promotion. Seed-2 indices 127/177 are additional negative witnesses.
- Consider a separate zero-ray positive-dimension/Smart-request ticket for tiny frames; this ticket does not alter layout/request policy.
- Reconcile inherited corpus refusal metadata for indices 2/3 separately. Native Windows/UCRT/AE and installed-host coverage remain outside this evidence.
