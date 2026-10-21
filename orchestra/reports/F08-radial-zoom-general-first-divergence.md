status: blocked

summary:
- Found and corrected a general Zoom dispatch defect: otherwise-supported zero-variation Offset profiles fell into legacy convolution instead of the original prepass/scatter/normalization path.
- Shrunk T05 cases 271 and 486 now match every captured original-AEX plane and both output routes; shrunk PF16 454 and PF32 116 also become exact. No admission predicate or gate was relaxed.
- Required seed-1/300 campaign improves Classic exact 32→35 and Smart exact 38→41, with zero lost exact rows.
- Full acceptance is blocked by a proven disagreement between retained AEX workers at the inverse-coordinate math boundary, plus remaining odd-stride typed failures/UB. No corpus expectations were changed.
- This is a reviewable partial implementation, not a completed general-Zoom compatibility or native-Windows claim.

facts:
- Base: `02307fff65391bfcad40918c16916400bb29b519`, branch `orch/F08-radial-zoom-general-first-divergence`. Read `AGENT_GUIDE.md`, RadialBlur ledger rows/forbidden actions, compatibility plan, emulation GOTCHAS, T05 report/cluster rows, relevant probe/adapter/source files. MAIN, AEXCompat sources and retained workers were read-only; no worker rebuild, push, history rewrite or `/tmp` writes.
- Source before SHA-256: `ba824fe8627eb5f4cc92686e0970bafba0a41c29e98840b3941cc5e66906f750` (same as T05).
- Source after SHA-256: `66ed2aeb5132e0a5670b3801a781e8d3e5a77c142533911c9b497b1b4b30db85`.
- Original AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- T05/fuzz worker SHA-256: `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`; controlled trace worker from cache INDEX: `16ab2412c00b6ce5d61cadbf9d1cd3aa3c991f36bc66c6af8c2595c32d075e3c`. Both run the same AEX. Six retained transport calibrations match for each public adapter build; that finite calibration does not equate their math imports.
- Reproducible reduced inputs, typed pixels, parameters and strides are committed in `tools/fuzz/fixtures/radialblur_zoom_F08.json`. Reductions were regenerated from T05 seed/index with the original source and bounded 64-attempt reduction; these are not claimed globally minimal.

  | T05 index / reduced cluster | depth | shrunk geometry | before mismatching words per route | after Classic / Smart | sanitizer |
  |---|---:|---|---:|---|---|
  | 271 / inner Offset | 8 | 2×1 | 1 | exact / exact | clean |
  | 486 / outer Offset | 8 | 3×1 | 1 | exact / exact | clean |
  | 454 / inner Offset | 16 | 1×3 | 1 | exact / exact | clean |
  | 116 / inner Offset | 32 | 3×1 | 4 | exact / exact | clean |
  | 30 / outer Offset | 32 | 2×1 | 1 | mismatch 1 / mismatch 1 | clean on one-row world |
  | 158 / outer Offset | 16 | 1×2 | 3 | mismatch 3 / mismatch 3 | alignment UB |

- Same raw pixels with padding set to zero: 30 becomes exact on both routes and sanitizer-clean; 158 still mismatches on both routes but sanitizer becomes clean. These are separate alignment experiments, not replacements for the original cases. The existing aligned-world dispatch restriction still sends odd-stride typed cases to the legacy path. Alignment-only admission edits were not made.
- Passive plane instrumentation reuses `probe_radialblur_zoom_fade_20261002.py`; native watches capture B150 input/prepass, A9D0 eligibility/span/scatter, and 9D80 input. Missing legacy stages are recorded as `not_executed_in_mac_path`, never as zero-valued matching planes.

  | shrunk case | original polar RGBA words | polar differences before/after | normalized differences before→after | eligible bytes differing after |
  |---|---:|---|---:|---:|
  | 271 | 28,800 | 0 / 0 | 3,367→0 | 0 |
  | 486 | 28,800 | 0 / 0 | 720→0 | 0 |
  | corpus 253 | 28,800 | 0 / 0 | 3,387→0 | 0 |

- After the correction, **all eight captured stages** match the controlled worker for all three rows: polar, eligibility, span, preaccum, premax, accum, max, normalized. The controlled worker and fuzz worker also agree on final output for 271/486. No fade is active in these primary witnesses; active-fade compatibility is not inferred from zero-fade observations.
- First normalized witness for 271: word 8780, AEX little-endian float bytes `00000080`, before Mac `00000000`; word 8781 AEX `ffff7f3f`, before Mac `00000000`. For 486: word 9615, AEX `0400803f`, before Mac `0000803f`. These expose legacy zero/alpha-clamp behavior upstream of writing; the writer was not patched.
- Static inspection used `pefile` + Capstone on the original AEX, ranges `0x4640..0x5e70` and `0xa9d0..0xb150`. At `0x57a4..0x5830` Zoom constructs the four Strength/Edge tables; strengths are stored at work `+0x3ed8/+0x3edc`. A9D0 reads them at `0xaaf1/0xadee`. The fix selects this existing numerical path using neutral Offset controls solely for worker eligibility; real render parameters and all earlier refusal predicates are retained. Its extension is limited to zero Size/Noise variation because component-field admission occurs earlier.

