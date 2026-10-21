status: done

summary:
- Closed the scalar unit-strength Alpha tiny-Gaussian cluster for directional Length2–1000, with Highlight disabled.
- Smart seed1 improves 130/0/170 to 134/0/166; seed4 improves 128/0/172 to 131/0/169 (exact/mismatch/refusal).
- Three paired original/public/production-Smart witnesses move from first-ray divergence to all27 captured stages exact.
- Independent210 production cases,600 campaign replays and10 negative cases are sanitizer-clean; all prior exact outputs persist.
- Corpus changes only toward exact:10 changed diagnostic samples;3 production-Smart refusals become exact. Length1 remains excluded with a reproducible1-ULP counterexample.

facts:

Base: `e7f23f66`. Machine evidence: `reports/fuzz/olmkirakira_smart_C04_gaussian.json`. AEX/worker identities are unchanged from the main C04 report. It records before/after source and header bindings, complete transitions, matrices, paired traces, corpus audits, the excluded counterexample and the remaining refusal census. No MAIN/external-worker/other-plugin/ledger/release-gate changes, rebuild, push or installation.

Fresh paired traces of the retained shrunk1x1 witnesses (original full caller and typed writer, independently bound to original public Smart):

| T06 witness | Depth | Before first stage | Original / Mac ray0 word, little-endian | Final differing bytes before -> after |
|---|---:|---|---|---:|
| C30/index210 |16|ray0|`e338763e` / `0038763f`|2 -> 0|
| C31/index23 |32|ray0|`7500803e` / `0000803f`|4 -> 0|
| C32/index232 |8|ray0|`7500803e` / `0000803f`|3 -> 0|

Source and seed match before the first differing ray. These four-direction Length50 cases create5x5 helper workspaces. The old `mode3_gaussian_admitted` rejects them, and `RotatedAxisBoxBlur` returns its unblurred input. The AEX executes `181272ec0` GaussianBlur with horizontal kernel size derived from Length and sigma=Length/2. Restoring that operation removes every captured difference, without modifying coefficients, convolution arithmetic, aggregation, composition or output bytes directly.

After the change all nine stages per case—source, seed, five rays, glow, composed—match (27/27), and production Mac **Smart** binds to public original AEX:

- PF16/index210: `a940f4cfe4aa8575d8a1c07fc7c5a1ad5d4a1ab984ffda669c5548e2db476ab4`
- PF32/index23: `e57d5fa6aba4fddfcb4a97da8edd1ea39017201162c7f0a8a4eedd94341d8dc9`
- PF8/index232: `7b15f541883e3d6e3a9e2521432c29878d9df0f4c40beb69f7be4091ece0fd21`

Both before and after trace sets pass the import-free reader ABI check and bind their original full-caller output to the retained public worker. Retained TLS/allocator/CRT/Python-libm scaffolding is used; no numerical AEX body is detoured. The shrunk inputs above differ from unshrunk campaign inputs with the same indices.

General production change:

- Keep the historical Gaussian admission function intact. Add a separate scalar workspace predicate: width/height at least5 (the caller always adds at least4 to each positive source extent), Length2–1000.
- Use that additional operation only for unit-exponent Alpha with no Highlight. Unreconciled seed/Highlight pipelines retain their previous helper boundary. No image-coordinate/value/case exceptions are introduced.
- Smart admission uses the existing Alpha finite-SDR/control/color/default-ramp/angle rules, selects Mode3 with Highlight0 and requires each active directional Length>=2. Zero-length rays are skipped. Classic admission and all older exact/generic branches remain unchanged.
- A separate checked workload budget sums all four active Gaussian/warp workloads, including repeated border reflection. It retains the existing12-billion-work-unit and1-GiB ceilings. The conservative peak includes all retained frame planes, the largest three helper workspaces and kernel storage. Existing full-frame, source/layout, side/area and downsample caps remain.

| n300/jobs2 campaign | Smart exact | Mismatch | Refusal | Uncompared | AEX Smart output/reject |
|---|---:|---:|---:|---:|---:|
| seed1 before |130|0|170|0|287/13|
| seed1 operation fixed, tuple gates off |218|69|0|13|287/13|
| seed1 after |134|0|166|0|287/13|
| seed4 before |128|0|172|0|281/19|
| seed4 operation fixed, tuple gates off |225|56|0|19|281/19|
| seed4 after |131|0|169|0|281/19|

New admissions: seed1 indices23/201/210/232; seed4 indices30/208/289. All are exact with gates off and in production. The old130/128 Smart exact result records stay identical; no missing original output is admitted. Final independent ASan/UBSan replay checks all600 campaign routes against recorded input/parameter/padding bindings and output hashes. No sanitizer errors occur. Leak detection is disabled as in the earlier ticket tools.

Independent production verification:

- 180 cases:10 geometries x3 depths x6 ray patterns, directional lengths2/3/7/15/50/300, both merge modes across the matrix, colors/default ramps, gains/angles, independent edge/random source values and odd byte padding. All original-Smart exact under ASan/UBSan.
- 30 boundary cases:3 depths x5 raw angles x Length2/1000, all four directions active, angles including -2147483647 and2147483512. All original-Smart exact under sanitizers.
- 10 one-away cases cleanly refuse: unsupported channel/mode, approximation, non-unit strength/opacities, the excluded signed-angle endpoint, Length1, nonzero Highlight and PF16 above SDR. Ordinary host/layout limits are retained; the matrix is not native large-frame/ROI proof.

