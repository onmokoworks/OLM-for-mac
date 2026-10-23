status: done

summary:
- Recover unordered-alpha rejection in the original four-component aggregator; admit finite PF32 color box inputs.
- Seed1 Smart284/0/16 →285/0/15; fresh seed24 282/0/18 →283/0/17.
- Initial independent matrix756 exact/108 mismatch becomes864/864 exact; boundary54 exact and12 negative refusals.
- All previous exact outputs persist;600 sanitized campaign renders/70 corpus cases pass; one saved refusal→exact.

facts:

Base `dc116dbc`. AEX/F32 identities are unchanged from the brightness report. Independent conditions use the existing parameter generator, original public Smart reference and ASan/UBSan Mac build. All campaigns n300/jobs1/no shrinking.

The first gate-off counterexample is finite-color-box/index3119, Channel3,1×9, box Mode2. Final3 words differ; first ARGB word29 original `0000803f`, Mac `00000000`. Seed is exact. Ray0/1/4 differ23/10/26 NaN words and zero finite/NaN-boundary words. Glow first differs at word0, original0 versus MacNaN;27 glow words differ. This refutes unrestricted admission of the old arithmetic and supplies a new boundary.

Original aggregation18114f020 has `18114f152 COMISD xmm1,xmm7` followed by `18114f156 JBE 18114f1c5`: unordered alpha skips contribution. Old C++ `alpha <= 0.001` instead passes NaN. Changing the predicate to `!(alpha > 0.001)` restores the original ordered branch, retaining the double threshold. No coefficients, filter arithmetic or output samples are patched. Finite source extremes can produce NaN filter alpha through overflow.

The import-free original aggregator probe checks20 alpha patterns, including threshold-adjacent floats, signed zero, subnormals, finite extrema, infinities and quiet/signaling NaNs. It verifies skipped outputs are all zero and alpha1 produces the expected four-component unit case. Initial probe setup omitted the unused ramp argument, faulting at18114f130; disassembly established stack offsets+0x30 normalizers/+0x38 output and the corrected ten-argument ABI passes. That harness error supplied no numerical evidence.

After the fix, public-bound index3119 has exact composition/final output. Intermediate ray NaN differences persist; glow now differs only4 NaN sign words, zero other differences. Source/seed and every finite/NaN boundary match. Public-bound campaign seed1/index52 matches all paired stages. Per-helper trace dumps have interleaved-versus-planar shapes for color, so those helper comparisons are retained as non-exact and are not used to assert a first numerical divergence.

| Check | Before | After |
|---|---|---|
| Seed1 Smart E/M/R |284/0/16|285/0/15;52 improved|
| Seed24 Smart E/M/R |282/0/18|283/0/17;245 improved|
| Independent finite color864 |756 exact/108 mismatch gate-off|864 exact production|
| Boundary54 |not promoted|54 exact|
| Nonfinite negative12 |refusal|refusal|

Final600 Smart sanitizer replays reproduce campaign hashes and every previous exact output; all600 Classic result objects are unchanged. Guarded F32 corpus70 has one refusal→exact (T06 seed1/index52),69 unchanged. Both-route sample audit140 has0 changed samples.26 fast tests pass; compiled54-row sanitizer test passes (45.782s).

T06 saved matches39/62 →38/62 before migration →39/62 after migration. The23 discrepancy paths are identical to the baseline set, verified against the complete recorded replay and current saved results. Only `seed1_case000052_cdd504885120.json` changes, refusal→exact; raw SHA256 `374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb`. Input, reductions and prior result/provenance history are preserved. Production saved replay8/8 passes. The inherited23 failures are not claimed green. Machine evidence is `reports/fuzz/olmkirakira_smart_C38_color.json`.

inference:

The recovered unordered branch explains the counterexample and all108 initial matrix mismatches. Finite PF32 color admission remains bounded by the existing box tuple, full-frame/layout/ramp/work restrictions. This is original-AEX CPU-emulation evidence, not native AE/UCRT proof. Raw intermediate NaN identity is not claimed. No still-host math first divergence was observed. The refuted admission hypothesis yielded a new boundary; the ticket stop condition was not triggered.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py` (color families; classify NaN-only differences at all paired stages)
- `tools/emulation/probe_kirakira_color_alpha_C38.py`
- `reports/fuzz/olmkirakira_smart_C38_color.json`
- One T06 corpus expectation, this report and ticket summary.

verify:

Use the brightness report's campaign/audit/sample/replay commands with base revision `dc116dbc`, seeds `1 24`, and separate scratch `orchestra/state/C38-kira-smart-r9/recheck-color`. Expected campaign counts above. The exact matrix/trace commands are:

```sh
s="$PWD/orchestra/state/C38-kira-smart-r9/recheck-color"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/emulation/snapshot_kirakira_C34.py --revision dc116dbc --scratch "$s/base" > "$s/snapshot.log" 2>&1
for seed in 1 24; do
 python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/base/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus$seed" > "$s/before-$seed.log" 2>&1
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus$seed" > "$s/after-$seed.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/base/before.cpp" --campaign-dir "$s" --seeds 1 24 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/base/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
python3 tools/emulation/probe_kirakira_smart_C07.py --family finite-color-box --source "$s/base/before.cpp" --gate-off --scratch "$s/gate" --report "$s/gate.json" > "$s/gate.log" 2>&1
for family in finite-color-box finite-color-boundary; do
 python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family finite-color-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/probe_kirakira_color_alpha_C38.py --aex '/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/OLMKiraKira.aex' --report "$s/leaf.json" > "$s/leaf.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --family finite-color-box --trace-index 3119 --ucrt-math --require-exact --scratch "$s/trace3119" --report "$s/trace3119.json" > "$s/trace3119.log" 2>&1
"$py" tools/emulation/probe_kirakira_smart_C07.py --campaign-seed 1 --trace-index 52 --ucrt-math --require-exact --scratch "$s/trace52" --report "$s/trace52.json" > "$s/trace52.log" 2>&1
```

Expect gate756/108; production864+54 exact; negative12 refusals; leaf20 pass; both traces public_bound=true.3119's stage_nan_differences must have other=0 throughout, composed exact. To reproduce its original failure add `--source "$s/base/before.cpp" --gate-off`, remove `--require-exact` and use separate scratch/report. Fast/compiled sanitizer commands follow C34 with ticket-local scratch.

next:
- Two clusters closed. Next: finite Alpha Gaussian/approximation (seed1/index179,272).
