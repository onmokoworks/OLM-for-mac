status: done

summary:
- Closed non-unit scalar Alpha Strength for Smart box modes, including zero Strength and its opacity interaction.
- Seed1 improves171/0/129→197/0/103; fresh seed5 improves172/0/128→193/0/107 (exact/mismatch/refusal).
- Previous exact Smart and all Classic campaign records remain identical;600 sanitized production routes pass.
- Two independent288-case production matrices pass;140 corpus route comparisons change264 samples only toward exact.
- Ten historical corpus inputs change refusal→exact; production expectations need no update and strict replay remains8/8.

facts:

Base `7db468f4`. Machine evidence: `reports/fuzz/olmkirakira_smart_C07_strength.json`. Original AEX/retained worker identities and untouched MAIN/external-worker restrictions remain as recorded in the opacity report. No worker rebuild or dependency installation.

| n300/jobs2 | Before E/M/R | After E/M/R | AEX Smart output/reject |
|---|---|---|---|
| seed1 |171/0/129|197/0/103|287/13|
| fresh seed5 |172/0/128|193/0/107|283/17|

Remeasuring the first-cluster source with final tuple gates off gives222 exact/65 mismatch/13 uncompared on seed1. All final production campaign records are independently replayed with ASan/UBSan (600 routes), matching ordinary builds. No admitted case lacks an original output.

First divergences and operations:

- Seed1/index24, PF32 50×34, Strength201: source matches, then seed word11 differs, AEX little-endian `c8d0b03b`, Mac `c7d0b03b`;57 seed words differ. Final output differs at28 words, first word1697 `1ff92b3f` versus `20f92b3f`. The trace binds to public Smart. Builder `18114e8d8/18114e8e7` converts integer Strength to float and multiplies by float0.01, storing at state+8. Preserving that float exponent restores all stages of this witness.
- Independent Strength0 exposes the original lower clamp: double constant `181489990`, bytes `fca9f1d24d62503f`, is0.001; replacement float `181488a60`, bytes `6f12833a`, is0.0010000000474974513. `18114edf0` selects it before `powf`. The port used1e-6. Percentage-only recovery leaves seed word0 AEX `a5fd7f3f`, Mac `ffff7f3f`; first final PF8 differing byte1 is `aa` versus `8f`.
- The recovered branch uses that float clamp and float `powf`. It retains directly loaded Brightness Gain at Strength0; the former127/255 fallback is excluded from this branch. Original caller gain comes from state+0x608 independently of exponent, as traced in C04/F12. Strength0 then matches all nine stages and final output.
- Independent index166, PF32 7×11, Strength537: corrected exponent plus double `pow` still differs at seed word16, AEX `5fb47f3f`, Mac `60b47f3f`. Final output differs at15 words/16 bytes; first word8 `fedd443f` versus `ffdd443f`. The float overload restores all nine stages and final output.
- The historical Python scaffold uses `math.pow` even for `powf`. At index166 it agrees with the incorrect double-pow port but **does not bind** to the public worker. That trace is retained but is not first-divergence evidence. Read-only retained worker `guest/crates/aex-guest-worker/src/x64/imports.rs:2685` installs `f32::powf`. The new opt-in host-float-powf trace import restores public binding and exposes the seed difference above. This is a host math substitution, not native Windows UCRT proof. Neither worker nor original numerical AEX functions were changed.
- Once its scalar seed is recovered, PF8 Alpha box aggregation uses the original reciprocal plus three multiplies for non-unit Strength too. Both opacities use the original float percentage operation. Color, Gaussian and approximation pipelines retain their boundaries.

`UsesRecoveredAlphaBoxPipeline` selects Alpha/Mode1-or2/no approximation. `ReadAlphaBoxPercent` handles Strength and both opacities while preserving Smart checkout order. Smart alone admits Strength0–1000% plus the already-proven opacity ranges. Full-frame/layout/finite-SDR/angle/length/gain/default-ramp guards remain. Classic/Gaussian admission remains unchanged. No expected pixel, coordinate or case index appears in production code.

