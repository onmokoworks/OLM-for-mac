status: done

summary:
- Closed approximated-input / all-rays-zero Smart source composition for finite SDR frames with both dimensions≥4.
- Seed1 improves215/0/85→219/0/81; fresh seed7 improves223/0/77→225/0/75. Seed6 stays227/0/73.
- All previous exact Smart and all Classic records persist;900 sanitized campaign routes,378 independent exact cases and18 negative refusals pass.
- Corpus index0 is rebased refusal→exact with its prior result retained. Diagnostic corpus changes620 samples, all to exact; strict replay8/8.
- Active-ray approximation remains excluded: original embedded IPP interpolation differs from the rejected generic linear experiment.

facts:

Base `75c7c728`. Machine evidence `reports/fuzz/olmkirakira_smart_C13_zero_approx.json` binds source/AEX/worker identities. Same original AEX and retained public worker hashes/absolute paths as the signed cluster. No external worker/source, MAIN, release gate, ledger or other-plugin modification.

| n300/jobs2 | Before E/M/R | After E/M/R | AEX Smart output/reject |
|---|---|---|---|
| seed1 |215/0/85|219/0/81|287/13|
| seed6 |227/0/73|227/0/73|291/9|
| fresh seed7 |223/0/77|225/0/75|287/13|

Seed1 remeasurement is the previous cluster's final campaign. Approximation had19 successful-oracle refusals across channels; the Alpha/Mode2 subgroup had9. The zero-ray subset is independent of unresolved interpolation values: `18114f4a0` zero-initializes five ray planes, skips every zero-length helper and accumulates zero glow. The original typed owner resizes only glow and composes with the original full-resolution source. The old port resized its small composed image, changing source samples despite zero glow. The fix selects full-resolution source composition for all-zero rays. Other approximation arithmetic/admission remains unchanged.

Public-bound seed1/index193 (PF16 12×8) before: full-resolution source, all five zero rays, small/full glow are exact. The first differing value on the output dependency path is composed word4, AEX `00e0203f`, Mac `00000000`. Final254 words/477 bytes differ, first word4 `0080` versus `0000`. After: original full source, zero rays, small/full glow, composed and final output are exact. The unused reduced source/seed planes still differ because the active interpolation operation is not restored; those planes cannot contribute with zero rays. This is explicitly not an all-stage approximation closure.

New Smart admission uses the existing zero-ray tuple with approximation allowed only at width≥4,height≥4; all positive full-frame/storage/downsample guards and finite SDR source checks remain. Source Opacity100%, Glow0–10000%, Channel1–6, Blur Mode1–3 and both merges retain their declared zero-ray interpretation. Strength, Fade, colors/default ramps and rotation cannot contribute to zero glow. Classic admission remains unchanged. No raw Length1/effectively-zero ray, non-SDR source or fractional Source Opacity is added.

Independent ASan/UBSan matrix:7 geometries (4×4,4×9,9×4,6×8,7×11,9×7,17×13)×3 depths×3 modes×6 channels =378 exact. Both merge choices, randomized colors/default ramps, strength/gain/glow/rotation controls, SDR edge/random samples and odd byte strides are covered. Eighteen one-away cases refuse:15 small geometry/depth pairs plus active Length1, Source97%, and HDR Alpha. Some small shapes also cause the original IPP to throw; those have no reference output and are never admitted. The public host checks source/padding preservation, unchanged destination on refusal and balanced callbacks.

| Corpus inputs | Fresh production Smart before→after | Diagnostic arithmetic |
|---|---|---|
| production index0 |refusal→exact, prior result retained|new admitted exact|
| T06 shrunk282 |refusal→refusal (source opacity outside new rule)|310 changed samples per route, all exact|
| other68 |unchanged status/bytes|unchanged bytes|

All70 production corpus comparisons pass. All140 arithmetic route comparisons pass,620 changed samples all toward original Smart. The arithmetic auditor now explicitly permits refusal→exact when the full new byte array equals the fresh original output; it still forbids changed rendered samples away from exact. Historical T06 expectations remain historical. Strict production replay is7/8 before explicit rebaseline and8/8 after. All900 campaign Smart routes independently rerender under ASan/UBSan, preserving previous exact records and all Classic records. Existing25 fast tests pass; compiled sanitizer passes54 internal rows including HD in42.840 seconds. `git diff --check` passes.

Active approximation investigation, not promoted:

