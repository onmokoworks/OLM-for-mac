status: done

summary:
- Admit finite PF32 HDR/signed luminance and Max box inputs through the existing Smart tuple.
- Seed1 Smart282/0/18 →284/0/16; fresh seed23 280/0/20 →285/0/15 (exact/mismatch/refusal).
- Preserve every previous exact Smart output and all600 Classic campaign result objects.
- Sanitized independent612 cases,600 campaign renders and70 guarded corpus cases pass; no expectation migration.

facts:

Base `f97b0143ab0f3a2ff14d34a957587722145f66fe`. F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`; original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`. All campaigns n300/jobs1/no shrinking. Initial remeasurement282/0/18; original Smart287 success/13 rejects.

All five successful-oracle refusals (39,52,86,179,272) produce exact final output with only final admission disabled. This cluster addresses39 (signed luminance) and86 (HDR Max). Original constructors181150600/18114ec60 call fade/powf helper1811501b0 then multiply by Alpha. MAIN decomp lines3524519/3523560/3524299 show the recovered arithmetic without an SDR constraint. No renderer arithmetic, Classic admission, work budget or final-byte correction changed.

Public-bound F32/UCRT trace86 matches every paired stage. Trace39 first differs at seed word0: original `0000c0ff`, Mac `0000c07f`;52 seed words differ. Ray3 differs126 NaN words, zero finite/NaN-boundary differences. Glow and composition are exact. This remains an explicitly non-exact intermediate NaN sign difference; the existing original aggregation clamp erases it. No first divergence at a still-host math import was established.

Gate-off576 and production576 independent conditions are exact under ASan/UBSan: both channels, four geometries, both box modes/merge modes, six strengths and HDR/signed/finite-extreme inputs. Production boundary36 is exact: fade0/0.2, maximal finite values, signed zero, subnormals, long rays, Highlight and opacity0. Eight nonfinite negative controls refuse. The new source predicate requires finite PF32 and the existing scalar brightness tuple, retaining all layout/geometry/parameter/ramp/work restrictions.

| Check | Before | After |
|---|---|---|
| Seed1 Smart E/M/R |282/0/18|284/0/16;39,86 improved|
| Seed23 Smart E/M/R |280/0/20|285/0/15;55,146,227,274,276 improved|
| Guarded F32 corpus70 |baseline|0 result changes|
| Both-route sample comparisons140 |baseline|0 changed samples|
| Production saved replay |8/8|8/8|
| T06 saved matches |39/62|39/62; all62 result objects unchanged|

Final600 sanitized Smart campaign renders reproduce their hashes. All prior exact Smart and all600 Classic result objects persist.26 fast tests pass; compiled54-row sanitizer test passes (46.853s). Saved replays honor fixture worker bindings; the guarded audit independently fixes F32. The23 inherited T06 discrepancies remain failures, not green results. No corpus rebaseline is necessary. Machine evidence: `reports/fuzz/olmkirakira_smart_C38_brightness.json`.

inference:

The existing scalar box/clamp pipeline supports the tested finite PF32 HDR/signed domain. These are bounded CPU-emulation results, not unrestricted native AE/UCRT or ROI/downsample proof. Intermediate NaN sign/payload identity remains unimplemented where downstream original clamps erase it. No hypothesis was refuted in this cluster.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `reports/fuzz/olmkirakira_smart_C38_brightness.json`
- This report and ticket summary.

verify:

Run at this cluster commit. Expected counts above. Every long command redirects to ticket-local logs.

```sh
s="$PWD/orchestra/state/C38-kira-smart-r9/recheck-brightness"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/emulation/snapshot_kirakira_C34.py --revision f97b0143ab0f3a2ff14d34a957587722145f66fe --scratch "$s/base" > "$s/snapshot.log" 2>&1
for seed in 1 23; do
 python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/base/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus$seed" > "$s/before-$seed.log" 2>&1
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus$seed" > "$s/after-$seed.log" 2>&1
done
for family in finite-brightness-box finite-brightness-boundary; do
 python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family finite-brightness-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/base/before.cpp" --campaign-dir "$s" --seeds 1 23 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/base/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
for i in 39 86; do
 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/probe_kirakira_smart_C07.py --ucrt-math --campaign-seed 1 --trace-index "$i" --require-exact --scratch "$s/trace$i" --report "$s/trace$i.json" > "$s/trace$i.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
```

Gate-off576: repeat the matrix command with `--source "$s/base/before.cpp" --gate-off`, separate scratch/report. Both traces must be public_bound;39 retains the reported NaN differences. Saved replay8/8. T06 replay uses the same command with its corpus directory: expect39/62, unchanged result objects. Fast/compiled sanitizer commands are in C34's final report, with scratch relocated here.

next:
- One cluster closed. Investigate finite four-component box (seed1/index52).
