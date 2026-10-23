status: done

summary:
- Recover four-component box seeds/rays/aggregation for the shared Channel 3/5/6 constructor.
- Seed 1 improves 229/0/71 → 248/0/52; seed 8 improves 221/0/79 → 243/0/57.
- No previous exact Smart or Classic campaign result changes; final-source sanitizer/corpus verification passes.

facts:

Base: `bd1f5ece`. Ranked after the scalar closure, Channel 6/Mode 2/SDR is the largest remaining successful-oracle refusal group (8 seed-1 cases). Channel 3/5/6 share original constructor `18114eed0` → `18114ef10`, as selected by all three typed owners. The initial experiment uses this constructor without changing any admission.

The first planar hypothesis recovered the RGBA seed but incorrectly reused normalized scalar box passes and scalar-style aggregation. Seed 1/index 41, PF8 20×15, is public-bound: source/seed exact, first ray word AEX `f3bcad43` versus candidate `a0ab013e`; 1,068 final samples differ. Original helper pass maxima progress 1 → 10.101961135864258 → 112.63922119140625 → 1505.62744140625. This is a new first-filter boundary, not evidence for output rescaling.

Original static/runtime facts:
- `18114ef10` allocates four float channels: powf(R,strength+1)×A, powf(G,strength+1)×A, powf(B,strength+1)×A, A. No scalar exponent clamp or Fade operation belongs to this constructor.
- `18114f4a0` / `181150790` pass normalize=false for the color owner. Each pass stores the unnormalized FLOAT64 sum narrowed once to FLOAT32. `1812d6690` receives channels=4; its direct/sliding double summation matches independent planar channels.
- `18114f020` takes per-ray normalizers separately: directional Length (Mode 1) or Length×integer(Length²) (Mode 2); Highlight kernel-area (Mode 1), or FLOAT32 area squared then squared again (Mode 2). At index 41 the recorded values are 2744,0,0,0,78310981632. These are constructor/helper coefficients, not fitted image corrections.
- Color aggregation ignores per-ray colors/ramps, tests alpha against double 0.001, uses 1/alpha, clamps alpha×reciprocal-normalizer, accumulates RGB with Brightness Gain, adds alpha, clamps total alpha and normalizes RGB. It is distinct from scalar normalized-union aggregation.
- The second diagnostic implements unnormalized operations within every pass. At index 41 source, four-component seed, all five rays, glow, composed and final output become exact and bind to public Smart. The original AEX and worker hashes remain those in the luminance report.

Diagnostic independent matrices: 288 exact control combinations and 48 exact length/alias conditions under ASan/UBSan. The latter spans 1,2,3,5,7,15,50,1000 directional lengths, Highlight through 500, all three depths, both box modes/merges, Channels 3/5/6, gains through 100, strengths through 1000 and rotations. Final production matrices also pass 288 + 48 exact conditions. Core `highlight_isotropic_box_blur` gains a default-true normalize argument, preserving its old callers; four-component processing passes false. No normalized result is multiplied afterward to simulate sums.

The production rule admits only finite SDR full-frame box input with existing controls, layout and default-ramp restrictions. Gaussian and approximation representation changes remain excluded. A final source narrowing preserves their earlier diagnostic behavior; all 600 sanitized campaign outputs are checked against the ordinary candidate hashes. No corpus expectation is rewritten by the verification tools.

Final verification: 600 sanitized campaign routes and all 70 corpus inputs pass. Strict production replay is 8/8; no production expectation changes. Existing tests: 25 fast tests and the 54-row generic sanitizer test pass (44.492 seconds). Final case-41 trace is public-bound with every full plane exact. The diagnostic helper trace names still represent scalar component calls on the Mac side, so their shapes are not claimed paired to the interleaved AEX helper; source/seed/ray/glow/full output planes are compared in interleaved order.

| Corpus | Before → after | Saved expectation action |
|---|---|---|
| production 8 | identical bytes/status | none |
| historical 62, both routes | 4,800 changed samples, all toward exact | historical diagnostics retained |
| all other samples | unchanged | none |

Changed historical indices: 19,41,52,61,62,73,76,108,129,136,157,187,208,262,288. This includes shrunk diagnostic inputs whose parameters differ from campaign inputs with the same index. Full sample audit: 140 route replays, zero changes away from exact.

inference:

Shared original constructors and independent channel/length controls support one four-component operation cluster. The planar implementation follows per-component sums; the observed original RowSum dispatch and full-plane comparisons support it over the measured domain. It does not establish every floating input, nonfinite filtering, native AE/UCRT, Gaussian or IPP resizing.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `core/kirakira_highlight.h`
- `tools/emulation/probe_kirakira_color_C16.py`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `reports/fuzz/olmkirakira_smart_C16_color.json`
- `orchestra/reports/C16-kira-smart-r4-color.md`
- `orchestra/reports/C16-kira-smart-r4.md`

verify:

Use the luminance report's shell setup, a new scratch subdirectory, and base `bd1f5ece` to reproduce before/after seed 1/8 campaigns and the sanitizer/corpus auditors. Use `--jobs 1` throughout. Replace the independent family with `color-controls` and `color-lengths`; expected 288 and 48 exact respectively. Public trace:

```sh
"$py" tools/emulation/probe_kirakira_smart_C07.py --campaign-seed 1 --trace-index 41 --require-exact --scratch "$s/trace41" --report "$s/trace41.json" > "$s/trace41.log" 2>&1
```

Reproduce the two diagnostic hypotheses without editing production:

```sh
git show bd1f5ece:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
python3 tools/emulation/probe_kirakira_color_C16.py --source "$s/before.cpp" --output "$s/planar.cpp"
python3 tools/emulation/probe_kirakira_color_C16.py --source "$s/before.cpp" --unnormalized --output "$s/sums.cpp"
for variant in planar sums; do
  "$py" tools/emulation/probe_kirakira_smart_C07.py --source "$s/$variant.cpp" --gate-off --campaign-seed 1 --trace-index 41 --keep-trace --scratch "$s/$variant-trace" --report "$s/$variant-trace.json" > "$s/$variant-trace.log" 2>&1
done
```

Expected normalized planar: public-bound first divergence ray0, 1068 differing final samples. Unnormalized sums: public-bound, all paired stages/output exact. No four-channel body is patched in the AEX.

next:
- Investigate Channel 4 scalar maximum/box controls (six SDR seed-1 refusals across both box modes), then the remaining Gaussian/approximation/nonfinite groups.
