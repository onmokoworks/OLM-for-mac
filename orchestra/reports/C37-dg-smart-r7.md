status: partial

summary:
- Closed two admission clusters: scalar Bilateral Power and finite radius-one Bilateral.
- Seed1 remains 290 exact / 0 mismatch / 3 refusal / 7 uncompared, all prior exact bytes preserved.
- Fresh seed37 cases73/22 improve refusal→exact; independent300+1944 exact, negative8+6 unchanged refusals, sanitizer equality throughout.
- Corpus145 remains exact without expectation edits. Other Bilateral domains remain under investigation.

facts:
- Starting commit `7f9c2ae051394482a2eae609ccca838e63dd67a8`, branch `orch/C37-dg-smart-r7`. Read AGENT_GUIDE, GOTCHAS, plugin ledger row, compatibility plan and T07/C03/C08/C14/C19/C27/C31/F10/F12 reports. MAIN, original emulator sources and retained workers are read-only.
- F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`; AEX SHA256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`. Public CPU Unicorn/SDK-shim evidence, not native AE certification.
- Re-measurement uses requested seed1 n300 jobs1 with shrinking disabled to avoid unrelated Classic reduction. Completed: Smart290/0/3/7, original290 success/8 rejection/2 wall timeout. Compared all290 exact result dictionaries/input hashes to C31 final evidence: identical.
- Seed1 residuals31/53/55/108/120/189/192/246: original OpenCV medianBlur assertion `src.depth() == CV_8U`;10/90: original wall timeout. All3 Mac refusals53/189/192 have rejected originals. No seed1 AEX-rendered refusal remains.
- Fresh seed37 n300: Smart279 exact/0 mismatch/10 refusal/10 uncompared/1 budget; original286 success/14 rejection. The10-second Mac timeout is not counted as exact or sanitizer-clean in this initial campaign.
- Largest AEX-rendered refusal family is Bilateral:22 (signed, radius0),25 (SDR, radius12),73 (Power0.01, radius14),199 (HDR, radius988). Additional Box refusals3/288 have sizes3703/2025; existing bounds were not changed.
- Scratch gate-off original22/25/73:22 and73 exact,25 mismatch; all3 sanitizer-identical. Case25 first output byte0/word0 original `acc6e83e`, candidate `aaaaaa3e`;9982 bytes/2924 words differ. Gate-off is diagnostic only.
- Cluster1 case73 takes the already-grounded scalar shape (19x7, radius14). The existing UCRT Power admission copy excludes Bilateral scalar only at the final profile guard. Reusing that same admission copy for this guard retains actual Power rendering, finite SDR source checks, exponent[0.01f,5.0f], radius[3,32], small-image shape, and all layout/lifecycle bounds.
- Independent300 public-original cases: all exact and ASan/UBSan-identical. Geometries/radii7x1/3,1x7/3,7x3/4,19x7/14,17x9/32; all ownership/RGB-or-Layer/background states, inversion variation, exponent0.01/neighbors-of-one/2.25/5, odd padding. Eight boundary controls (out-of-range exponents, radius2/33, infinity, NaN, mask overflow, extended RGB) remain unchanged refusals with sanitizer equality.
- Before/current/sanitized verifier completed all600 campaign cases and145 corpus cases with strict refusal→exact-only changes. Seed1:290 unchanged exact/10 unchanged nonexact. Seed37:280 unchanged exact/19 unchanged nonexact/1 newly exact(case73). The longer180-second render allowance resolves the initial Mac timeout at both revisions; this extra unchanged exact is not credited to the code change. Leak detection disabled.

- Existing beta tests:9 run, OK (17.407s), including their compiled sanitizer coverage. `git diff --check` passes.

| Smart corpus | Before | After | Expectation edits |
|---|---|---|---|
| Saved145 |145 exact|145 exact, identical bytes/status|None|