Rejected broader hypothesis and retained boundary:

The initial all-length candidate passed180 ordinary cases but failed the boundary matrix at PF32/index24,9x7, Mode3, all four directional lengths1, Highlight0, Rotation0, Alpha/Strength100. Exactly one float word differs: byte868/word217, original `5cf1563f`, Mac `5df1563f`. Input SHA256: `c3cc70ed4a7d57f6c836e5ae6d4fe5ce872d83595b3c6ffd24b5b588f58677b9`. This is a new observed boundary, not a second refuted hypothesis without new values.

Length1 selects the separately implemented five-tap optimized row path (`prepare_actual_aex_small5_nonfused`), whereas Length>=2 uses the generic row path. This motivates the general branch boundary; the exact internal cause of that one-word residual is **not established** here. The final production rule refuses the witness cleanly. The committed `gaussian-length1` generator reproduces its original bytes/settings: gate-off retains exactly the same mismatch; production retains refusal, both under sanitizers. Its verifier reports the expected diagnostic status explicitly; that PASS is not an exact-output claim. No failing case is promoted or corrected by an expected-value adjustment.

Corpus before/after:

| Saved input | Smart production before -> after | Fixed-admission diagnostic sample audit |
|---|---|---|
| T06 shrunk23 |refusal -> exact|1 sample per route now exact|
| T06 shrunk210 |refusal -> exact|1 sample per route now exact|
| T06 shrunk232 |refusal -> exact|3 samples per route now exact|
| other67 inputs |unchanged status/output|unchanged samples|

Seventy production corpus inputs pass the sanitized monotonic comparison. The independent140-route diagnostic audit measures10 changed samples, all now equal original Smart, none away from exact. The arithmetic-only repeat confirms the same count. Historical T06 expectations remain historical; the table and complete before/after records establish the new measured baseline. The production8-case corpus needs **no further expectation update**: strict replay is8/8.

The25 fast tests pass (0.005s). The existing compiled generic-beta ASan/UBSan test passes its54 rows, including HD, in44.209s. Only its read-only SDK root is MAIN; source/harness remain in this worktree. `git diff --check` passes. Regenerable completed builds were deleted; scratch is39MiB before final report generation, well below5GiB.

inference:

The three traced tiny residuals were missing-operation errors caused by the helper's restrictive admission predicate. Matching upstream words, exact restored ray/glow/compose planes and bound public outputs support this independently of final-byte equality. Finite probes do not prove all native AE/UCRT inputs, custom ramps, arbitrary HDR or ROI/downsample. Length1 and Mode3 Highlight remain separate unresolved processing families.

changed_files:
- `core/kirakira_gaussian.h`
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/verify_kirakira_smart_C04.py`
- `tools/emulation/summarize_kirakira_smart_C04.py`
- `reports/fuzz/olmkirakira_smart_C04_gaussian.json`
- `orchestra/reports/C04-kira-smart-gaussian.md`
- `orchestra/reports/C04-kira-smart.md`

verify:

From this cluster commit, create the prior source in ticket scratch; no checkout or MAIN mutation is needed:

```sh
s="$PWD/orchestra/state/C04-kira-smart/recheck-gaussian"
mkdir -p "$s/gaussian-campaigns"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show e7f23f66:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
# The older source calls only the unchanged historical Gaussian predicate;
# the added inline function in the current header does not change that build.
for seed in 1 4; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/gaussian-campaigns/before-seed$seed.json" --corpus "$s/before-seed$seed-corpus" > "$s/before-seed$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/gaussian-campaigns/after-seed$seed.json" --corpus "$s/after-seed$seed-corpus" > "$s/after-seed$seed.log" 2>&1
done
for family in gaussian-all gaussian-boundary; do
  python3 tools/emulation/verify_kirakira_smart_C04.py --family "$family" --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s/gaussian-campaigns" --gaussian-negatives --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
for index in 210 23 232; do
  "$py" tools/emulation/trace_kirakira_smart_C04.py --corpus-index "$index" --production --require-exact --scratch "$s/trace-$index" --report "$s/trace-$index.json" > "$s/trace-$index.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --gate-off --family gaussian-length1 --scratch "$s/length1-diagnostic" --report "$s/length1-diagnostic.json" > "$s/length1-diagnostic.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --family gaussian-length1 --scratch "$s/length1-production" --report "$s/length1-production.json" > "$s/length1-production.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/sample-audit" --report "$s/sample-audit.json" > "$s/sample-audit.log" 2>&1
```

Expected: table above;180+30 exact matrix cases;70 corpus comparisons and600 sanitized campaign routes pass;10 negative refusals;27 exact trace stages; Length1 diagnostic retains exactly1 word difference and production refuses;140-route sample audit has10 samples toward exact.

next:
- The ticket's three-cluster stop condition is met. Final Smart seed1 has166 refusals:13 have no AEX output;153 have successful AEX output. Of those153, the diagnostic candidate is exact on84 and mismatches69. These84 are not promoted without a general branch proof.
- Largest remaining diagnostic group is Channel1/Mode2 (27 cases); trace non-unit control/seed/opacity materialization next. The next groups are Channel6/Mode2 (8), Channel2/Mode2 (7), Channel5/Mode2 (5), Channel3/Mode2 (5). These parameter groups are not proven root causes.
- Preserve and trace the Length1 counterexample; implement/validate Mode3 Highlight and four-plane color seeds separately. Native AE/UCRT, custom ramps, HDR and ROI/downsample remain outside the measured contract.
