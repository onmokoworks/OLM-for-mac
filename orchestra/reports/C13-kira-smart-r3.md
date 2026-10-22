status: done

summary:
- Three clusters closed separately: finite signed-Alpha seeds, zero-ray approximation source composition, and scalar directional Gaussian controls.
- Seed1 Smart improves207→215→219→222 exact; mismatches remain0; refusals93→78.
- Previous exact Smart and all Classic campaign records persist; every cluster passes ASan/UBSan and corpus monotonicity checks.
- Final seed6=230/0/70; seed7=227/0/73. Strict production corpus replay8/8.
- Stop after three clusters; active IPP resize and other residuals are documented without promotion.

facts:

Base `7d0b64fad8c5e5909404853e0264537352fcb7e0`, branch `orch/C13-kira-smart-r3`.

| Cluster | Commit | Seed1 exact/mismatch/refusal | Seed6 | Seed7 |
|---|---|---|---|---|
| base |7d0b64fa|207/0/93|220/0/80|not measured|
| signed finite seeds |75c7c728|215/0/85|227/0/73|223/0/77 measured before next cluster|
| zero-ray approximation |37c11c85|219/0/81|227/0/73|225/0/75|
| directional Gaussian controls |this commit|222/0/78|230/0/70|227/0/73|

All campaigns ran `python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed <seed> --jobs 2 --shrink-attempts 0 --shrink-seconds 0`, with ticket-local corpus/scratch/report paths. Before-source reruns use `verify_kirakira_admission_F10.py --campaign-source`. No framework errors. Seed1/6/7 original Smart outputs/rejects are287/13,291/9,287/13. Reference workers were used by absolute path without rebuilding; INDEX contains the separate RadialBlur workers.

Final source SHA256 `643a6d545a22e3aabf0003ea0b0d661e942b502ff5a29c23b1cfb290e32c07f8`; original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`; retained worker SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`.

Detailed commands, boundaries, corpus tables and machine evidence:

- [Signed seeds](C13-kira-smart-r3-signed.md):600 sanitized campaign routes;167+167 independent exact conditions;6 invalid-input refusals;70 unchanged corpus inputs. Negative fractional-exponent Alpha remains excluded; seed1/index89 first box output word227 is AEX `0000c07f` versus `aff59c3d`.
- [Zero-ray approximation](C13-kira-smart-r3-zero-approx.md):900 sanitized campaign routes;378 exact conditions;18 negative refusals. Source composition restores index193 from254 differing final words to exact. Corpus index0 is explicitly rebased refusal→exact, retaining its old result. Historical diagnostic corpus changes620 samples, all to exact.
- [Gaussian controls](C13-kira-smart-r3-gaussian.md):900 sanitized campaign routes;288+288+24 production exact conditions;8 negative refusals. Case166's first seed word `0253b83c` versus `0153b83c`, and case27's skipped tiny Gaussian ray, become exact through the original scalar operations.

The numerical traces bind to original public Smart. Approximation's unused reduced source/seed planes are explicitly not claimed exact on the zero-ray shortcut. Active IPP interpolation remains excluded: the original resize uses sixth argument1, contrary to the historical nearest-neighbor audit, and the rejected general bilinear candidate still differs by6 final words. Its source patch and original write-PC evidence are retained for follow-up.

Final70-input corpus audit is unchanged by the third cluster;140 final arithmetic route replays change0 samples. Strict production replay8/8. Each cluster passes25 existing fast tests and the compiled54-row sanitizer test including HD; final sanitizer time44.047 seconds. `git diff --check` passes. Removed18 remaining generated compilation directories; cleanup measurement was40,249,742 scratch bytes (under5GiB).

No permission rejection occurred. No write to `/tmp`, MAIN or external emulator source/worker; no release-gate, ledger-forbidden-list or other-plugin changes; no stash, push, install, merge or history rewrite.

inference:

Public-bound traces and independent input/control matrices establish the three bounded general operation/admission rules. Finite tests do not establish all floating values, native AE/UCRT, custom active ramps or ROI/downsample. Embedded IPP resize, nonfinite filtering, color constructors and remaining Gaussian branches are separate unclosed operations.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `tools/emulation/audit_kirakira_numeric_corpus_F09.py`
- `tools/emulation/summarize_kirakira_smart_C13.py`
- `tools/emulation/fixtures/kirakira_{resize_linear,gaussian_controls}_C13.patch`
- `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000000.json`
- `reports/fuzz/olmkirakira_smart_C13_{signed,zero_approx,gaussian}.json`
- `orchestra/reports/C13-kira-smart-r3{,-signed,-zero-approx,-gaussian}.md`

verify:

The detailed reports contain full before/after, sanitizer, matrix, trace and corpus commands. Quick final recheck:

```sh
s="$PWD/orchestra/state/C13-kira-smart-r3/final-recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for seed in 1 6 7; do
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/seed$seed.json" --corpus "$s/seed$seed-corpus" > "$s/seed$seed.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
git diff --check
```

Expected seed1=222/0/78, seed6=230/0/70, seed7=227/0/73; replay8/8; clean diff check.

next:
- Ticket stop condition met at three closed clusters. Seed1 remaining78 refusals comprise13 without original output and65 with output.
- Follow-up: Channel6/four-plane and Channel2 scalar color constructors, embedded IPP resize/coefficient/dispatch recovery, Gaussian Length1/Highlight, NaN filtering. Keep native AE/UCRT proof separate.