- Prior 20260718 audit claims interpolation0. Actual instructions at `18114ce43` and `18114d101` store **1** at `[RSP+0x28]`, the sixth Win64 argument to `1812639f0`; the fifth argument is double0 at `[RSP+0x20]`. The original typed owner also resizes glow before its full-source outer writer. This corrects the interpretation without editing historical reports or release evidence.
- The extended paired trace executes original `181157770` Mat constructors and `1812639f0` resize bodies, with actual explicit dimensions/interpolation1. No numerical function is detoured. Seed1/index70 (6×17 PF16) binds to original public Smart. The old port first differs at reduced-source word0: AEX `80b7793e`, Mac `009a183f`; final357 words/705 bytes differ.
- A diagnostic general bilinear implementation plus full-source composition restores source/seed/all rays/glow. Its first remaining enlarged-glow difference is word15 `fbed413e` versus `fced413e`. Replicated-border coordinate clamping removes that boundary but exposes word35 `cfea863e` versus `ceea863e`:29 enlarged-glow words and6 final PF16 words remain different. Both experiments supply new boundary values; neither is promoted.
- Runtime destination-write hooks identify embedded IPP edge stores `180323bbd` etc. Disassembly of `1803238a0` shows `a + (b-a)*weight` with separate SUBSS/MULSS/ADDSS, unlike two weighted products. Interior output is copied through `1806e6eef/ef3`; its original producer and coefficient/dispatch semantics remain unclosed. A2×2 independent case throws `IwException@ipp` at `18125ef13`, reinforcing the unproven one-pixel workspace boundary. No output is inferred from that rejection.
- The rejected candidate is retained as `tools/emulation/fixtures/kirakira_resize_linear_C13.patch`, against this cluster's base source. Its hash matches the captured writer trace. The active-renderer admission is unchanged. Embedded IPP recovery is a follow-up, not a reason to fit final bytes.

inference:

Zero-ray source composition can be restored without assuming interpolation equivalence because the only resized contributing plane is identically zero. Finite matrices/public binding establish this bounded CPU/fake-host rule. They do not establish active IPP resize, native AE/UCRT, arbitrary HDR, custom active ramps or ROI/downsample compatibility.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/{probe_kirakira_smart_C07,trace_kirakira_numeric_F09,audit_kirakira_numeric_corpus_F09}.py`
- `tools/emulation/fixtures/kirakira_resize_linear_C13.patch`
- `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000000.json`
- `reports/fuzz/olmkirakira_smart_C13_zero_approx.json`
- `orchestra/reports/C13-kira-smart-r3{,-zero-approx}.md`

verify:

At this cluster commit:

```sh
s="$PWD/orchestra/state/C13-kira-smart-r3/recheck-zero"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 75c7c728:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 6 7; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/before-seed$seed.json" --corpus "$s/before-seed$seed-corpus" > "$s/before-seed$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/after-seed$seed.json" --corpus "$s/after-seed$seed-corpus" > "$s/after-seed$seed.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 6 7 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/probe_kirakira_smart_C07.py --family approximation-zero --require-exact --scratch "$s/matrix" --report "$s/matrix.json" > "$s/matrix.log" 2>&1
python3 tools/emulation/probe_kirakira_smart_C07.py --family approximation-zero-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --campaign-seed 1 --trace-index 193 --require-exact --scratch "$s/trace" --report "$s/trace.json" > "$s/trace.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/arithmetic" --report "$s/arithmetic.json" > "$s/arithmetic.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
cp "$s/before.cpp" "$s/linear.cpp"
patch "$s/linear.cpp" < tools/emulation/fixtures/kirakira_resize_linear_C13.patch > "$s/patch.log"
"$py" tools/emulation/probe_kirakira_smart_C07.py --source "$s/linear.cpp" --gate-off --campaign-seed 1 --trace-index 70 --keep-trace --scratch "$s/active" --report "$s/active.json" > "$s/active.log" 2>&1
git diff --check
```

Expected: campaign table;900 sanitized routes;378 exact;18 refusals;70 corpus comparisons; index193 exact output/full-source/zero glow with unused reduced planes explicitly different;620 diagnostic changed samples all exact; replay8/8. Rejected linear experiment remains public-bound, first enlarged-glow word35,6 final words differing.

next:
- Two ticket clusters closed. Remaining seed1:81 refusals (13 without original output).
- Move active approximation to an embedded IPP resize ticket; investigate Alpha Gaussian controls next (9 successful-oracle refusals versus8 Channel6/Mode2 cases).
