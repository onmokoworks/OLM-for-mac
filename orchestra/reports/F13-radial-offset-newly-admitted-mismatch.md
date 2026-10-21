status: done

summary:
- Closed the four T01 newly admitted wrong routes by restoring refusal, as explicitly allowed by this ticket; this is an admission repair, not numerical nonfinite conformance.
- Generic typed Zoom admission now requires finite input; finite signed/HDR and older typed profiles retain their dispatch.
- Original-AEX replay confirms all four original routes and all four reduced routes now refuse, with clean target ASan/UBSan runs.
- Seed 1 n300 retains 79 Classic and 108 Smart exact results, all 187 hashes unchanged; eight selected existing tests pass.
- Rebaselined 35 corpus files: 58 saved mismatch routes become exact; measured before/after results are identical and fresh replay matches all 35.

facts:

Starting revision: `1408f2374500ece3d98c439ef9f9f66cb6e7efd7`.
Before production SHA-256: `bbe3731138805156ed487136e70dad5c39731fc560a284956b9f47e44d0297d8`.
After production SHA-256: `347c9fd41c3ca6fcc9146efd5b60b5985e86c0c34b31d0309ef488847f01e2db`.
Original AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
Worker: `/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker`,
SHA-256 `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`.
No worker rebuild, MAIN write, release-gate edit, or ledger change was made.

`verify_radialblur_offset_admission_F13.py` completed with 18/18 recorded-AEX
worker calibrations and nine original/reduced/retained witnesses across four
builds: diagnostic before, ordinary after, sanitized after, and sanitized before.
The diagnostic before build adds only a stderr observation of the generic
admission boolean and its SDR predicate; the report separately records the
unmodified production hash. Its original-target output hashes match T01.
Each original-AEX observation passed output guards and session-clean checks.
The ordinary adapter's older calibration remains 4/6, as in T01; its two stale
PF32 hashes are not acceptance truth. The independent 18/18 calibration is used.

The before diagnostic records `generic=1 sdr=0` on every target mismatch.
Afterward all eight original/reduced wrong routes return error 516 at
`RenderZoomTyped:unadmitted-zoom-profile@2917`. No wrong output is relabeled exact.
E=exact, M=mismatch, R=refusal. Hex words below are little-endian raw bytes.

| Witness | Geometry | Route | Before → after | Before differing bytes / words | First byte; AEX → Mac word |
| --- | --- | --- | --- | --- | --- |
| Seed1 #89 original | 17×21 | Classic + Smart | M → R each | 827 / 328 each | 0; `00000000` → `4623c1ff` |
| Seed1 #459 original | 23×22 | Smart | M → R | 1220 / 375 | 64; `0000807f` → `4623c1ff` |
| Seed2 #217 original | 72×1 | Smart | M → R | 142 / 47 | 34; `0000807f` → `0000c07f` |
| Seed1 #89 reduced | 1×1 | Classic + Smart | M → R each | 10 / 4 each | 0; `00000000` → `4623c1ff` |
| Seed1 #459 reduced | 2×1 | Smart | M → R | 12 / 5 | 0; `6238403e` → `0000c07f` |
| Seed2 #217 reduced | 4×1 | Smart | M → R | 9 / 5 | 34; `00000000` → `0000c07f` |

The other Classic target routes remain refused. Reductions took 19, 32, and 32
attempts respectively, preserving their initially mismatching routes. The
committed fixtures contain pixels, generator parameters, operations, and input
hashes; no global-minimality claim is made. Full output hashes and refusal
observations are in `F13-focused.json`.

Retained witnesses:

| Witness | Classic before → after | Smart before → after | Retained exact hash |
| --- | --- | --- | --- |
| Seed1 #193, PF16 odd strides | E → E | E → E | `61419588ac096ac05cd390e83bc6a71aa4f6db1c7b50b1d36ab130dc272ccde8` |
| Seed1 #219, PF32 signed | R → R | E → E | `20ed5eeffb1f587b3ccb5f2f9979222284a3c0e5da0c1f6e025e4dfdc8e65961` |
| Seed1 #425, PF32 HDR | M → M | E → E | `8405927c8b78605ecd5b76dd15eb2a7b5d0b85df52ce708a410305069cd117dc` |