Rejected candidates: percentage-only recovery fails Strength0 (new clamp/scale boundary). Strength recovery without its related opacity operation fails corpus7:6 samples change, but321/362 are not exact. Recovering both resolves this dependency. Double-pow candidates fail independent166 in both plain and combined-opacity matrices (15/7 final differing words); the float-powf trace resolves it. Each rejection supplies a concrete new value or boundary; the no-new-boundary stop condition was not reached.

Independent ASan/UBSan production matrices:288 cases across1×1/7×11/9×7, PF8/16/32, modes1/2, merges1/2 and Strength{0,1,40,97,100,101,537,1000}; randomized SDR sources/colors, active directional/Highlight rays and odd byte strides. Another288 mix source/glow opacity and default ramps. All576 are exact; corrected gate-off matrices also pass288+288.

| Corpus inputs | Fresh production Smart before→after |
|---|---|
| T06 shrunk7,24,29,45,77,81,142,160,260,280 | refusal→exact |
| other60, including all8 production inputs | unchanged status/output |

The70-input production audit is sanitized. The separate140-route arithmetic audit changes264 typed samples, all equal original Smart afterward. This includes the formerly excluded non-unit PF8 family. T06 expectations remain historical; production strict replay is8/8 without updates. The25 fast tests pass; existing compiled generic-beta ASan/UBSan test passes54 internal rows including HD in43.961s. `git diff --check` passes.

inference:

The scalar branch needs a consistent control/seed/normalization pipeline; isolated opacity/exponent fixes exposed unresolved dependencies. Float powf now matches the retained emulator's import and measured public outputs, but native Windows powf remains a separate dependency question. These probes do not establish arbitrary native AE/UCRT, HDR/nonfinite, ROI/downsample, custom ramps or other channel constructors.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/summarize_kirakira_smart_C07.py`
- `reports/fuzz/olmkirakira_smart_C07_strength.json`
- `orchestra/reports/C07-kira-smart-r2-strength.md`
- `orchestra/reports/C07-kira-smart-r2.md`

verify:

At this cluster commit:

```sh
s="$PWD/orchestra/state/C07-kira-smart-r2/recheck-strength"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 7db468f4:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 5; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/before-seed$seed.json" --corpus "$s/before-seed$seed-corpus" > "$s/before-seed$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/after-seed$seed.json" --corpus "$s/after-seed$seed-corpus" > "$s/after-seed$seed.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 5 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
for family in strength strength-combined; do
  python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
for index in 0 166; do
  "$py" tools/emulation/probe_kirakira_smart_C07.py --family strength --trace-index "$index" --require-exact --scratch "$s/trace-$index" --report "$s/trace-$index.json" > "$s/trace-$index.log" 2>&1
done
"$py" tools/emulation/probe_kirakira_smart_C07.py --source "$s/before.cpp" --gate-off --campaign-seed 1 --trace-index 24 --scratch "$s/trace-before" --report "$s/trace-before.json" > "$s/trace-before.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
```

Expected: campaign table,600 sanitized routes/70 corpus inputs,288+288 exact,140-route sample audit/264 samples toward exact, final traces public-bound/all nine stages exact, before case24 first divergence seed, replay8/8. To reproduce double-pow rejection, copy this source into scratch and replace only `std::pow(p.a, (float)exponent)` with `(float)std::pow((double)p.a, exponent)`, then pass it to `probe_kirakira_smart_C07.py --source <copy> --gate-off --family strength --trace-index 166`; expected bound seed difference at word16 and15 differing final words.

next:
- Largest successful-oracle refusal group: Alpha Mode2 HDR10 and signed9. Investigate input-domain admission with independent finite/extreme values; preserve nonfinite/negative-alpha counterexamples.
- Gaussian Length1, approximation, four-channel seeds and other scalar constructors remain separate.
