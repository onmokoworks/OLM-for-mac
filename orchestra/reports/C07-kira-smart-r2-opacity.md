status: done

summary:
- Closed the scalar Alpha / unit Strength / box-mode opacity materialization cluster on Smart.
- Seed 1 improves 134/0/166 to 171/0/129; fresh seed 5 improves 127/0/173 to 172/0/128 (exact/mismatch/refusal).
- All baseline-exact Smart records and all Classic campaign records remain identical; 600 sanitized production campaign routes pass.
- Independent source/glow/combined-opacity matrices pass 180/288/288 cases. The 140-route arithmetic corpus audit changes 546 samples, all toward exact.
- Rebased only production corpus index16, refusal→exact, retaining its previous complete result. Strict replay passes 8/8.

facts:

Base `81a91efdcc5f3cb55003478cae8665ca42ad8916`. Read the shared guide, compatibility plan, emulator GOTCHAS, KiraKira ledger restrictions and preceding T06/F03/F04/F09/F10/F11/F12/C04 reports. No MAIN, worker, external emulator source, ledger, release gate or other plugin modification; no push, install or worker rebuild.

Machine evidence: `reports/fuzz/olmkirakira_smart_C07_opacity.json`. The original AEX SHA256 is `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`; retained worker SHA256 is `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. Paths are the unchanged MAIN `plugins_2025/OLMKiraKira.aex` and `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`. INDEX contains RadialBlur workers, not a replacement KiraKira worker.

| Campaign, n300/jobs2 | Smart exact | mismatch | refusal | AEX Smart output/reject |
|---|---:|---:|---:|---:|
| seed1 before |134|0|166|287/13|
| seed1 baseline tuple gates off, ASan/UBSan |218|69|0 (13 uncompared)|287/13|
| seed1 after |171|0|129|287/13|
| seed5 before |127|0|173|283/17|
| seed5 after |172|0|128|283/17|

All campaigns disable shrinking, retaining identical seeded inputs while avoiding C04's documented timeout-cleanup issue. There are no framework errors. The largest baseline refused parameter group with an AEX output is Channel1/Mode2: 89 cases, of which 62 diagnostic exact and 27 diagnostic mismatch. Parameter groups are not claimed as root causes.

First divergence and original operation:

- Seed1/index281, PF32 1×7, Source Opacity5, has exact source, seed, five rays and glow. First composed difference is word18: AEX little-endian `770b4c3f`, Mac `780b4c3f`. Final output differs at word19/byte76, one word/one byte. The full-caller trace binds to the retained original public Smart worker.
- Original builder `18114e860`: source opacity is converted with `CVTDQ2PS` at `18114eb56`, multiplied by float constant `0x3c23d70a` at `18114eb65`, then stored at state+0x3c. Glow opacity uses the same sequence at `18114eb2b/18114eb3a`, stored at +0x38. The binary constant is `0.009999999776482582`. The port used double division by100 before its later float cast.
- The paired-trace scaffold previously constructed percentages by double division too. Its new opt-in `aex_percent_materialization` loads the original constant and mirrors these instructions. Historical F09 defaults remain reproducible. Every C07 trace must still bind independently to original public output; the source-reader fifth-argument ABI check runs first. No original numerical function is detoured.
- The corrected production trace matches all nine stages and final output. Both source/glow opacity reads share `ReadAlphaBoxOpacity`; Smart retains checkout order and applies conversion after its controlling fields are available.
- The recovered operation is bounded to Alpha, Strength100%, Mode1/2, approximation off. Smart admission additionally permits Source Opacity0–100% and Glow Opacity0–10000% for that tuple. All prior geometry, finite-SDR, layout, angle, gain, length, color/default-ramp and lifecycle guards remain. Classic admission and Gaussian admission are unchanged.

Rejected wider hypothesis and new boundary:

Applying float multiplication to every opacity read fails the strict arithmetic audit at historical corpus index7, PF32, Strength74%, Source73%, Glow9351%. There are58 changed samples, but sample321 does not move to exact (total differing words63→6). This experiment is not promoted. Restricting recovery to the proven unit-exponent scalar box pipeline gives140 audited route renders and546 changed samples, all now equal original Smart. This is a new upstream-dependency counterexample, not a reason to patch that sample. The full rejected record is retained in machine evidence.

Independent ASan/UBSan matrices:

- Source opacity {0,1,40,97,100}, three geometries (1×1,7×11,9×7), three depths, both box modes and both merges:180 cases. Before recovery162 exact/18 mismatch; corrected diagnostic180 exact.
- Glow opacity {0,1,40,97,100,101,1703,10000}, same axes:288 corrected diagnostic exact.
- Independent combined source/glow values, randomized SDR sources/colors, alternating default ramps, active directional rays and Highlight, odd byte strides:288 production exact. Source-zero/glow-zero and upper endpoints are included.

| Saved input | Fresh production Smart before→after |
|---|---|
| production index16 | refusal→exact |
| T06 shrunk42,104,115,125,165,251,281 | refusal→exact |
| other62 corpus inputs | same status and output bytes |

The70-input production audit is sanitizer clean. The separate140-route diagnostic audit changes546 samples only toward exact; historical T06 expectations remain historical. Production index16's full prior record is saved under `C07_opacity_expectation_update`; its new exact hash is `d01c07b8a2559a631314d580589f31e2d53afaf36b9307f5c425982a6b35b6c4`. Strict production replay is7/8 before explicit rebaseline and8/8 after. All oracle/Classic records remain unchanged.

The600 final Smart campaign routes are independently rebuilt with ASan/UBSan and checked against the ordinary campaign hashes/statuses. The25 fast tests pass; the existing compiled generic-beta sanitizer test passes its54 internal rows including HD in44.378s. Only the read-only SDK ROOT for that test is rebound to MAIN. `git diff --check` passes.

inference:

Paired exact upstream stages, original instruction order, and restoration of all composed words establish an opacity materialization cause in the admitted scalar branch. The non-unit-strength counterexample shows that correcting one later boundary can expose unresolved upstream error. These finite CPU-emulation/fake-host results do not establish native Windows UCRT/AE, arbitrary HDR, custom ramps, ROI/downsample or all inputs.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/summarize_kirakira_smart_C07.py`
- `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000016.json`
- `reports/fuzz/olmkirakira_smart_C07_opacity.json`
- `orchestra/reports/C07-kira-smart-r2-opacity.md`
- `orchestra/reports/C07-kira-smart-r2.md`