The first hypothesis, requiring the entire SDR range in the inner generic
classifier, was refuted by #219: Smart exact became refusal. Its 300-case
measurement is preserved in `F13-sdr-experiment.json` (79/107 exact, one AEX
budget result on an already-refused case). This supplied a new boundary value:
finite signed input must remain admitted. The final finite-only check preserves
#219 while refusing the nonfinite targets. No second cause hypothesis was
refuted; the stop condition was not reached.

Static cross-check: read MAIN's `disasm/OLMRadialBlur.aex.asm.txt` at
`0x1800057a4..0x180005830`. The original Zoom builder reads four integer fields
at `R14+0x64/0x68/0x6c/0x70`, multiplies by `R14+0x48`, truncates, and calls
`0x18000b680` four times. This is consistent with retaining the grounded Zoom
worker selection and table setup. It does not prove nonfinite arithmetic.
The new evidence is at the admission boundary, not a claim to have found the
first differing arithmetic operation inside the original AEX.

The actual fuzz commands were `tools/fuzz/run.py --plugin radialblur --n 300
--seed 1 --jobs 2 --case-timeout 30 --budget-minutes 120`, with the above worker,
separate ticket scratch directories, scratch `--corpus`, and JSON/log outputs.
They were run on starting production, the rejected SDR candidate, and final
production. The final comparison and counts are:

| Campaign / route | Before | Final | Exact hashes retained |
| --- | --- | --- | --- |
| Seed1 n300 Classic | 79 E / 1 M / 220 R | 79 E / 0 M / 221 R | 79 / 79 |
| Seed1 n300 Smart | 108 E / 1 M / 191 R | 108 E / 0 M / 192 R | 108 / 108 |
| Original AEX | 280 successful / 20 rejected | 280 successful / 20 rejected | All available oracle hashes unchanged |

Both runs completed 300 cases, no framework errors, no AEX budget results in
the final comparison. Only #89 changes in this sample. The focused run covers
#459 and seed2 #217 outside it. `compare_radialblur_admission_F13.py` exited 0:
`F13_AUDIT 187 exact hashes preserved; 2 target routes refused; corpus 35 unchanged`.

Corpus replay used `tools/fuzz/run.py --plugin radialblur --replay
tests/fuzz_corpus/radialblur --jobs 2 --case-timeout 30 --budget-minutes 60` on
both starting and final production. Both exited 1 because the saved expectations
were stale, with all 35 observations completed. Every measured route record,
including hashes and callback metadata, is unchanged before/after this fix.
The rebaseline command exited 0 and changed only `result` and `provenance` in
35 files. Inputs, parameters, reductions, and operations remain identical.
A third replay exited 0 with `replay_matches_saved=true`, 35/35.

Orchestrator-visible corpus accounting:

| Route | Saved expectation | Measured before | Final / rebased | Cases |
| --- | --- | --- | --- | --- |
| Classic | M | E | E | 23 |
| Classic | M | M | M | 1 |
| Classic | R | R | R | 11 |
| Smart | M | E | E | 35 |

Per-file table (all paths under `tests/fuzz_corpus/radialblur`; measured-before
states are exactly the final column):