inference:
- Scalar Bilateral Power refusal was an obsolete admission restriction after UCRT integration. Independent public rendering supports only the existing scalar shape/radius domain; the radius-one Power branch and larger vector-filter shapes are separate.
- Original assertions/timeouts provide no comparable output and do not justify a Mac numerical change. The remaining effective-filter refusal domain is not established exact by this change.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/fuzz/probe_distancegradation_C37.py`
- `tools/fuzz/summarize_distancegradation_C37.py`
- `reports/fuzz/olmdistancegradation_C37_power.json`
- `orchestra/reports/C37-dg-smart-r7.md`

verify:
Run from this worktree; redirect long command output into scratch logs. Each command below has been executed; expected results are listed above. The helper's other experiment modes are diagnostic, not production promotions.
```sh
s="$PWD/orchestra/state/C37-dg-smart-r7"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s"
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$s/base" --corpus "$s/corpus" --report "$s/base.json"
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 37 --jobs 1 --shrink-attempts 0 --scratch "$s/fresh" --corpus "$s/fresh-corpus" --report "$s/fresh.json"
python3 tools/fuzz/probe_distancegradation_C37.py --mode power-scalar --scratch "$s/power" --report "$s/power.json" --write-source "$s/power.cpp" --require-exact
python3 tools/fuzz/probe_distancegradation_C37.py --mode power-scalar --negative --scratch "$s/power-negative" --report "$s/power-negative.json"
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 7f9c2ae --candidate-source "$s/power.cpp" --campaign "$s/base.json" --campaign "$s/fresh.json" --corpus --strict-admission --case-timeout 180 --scratch "$s/power-verify" --report "$s/power-verify.json"
mkdir -p "$s/bin"
ln -sf "$PWD/tools/ucrt_cxx.py" "$s/bin/clang++"
PATH="$s/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py'
git diff --check
```
Campaign reruns on promoted source measure current counts; the committed evidence preserves original results. Machine-load-dependent timeouts must be reported separately.

next:
- Continue finite-input radius-one Bilateral matrix and generic-radius first-stage investigation. No production gate or work budget is relaxed for these pending domains.

Cluster 2 — finite radius-one Bilateral (base `99b73247`):

facts:
- Re-measured seed1 after cluster1:290/0/3/7. All300 Smart result dictionaries remain identical to the initial campaign, not just the exact count.
- Gate-off seed37 case22 (15x4, signed samples, Linear, Bilateral Size0) equals the original output with sanitizer equality. Radius0 is the original effective radius1 operation, already restored by C14/C27.
- General input-domain rule now permits finite extended samples through the existing radius-one Bilateral admission predicate. Positive mask-conversion overflow and nonfinite samples remain refused; Power and larger Bilateral radii retain their previous source-domain guards. No output arithmetic or filter dispatch changes in this cluster.
- Independent1944 cases all change refusal→exact and are sanitizer-identical. Nine finite profiles include signed/HDR RGB and alpha, uniform masks, maximum finite RGB/negative alpha, mask-conversion edge8421504, subnormals/cutoff neighbors;7x1/1x7/17x9 geometries; all ownership/RGB-or-Layer/background states; Constant/Linear/Sphere; Size0/1; odd padding. Both source pattern geometries from the existing C14 matrix are retained.
- Six unchanged-refusal controls:Power2.25, radius2, effective Median, infinity, NaN and positive mask overflow. Negative controls test admission only and intentionally do not invoke an original that supplies no required reference.
- All600 campaign and145 corpus before/current/sanitized comparisons pass. Seed1:290 unchanged exact/10 unchanged nonexact. Seed37:281 unchanged exact/18 unchanged nonexact/1 newly exact(case22). This is the180-second verification reference set; initial10-second timeout201 is separately accounted for above. Corpus145 remains byte/status-identical and exact; no rebaseline edits.
- Existing beta tests:9 run, OK (16.687s). No sanitizer diagnostic or disagreement. `git diff --check` passes.

| Cluster2 Smart corpus | Before | After | Expectation edits |
|---|---|---|---|
| Saved145 |145 exact|145 exact, identical bytes/status|None|

inference:
- The finite-source restriction was conservative after ownership/mask and radius-one filter repairs. This promotion reuses those general operations; it does not justify nonfinite effective filters, larger-radius extended inputs or Power source-domain promotion.

changed_files (cluster2):
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/fuzz/probe_distancegradation_C37.py`
- `reports/fuzz/olmdistancegradation_C37_finite.json`
- `orchestra/reports/C37-dg-smart-r7.md`

verify (additional executed commands):
```sh
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$s/after-power" --corpus "$s/after-power-corpus" --report "$s/after-power.json"
python3 tools/fuzz/probe_distancegradation_C37.py --mode finite-bilateral --scratch "$s/finite" --report "$s/finite.json" --write-source "$s/finite.cpp" --require-exact
python3 tools/fuzz/probe_distancegradation_C37.py --mode finite-bilateral --before-ref 99b73247 --negative --scratch "$s/finite-negative" --report "$s/finite-negative.json"
```
For the combined cluster1+2 source, the executed generation was `candidate(SOURCE.read_text(),'finite-bilateral')` from `probe_distancegradation_C37` while HEAD was99b73247, written to `$s/finite-final.cpp`. Reproduce it by adding `--before-ref 99b73247 --write-source "$s/finite-final.cpp"` to the independent matrix command (same domain and expected1944 exact).
```sh
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref 99b73247 --candidate-source "$s/finite-final.cpp" --campaign "$s/base.json" --campaign "$s/fresh.json" --corpus --strict-admission --case-timeout 180 --scratch "$s/finite-verify" --report "$s/finite-verify.json"
PATH="$s/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py'
```
Expected:only seed37 case22 changes in this verification; corpus145 unchanged; tests9 pass.

next:
- Generic-radius scalar/vector candidate has passed its independent matrix and import-free IPP leaf check; full campaign regression and negative admission checks are pending. No existing work budget has changed.