verify:

Run at this cluster commit. All logs, builds and corpora stay in ticket scratch.

```sh
s="$PWD/orchestra/state/C07-kira-smart-r2/recheck-opacity"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 81a91efd:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 5; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/before-seed$seed.json" --corpus "$s/before-seed$seed-corpus" > "$s/before-seed$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/after-seed$seed.json" --corpus "$s/after-seed$seed-corpus" > "$s/after-seed$seed.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 5 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
for family in source-opacity glow-opacity opacity-combined; do
  python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
"$py" tools/emulation/probe_kirakira_smart_C07.py --source "$s/before.cpp" --gate-off --campaign-seed 1 --trace-index 281 --scratch "$s/trace-before" --report "$s/trace-before.json" > "$s/trace-before.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --campaign-seed 1 --trace-index 281 --require-exact --scratch "$s/trace-after" --report "$s/trace-after.json" > "$s/trace-after.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
```

Expected: campaign table above,600 sanitized routes and70 corpus comparisons pass,180+288+288 matrix exact, bound trace composed→no divergence, replay8/8. For the fixed-admission arithmetic audit, create a scratch copy of this commit's source changing only `IsAlphaBoxTuple(info, format, true, true)` back to `IsAlphaBoxTuple(info, format, true)`, then run `audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --after-source <scratch-copy> --scratch "$s/samples" --report "$s/samples.json"`. Expected140 routes and546 samples toward exact. The originally measured `opacity-bounded.cpp` has identical arithmetic and the old admission.

next:
- Continue C07 with the remaining non-unit Alpha Strength cluster; keep Length1 Gaussian excluded.
- The wider-opacity corpus index7/sample321 boundary must be closed upstream before expanding this rule.