| File | Saved Classic / Smart | Final Classic / Smart |
| --- | --- | --- |
| `seed1_case000006_253d4390d90b.json` | M / M | E / E |
| `seed1_case000029_b099428e963b.json` | R / M | R / E |
| `seed1_case000034_f67ec58a433d.json` | R / M | R / E |
| `seed1_case000041_42e5f8af427d.json` | M / M | E / E |
| `seed1_case000043_5a4c69b38522.json` | M / M | E / E |
| `seed1_case000044_d1d38fe702c9.json` | R / M | R / E |
| `seed1_case000050_aa6536a877df.json` | M / M | E / E |
| `seed1_case000081_9774c69c219e.json` | M / M | E / E |
| `seed1_case000091_0f4b356bb556.json` | M / M | E / E |
| `seed1_case000152_0f4b356bb556.json` | M / M | E / E |
| `seed1_case000153_f8d4024784b4.json` | R / M | R / E |
| `seed1_case000180_f67ec58a433d.json` | R / M | R / E |
| `seed1_case000203_f8d4024784b4.json` | M / M | E / E |
| `seed1_case000221_dc2eff5fb2aa.json` | M / M | E / E |
| `seed1_case000230_f8d4024784b4.json` | R / M | R / E |
| `seed1_case000253_0f4b356bb556.json` | M / M | E / E |
| `seed1_case000268_c68d152bb97c.json` | R / M | R / E |
| `seed1_case000269_d7848a7c740d.json` | R / M | R / E |
| `seed1_case000271_9a5b282a1ffa.json` | M / M | E / E |
| `seed1_case000303_5a4c69b38522.json` | M / M | E / E |
| `seed1_case000305_93a01b17e479.json` | M / M | E / E |
| `seed1_case000328_93a01b17e479.json` | M / M | E / E |
| `seed1_case000347_d1d38fe702c9.json` | R / M | R / E |
| `seed1_case000369_90303525f87f.json` | M / M | E / E |
| `seed1_case000379_dc2eff5fb2aa.json` | M / M | E / E |
| `seed1_case000384_d1d38fe702c9.json` | R / M | R / E |
| `seed1_case000390_f8d4024784b4.json` | R / M | R / E |
| `seed1_case000421_71f8c982c45b.json` | M / M | E / E |
| `seed1_case000425_df3690c920ab.json` | M / M | M / E |
| `seed1_case000440_e04d91d93cb4.json` | M / M | E / E |
| `seed1_case000444_253d4390d90b.json` | M / M | E / E |
| `seed1_case000448_d1d38fe702c9.json` | M / M | E / E |
| `seed1_case000458_e04d91d93cb4.json` | M / M | E / E |
| `seed1_case000486_0f4b356bb556.json` | M / M | E / E |
| `seed1_case000487_5a4c69b38522.json` | M / M | E / E |

`validate_radialblur_admission_F13.py` exited 0: eight tests, zero failures/errors.
Selected existing files (prefix `tests/test_olmradialblur_`):

- `generic_baseline_20260820.py`
- `generic_baseline_sanitizers_20260820.py`
- `generic_budget_20260821.py`
- `generic_type3_sanitizers_20260820.py`
- `global_polar_smart_contract_20260820.py` (two tests)
- `size_noise_effectmain_20260821.py`
- `typed_inner_geometry_guard_20260807.py`

Initial smoke attempts failed to compile because worktrees lack MAIN's SDK
links: first seven failures missing `AEConfig.h`, then one missing
`Util/AEGP_SuiteHandler.cpp`/`MissingSuiteError.cpp`. The committed wrapper creates
scratch-only links to the absolute MAIN SDK paths and worktree Mac source;
it does not change test assertions or production. UI parity was not selected:
T01 already records its unrelated stale Thickness assertion.

Sanitizer limits are explicit: final target refusals have zero diagnostics.
The retained #193 odd-stride PF16 input/output and #425 Classic HDR output
have misaligned-reference diagnostics in both starting and final builds, with
identical diagnostic kinds and output hashes. These pre-existing findings are
preserved in `F13-focused.json`, not called sanitizer-clean. An early verifier
also required the *wrong* sanitized #89 output hash to equal the wrong ordinary
hash; that assertion failed (831 vs 827 differing bytes). The final verifier
keeps both observations, checks exact retained hashes, and requires clean
refusals on targets. It does not use agreement between wrong outputs as an oracle.
No admission guard was relaxed in final production.

inference:

The expanded Offset classifier leaked into the legacy typed fallback: failure
of RenderWorld's SDR gate did not prevent RenderZoomTyped's generic classifier
from admitting nonfinite input. Original-AEX output mismatches plus the passive
admission trace establish that these routes had no exactness basis. Restricting
that classifier to finite samples repairs the admission cause generally, without
coordinate/seed-specific code, tolerance, expected-value patches, or writer edits.
Requiring SDR rather than finiteness would incorrectly remove the observed exact
signed boundary. The underlying NaN/Inf propagation difference remains unresolved.
This is bounded CPU-AEX/fake-SDK-host evidence, not native Windows UCRT/AE or GPU
conformance, nor a claim that every remaining admitted profile is exact.