- **Proven reference boundary, corpus 253:** original-AEX `A850` output for pixel (0,1), radius bits `0x3f000000` on both workers, angle bits `0x40490fda` on the fuzz worker versus `0x40490fdb` on the controlled worker. `9D80` sampler alpha then becomes `0x3f800000` versus `0x3f7ffffe`; final PF8 alpha is `ff` versus `fe`. The Mac agrees with the controlled worker in every captured plane and final byte. Fuzz worker source uses `y.atan2(x)` at FLOAT32; the retained controlled-reference patch uses DOUBLE atan2 followed by FLOAT32 conversion. No host-math replacement was made.
- Corpus-253 controlled/Mac raw SHA-256: `56b10b93033b4de9947293803b2f4582cf3812043b2c29a72485bada0d90770a`; fuzz-worker raw SHA-256: `e847837dfbc45db76e77d5007908021f3cbaa634ba4ff7cddf58f8df49a46ae9`. The old fuzz trace CLI cannot parse typed Angle assignments or offset windows; its successful sampler-only replay omits **only zero/default Angle parameters**, checks that they are zero, and uses direct A850/9D80 output-pointer watches. It reproduces the session hash.

- Required campaigns, before and final source respectively (each completed 300/300):

  ```sh
  python3 tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 2 --corpus orchestra/state/F08-radial-zoom-general-first-divergence/before_corpus --scratch orchestra/state/F08-radial-zoom-general-first-divergence/before_scratch --report orchestra/state/F08-radial-zoom-general-first-divergence/before.json
  python3 tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 2 --corpus orchestra/state/F08-radial-zoom-general-first-divergence/final_corpus --scratch orchestra/state/F08-radial-zoom-general-first-divergence/final_scratch --report orchestra/state/F08-radial-zoom-general-first-divergence/final.json
  ```

  Both commands were redirected to same-prefix `.log` files. No bypass/sanitizer variable was set for these production campaigns.

  | route | exact before→after | mismatch before→after | refusal before→after | uncompared before→after | lost exact |
  |---|---|---|---|---|---:|
  | Classic | 32→35 | 11→8 | 256→256 | 1→1 | 0 |
  | Smart | 38→41 | 19→16 | 242→242 | 1→1 | 0 |

  Original indices 41/50/271 become exact on both routes. AEX wall-time budgets changed 4→5 (ok 276→275, reject 20→20); this did not change either route's exact count. An earlier wider private candidate also had 35/41 exact; the committed source restricts the new dispatch selection to zero Size/Noise variation and was independently rerun.

- Corpus replay of all 35 rows: original source 35/35 `matches_saved`; final source 27/35 unchanged. The following is the complete changed-case table (word counts are exact mismatching raw words, no tolerance):

  | corpus seed-1 index | Classic before→after | Smart before→after |
  |---|---|---|
  | 41 | mismatch 1→exact | mismatch 1→exact |
  | 50 | mismatch 2→exact | mismatch 2→exact |
  | 91 | mismatch 2→exact | mismatch 2→exact |
  | 152 | mismatch 1→exact | mismatch 1→exact |
  | 253 | mismatch 3→mismatch 1 | mismatch 3→mismatch 1 |
  | 271 | mismatch 1→exact | mismatch 1→exact |
  | 425 | mismatch 36→mismatch 36, bytes unchanged | mismatch 36→mismatch 9 |
  | 486 | mismatch 1→exact | mismatch 1→exact |

  All oracle results are unchanged between these two corpus replays. Fewer differing words are **not** completion: 253 exposes a different alpha word due to the worker disagreement. Therefore strict “only toward exact” acceptance is not claimed. Corpus JSON remains untouched; replay currently exits 1 by design. Full before/after route results and hashes are committed in the evidence JSON.
- Tests: `test_olmradialblur_pf8_writer_oracle_20260728.py` plus `test_olmradialblur_global_polar_smart_contract_20260820.py`: **13 passed** using MAIN SDK directories through `CPATH`, and scratch `TMPDIR`. Initial global-contract compilation without SDK include paths failed (`AEConfig.h` missing); rerun with absolute include paths passed. UI parity additionally ran: 2 passed / 1 failed due to the existing literal whitespace expectation before `THICKNESS_DISK_ID`; executing the same three test functions against base and candidate source confirms identical pass/fail results. No UI/test assertion was changed.
- Initial probe-development failures were assertions for absent legacy planes, an accidental post-fix shrink into a no-op with no B150 watch, and old trace-CLI Angle/window syntax. The committed fixture/passive-stage/sampler-only modes resolve these harness issues. No permissions tool call was rejected.
- Evidence: `orchestra/reports/F08-radial-zoom-general-first-divergence.evidence.json` includes source/AEX/worker bindings, complete corpus transitions, final campaign summary/changed rows, before/after plane counts and first differing words, sanitizer messages, and both coordinate/sampler traces.

