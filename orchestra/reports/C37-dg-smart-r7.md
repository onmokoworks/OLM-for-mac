status: partial

summary:
- Closed scalar Bilateral Power admission; no rendering arithmetic changed in cluster 1.
- Seed1 remains 290 exact / 0 mismatch / 3 refusal / 7 uncompared, all prior exact bytes preserved.
- Fresh seed37 case73 improves refusal→exact; independent300 exact, negative8 unchanged refusals, sanitizer equality throughout.
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