changed_files:

- `mac/OLMRadialBlur/OLMRadialBlur.cpp`: finite-input qualification for generic typed Zoom admission.
- `tools/fuzz/verify_radialblur_offset_admission_F13.py`: shared original-AEX target/retained replay, admission traces, and before/after sanitizer comparison.
- `tools/fuzz/fixtures/radialblur_offset_F13/*.json`: three reproducible reduced witnesses.
- `tools/fuzz/compare_radialblur_admission_F13.py`: assert retained exact hashes and monotonic corpus transitions against historical saved expectations.
- `tools/emulation/validate_radialblur_admission_F13.py`: existing-test runner with scratch SDK links.
- `tests/fuzz_corpus/radialblur/*.json`: 35 result/provenance rebaselines only.
- `orchestra/reports/F13-*.json`, `F13-*.log`, and this report: bound measurements, experiments, and verification evidence.

verify:

Run from the worktree root. The following reproduce final acceptance; the
committed before campaign is additionally audited against the fresh final one.
All logs/builds stay inside the ticket. Expected counts are the tables above.

```sh
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
worker=/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker
export TMPDIR="$PWD/orchestra/state/F13-radial-offset-newly-admitted-mismatch/recheck"
mkdir -p "$TMPDIR"
"$py" -u tools/fuzz/verify_radialblur_offset_admission_F13.py \
  --worker "$worker" --scratch "$TMPDIR/focused" --report "$TMPDIR/focused.json" \
  > "$TMPDIR/focused.log" 2>&1
"$py" -u tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 2 \
  --case-timeout 30 --budget-minutes 120 --worker "$worker" \
  --scratch "$TMPDIR/fuzz" --corpus "$TMPDIR/fuzz-corpus" --report "$TMPDIR/after.json" \
  > "$TMPDIR/fuzz.log" 2>&1
"$py" -u tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur \
  --jobs 2 --case-timeout 30 --budget-minutes 60 --worker "$worker" \
  --scratch "$TMPDIR/corpus" --report "$TMPDIR/corpus-after.json" \
  > "$TMPDIR/corpus.log" 2>&1
"$py" tools/fuzz/compare_radialblur_admission_F13.py \
  --before orchestra/reports/F13-before.json --after "$TMPDIR/after.json" \
  --corpus-before orchestra/reports/F13-corpus-before.json \
  --corpus-after "$TMPDIR/corpus-after.json" --report "$TMPDIR/comparison.json" \
  > "$TMPDIR/comparison.log" 2>&1
"$py" -u tools/emulation/validate_radialblur_admission_F13.py \
  --scratch "$TMPDIR/smoke" --report "$TMPDIR/tests.json" > "$TMPDIR/tests.log" 2>&1
git diff --check
```

Expected: all exit 0; focused complete, 18 calibration successes, four original
and four reduced M→R routes, preserved retained hashes; fuzz 79/108 exact with
no mismatches; corpus 35 matching; audit preserves 187 exact hashes; smoke 8/8.
The historical recorded-outcome audit can also run using all four committed
`F13-before.json`, `F13-after.json`, `F13-corpus-before.json`, and
`F13-corpus-after.json` inputs. It binds saved expectations to the starting
revision, so rebaselining does not erase the table.

The actual corpus mutation command was:

```sh
python3 tools/fuzz/rebaseline_corpus.py --plugin radialblur \
  --corpus tests/fuzz_corpus/radialblur \
  --report orchestra/state/F13-radial-offset-newly-admitted-mismatch/corpus-after.json
```

next:

No work remains for the ticket's explicitly permitted refusal/rebaseline outcome.
Separate follow-ups should binary-ground nonfinite Zoom arithmetic before
readmission; repair the pre-existing typed odd-stride reference-binding UB;
and investigate the retained Classic mismatch independently. The unrelated
Thickness UI assertion remains outside this ticket. Disposable build outputs
were cleaned by the runners; scratch is well below 5 GiB.