- Final committed-probe smoke (`--measure-only --indices 271,486,454,116`) confirms all four exact on Classic and Smart. Removed 33 regenerable build/venv directories; remaining scratch is 87,730,536 bytes, below 5 GiB.

inference:
- The first port divergence in the smallest PF8 offset witnesses is choosing legacy convolution after exact polar sampling. Offset-only control differences must not choose a different Zoom numerical algorithm; the shared path correction restores the original maximum-alpha and signed intermediate behavior.
- Corpus 253 is a demonstrated emulator/reference-math boundary. Choosing which atan2 result equals general native Windows UCRT requires separate authoritative evidence; modifying the port or a final byte to satisfy the newer fuzz worker would contradict the retained controlled witness.
- The remaining 158/425 failures cannot all be attributed to that one boundary from the evidence here. Odd-stride UB is directly observed; other causes remain unproven. The broad unadmitted-zoom-profile population is not safe to admit.
- Acceptance 1 is met for four shrunk targets, not the whole cluster population; acceptance 2 passes; acceptance 3 is not fully closed; the relevant fast test subset passes with a separately documented pre-existing UI test failure. Stop here at the proven external reference boundary, without widening admission or changing corpus truth.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `tools/fuzz/probe_radialblur_zoom_F08.py`
- `tools/fuzz/fixtures/radialblur_zoom_F08.json`
- `orchestra/reports/F08-radial-zoom-general-first-divergence.evidence.json`
- `orchestra/reports/F08-radial-zoom-general-first-divergence.md`

verify:
Run from the ticket worktree; use fresh output-directory names (the probe refuses overwrite). Every long command below was run with output redirected to scratch logs during this ticket.

```sh
S="$PWD/orchestra/state/F08-radial-zoom-general-first-divergence"
PY='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
mkdir -p "$S"
"$PY" tools/fuzz/probe_radialblur_zoom_F08.py --output "$S/verify_base_planes" --revision 02307fff65391bfcad40918c16916400bb29b519 --indices 271,486,253 > "$S/verify_base_planes.log" 2>&1
"$PY" tools/fuzz/probe_radialblur_zoom_F08.py --output "$S/verify_final_planes" --indices 271,486,253 > "$S/verify_final_planes.log" 2>&1
OLM_RADIAL_CANDIDATE_SANITIZE=1 "$PY" tools/fuzz/probe_radialblur_zoom_F08.py --output "$S/verify_sanitizer" --measure-only --indices 271,486,454,116,30,158 > "$S/verify_sanitizer.log" 2>&1
"$PY" tools/fuzz/probe_radialblur_zoom_F08.py --output "$S/verify_fuzz_sampler" --indices 253 --sampler-only --legacy-trace-angles --trace-worker /Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker > "$S/verify_fuzz_sampler.log" 2>&1
python3 tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 2 --corpus "$S/verify_corpus" --scratch "$S/verify_fuzz_scratch" --report "$S/verify_fuzz.json" > "$S/verify_fuzz.log" 2>&1
python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --scratch "$S/verify_replay_scratch" --report "$S/verify_replay.json" > "$S/verify_replay.log" 2>&1
```

Expected: base normalized differences 3367/720/3387, final all captured planes zero differences; 271/486 exact on both workers, 253 exact only against controlled worker. Sanitizer: 271/486/454/116 exact/clean; 30 residual 1 word, 158 residual 3 words plus alignment diagnostics. Default fuzz expected Classic 35 exact, Smart 41 exact (AEX time-budget totals may vary). Replay expected 35 completed, 27 unchanged, the eight-row table above, exit 1; do not silently rebaseline it.

Fast tests (pytest is absent from system Python and MAIN emulation venv, so a scratch venv was used):

```sh
TMPDIR="$S" python3 -m venv "$S/verify_pytest"
TMPDIR="$S" "$S/verify_pytest/bin/pip" install --no-cache-dir pytest==9.1.1 > "$S/verify_pytest_install.log" 2>&1
CPATH='/Users/onmk/Documents/Projects/Personal/OLM as/Headers:/Users/onmk/Documents/Projects/Personal/OLM as/Headers/SP:/Users/onmk/Documents/Projects/Personal/OLM as/Util:/Users/onmk/Documents/Projects/Personal/OLM as/Resources' TMPDIR="$S" "$S/verify_pytest/bin/python" -m pytest -q tests/test_olmradialblur_pf8_writer_oracle_20260728.py tests/test_olmradialblur_global_polar_smart_contract_20260820.py > "$S/verify_tests.log" 2>&1
```

Expected: 13 passed. Remove regenerable build/venv outputs after review.

next:
- Resolve the fuzz-worker versus controlled/native-UCRT atan2 boundary using corpus 253's exact arguments and captured A850 result, without rebuilding or silently substituting the current oracle in this ticket.
- Separate odd-stride Zoom dispatch/read/write alignment ticket, starting with retained PF16 158 and PF32 30. Preserve their odd padding and original byte inputs.
- Then replay all saved cases and gate-off clusters; promote only demonstrated-exact, sanitizer-clean profiles. Keep all current guards and corpus expectations until that review.
