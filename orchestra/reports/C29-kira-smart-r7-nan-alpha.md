status: done

summary:
- Restore height-one ColumnSum state and FilterEngine's four-row call boundaries.
- Admit finite-source Alpha box tuples with canonical NaN seeds; retain infinite-seed and nonfinite-source rejection.
- Seed1 Smart272/0/28 →274/0/26; fresh seed18 274/0/26 →276/0/24.
- Preserve previous exact outputs;562 independent production conditions and600 sanitized campaign renders pass.

facts:

Base `d94b33a6`; worker/AEX identities unchanged from the scalar Highlight report. Machine evidence: `reports/fuzz/olmkirakira_smart_C29_nan_alpha.json`. All campaigns n300/jobs1/no shrinking, ticket-local scratch/corpora. Seed1 admissions89,299; seed18 admissions46,262. Original output/reject287/13 and288/12, respectively.

Census of the five successful-oracle non-SDR box refusals:
-39: first seed difference is invalid-op NaN sign (`0000c0ff` original, `0000c07f` Mac),52 words. Skip as F38 instructed; no sign correction was added.
-52: first complete-plane difference ray3, original NaN versus finite Mac. Four-component admission remains outside this cluster; per-component Mac helper dumps do not align with original interleaved helper dumps.
-86: all paired stages/output exact with the gate off; finite-HDR Max admission remains follow-up work.
-89: source, seed and forward warp exact; first box output word227 is original `0000c0ff`, Mac `aff59c3d`.75 first-pass words and36 final words differ.
-299: all stages/output already exact with the gate off, refused by the former finite-seed check.

Original RowSum<float,double> `18127f3c0` matches the port's direct3/5-tap and other sliding sums. Original ColumnSum<double,float> `1812d1d70` adds each incoming row to SUM, writes the scaled total, then subtracts the outgoing row. Its ksize1 sumCount stays0, causing SUM to clear on every call. The previous port omitted this algebraically redundant column operation, losing NaN propagation.

A persistent-column diagnostic reduces case89's final difference to13 words but is refuted at first-pass word302: original `3a0b0d3e`, candidate `0000c0ff` (38 first-pass words differ). This is a new boundary at row12 of the25-wide workspace. Entry hooks then record kernel1, sumCount0 and rows `[4,4,4,4,4,4,1]` for each of the three directional passes. Applying the same ColumnSum state independently to each four-row FilterEngine batch makes every paired stage and final output exact. This is operation/call-state recovery applied to every row and column, not an expected-value or coordinate exception. The refuted persistent-state proposal is reproducible with `kirakira_column_persistent_C29.patch` on this cluster's base source.

The final source accepts finite PF32 source components when the Alpha powf seed is finite or canonical NaN; infinite seeds still refuse. Only the existing non-approximated Alpha box tuple reaches this source rule. Input NaN/Inf, other channels and Gaussian retain their prior source restrictions. The seed computation itself is unchanged UCRT FMA powf. No NaN sign override was introduced.

| Check | Measured result |
|---|---|
| Initial gate-off signed/HDR/extreme matrix |288 exact, including23 outside the final non-infinite-seed domain|
| Gate-off length/rotation/Highlight matrix |265 exact, sanitizer clean|
| Final production matrices |265 source +265 lengths +32 opacity =562 exact, sanitizer clean|
| Final unsupported input/overflow tests |5 refusals, sanitizer clean|
| Final campaign audit |600 Smart sanitizer renders, all equal ordinary campaign hashes|
| Previous exact Smart / all Classic campaign results |all unchanged at both seeds|
| Production8 saved replay |8/8, no rebaseline|
| Both-route corpus sample audit |140 route comparisons;26 changed samples, all toward exact;0 away|
| Guarded Smart corpus audit |70 cases, unchanged or refusal→exact only|
| Existing tests |25 fast tests +1 compiled54-row sanitizer test pass (44.753s)|

Final production traces indices89 and299 bind to F32 and have no divergent paired stage. Infinity exclusion is a domain boundary, not an inference that the23 gate-off infinity cases mismatch. The persistent-state hypothesis was refuted with a new boundary; the batched-state proposal passed. No two-refutations-without-new-boundary condition occurred.

inference:

The measured call boundaries, static ColumnSum state transition, independent matrices and fresh campaign support this finite-source Alpha/box domain. Arbitrary input NaN payloads, invalid-op sign work, color NaN-seed admission, finite-HDR Max, Gaussian NaN seeds, native AE and general host-math equivalence remain unproved.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `tools/emulation/fixtures/kirakira_column_persistent_C29.patch`
- `reports/fuzz/olmkirakira_smart_C29_nan_alpha.json`
- `orchestra/reports/C29-kira-smart-r7{,-nan-alpha}.md`

verify:

At this cluster commit, use the scalar report's complete command sequence with these substitutions:
- Base source revision `d94b33a6`; scratch `orchestra/state/C29-kira-smart-r7/recheck-nan`.
- Campaign seeds1 and18; expected Smart274/0/26 and276/0/24.
- Independent families `nan-alpha`, `nan-alpha-lengths`, `nan-alpha-opacity`:265,265,32 exact.
- Negative family `nan-alpha-negative`:5 refusals.
- Trace campaign indices89 and299 with `--ucrt-math`:public-bound/all stages exact.
- Run the same C04 audit, both-route F09 sample audit and strict8-case saved replay commands against the extracted before source. Expected sample changes26/away0.

The exact new-family commands are:

```sh
s="$PWD/orchestra/state/C29-kira-smart-r7/recheck-nan"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for family in nan-alpha nan-alpha-lengths nan-alpha-opacity; do
 python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family nan-alpha-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
git diff --check
```

next:
- Two clusters closed. Remaining largest parameter group is Approximation (four seed1 refusals); investigate its directional Gaussian owner.
- Keep case39 with F38. Preserve the color/HDR/nonfinite witnesses for follow-up without promoting them from final-byte equality alone.
