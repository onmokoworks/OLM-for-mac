status: blocked

summary:
- Reproduced both seed45 Smart mismatches with the default F45 worker; neither is fixed or refused.
- DG first observed divergence is the float field at cvSmooth entry; two scratch-only bilateral candidates failed.
- Obeyed the two-refuted-hypotheses stop rule; no production/admission edits were applied.
- Saved both known-red witnesses; both individually replay with saved results. Radial plane capture remains incomplete.
- The required n300 campaigns and complete corpus replay remain outstanding.

facts:
- Starting HEAD `4fabd3ee40fe564f39441235746b0ccced122fe3`, branch `orch/C39-seed45-residual-mismatches`, clean initial worktree. Read AGENT_GUIDE, GOTCHAS, compatibility plan and plugin ledger rows. No gate/ledger, MAIN, emulator checkout or production edits; no push, stash, history rewrite, or subagents.
- Default worker in this checkout is F45 (`/Users/onmk/.cache/olm-emu/worker-F45-msdouble/aex-guest-worker`), SHA256 `8849565128e4147bb39b145bf392e20da1983c476498ca4448001ea278a38409`. F46 is not the merged default here.
- Original diagnostic command: `PYTHONDONTWRITEBYTECODE=1 python3 orchestra/state/C39-seed45-residual-mismatches/reproduce.py` (exit 0). The committed equivalent is `tools/fuzz/reproduce_C39.py --plugin <plugin>`. Full parameters, input/AEX/source/worker hashes and both route results are retained in corpus/evidence JSON.
- DG seed45 case2: 169x1 PF8, Bilateral, Size0. Smart reference SHA256 `c7f3ed695bd7f22776182458d8f2ed460e24520dc0179f7b018a01f433a8b735`; Mac `bc94a91aa42b9251ca331fd53856f177acea8654ee0416ab1b975db80fd1bfee`. Four differing bytes, first 424: reference `19`, Mac `1a`. Classic independently differs at 366 bytes; this ticket does not claim Classic closure.
- `trace_distancegradation_blur_C14.py --seed 45 --index 2` (full command below) exited 0. Public-trace output hash equals the separate raw Smart oracle. At original RVA `0x1172901` (cvSmooth call), pre-filter planes differ in 82 FLOAT32 words: first word1 is AEX `00002a42` (42.5), Mac `00002842` (42). Post-filter planes also differ in 82 words. Full paired planes retained in `C39-evidence/dg-trace.json`.
- Static read of MAIN's `disasm/DistanceGradation.aex.asm.txt`, addresses `1811728aa..181172901`: only Blur Mode1 skips cvSmooth; diameter is `2*size+1`. Current Mac `has_effective_blur` gives Bilateral Size0 special treatment only for PF32. This is a boundary observation, not a proven complete fix.
- Hypothesis 1: allow PF8 Bilateral Size0 to retain its unrounded field and use the existing general scalar bilateral body for radius-one narrow geometry. `dg-probe.py` first run (exit0) produced 44 differing bytes on seed45 case2, first4 reference `d5` / Mac `d4`; seed44 case70 produced eight, first232 reference `39` / Mac `38`. Refuted as a fix. Log `dg-probe.txt` retained; committed equivalent `probe_distancegradation_C39.py --body general-scalar`.
- Hypothesis 2: retain that field and use the existing specialized radius-one body instead. Second `dg-probe.py` run (exit0) produced 122 differing bytes on seed45 case2, first0 reference `56` / Mac `82`; seed44 case70 again eight, first232 `39` / `38`. Refuted as a fix. Log `dg-probe2.txt` retained; committed equivalent `probe_distancegradation_C39.py --body radius-one`.
- No paired intermediate boundary was obtained between these two refutations. Stopped numerical work under hard rule8. Neither rejected candidate is production code. No admission narrowing was attempted after the stop; absence of exact-case loss is not verified.

- DG saved-witness replay exited0: `replay_complete`, completed1, `replay_matches_saved=true`. This confirms the known-red result, not conformance. Syntax AST parsing and `git diff --check` pass.

- Radial seed45 case8: 12x21 PF8 Rotation. Smart reference SHA256 `9238ffef5cad5f2efe79b29bcf349cc34cc532ac563b2d4289d9729ec5f56049`; Mac `9578c539714e8ef47a83c67acd6806cc674097b7158c5904947c271e0f382ea4`. One differing byte at1000: reference `e4`, Mac `a8`. Classic separately differs at1006 bytes. Full input and parameters are in its saved corpus witness.
- Existing `trace_radialblur_rotation_C11.py` was invoked through a scratch wrapper with F45 and the exact unshrunk witness. Initial trace exited1 on the config capture command containing `:angle` assignments. The wrapper then omitted the two zero angle assignments (after asserting they are zero); no numerical parameter changed. The second run captured config, then exited2 attempting the first 432000-byte preaccum plane with 106 watches. Both Python drivers exited1 via CalledProcessError. Stderr was not retained by the existing tracer; the precise worker rejection reason is unconfirmed. These are subprocess failures, not permission/tool rejections.
- Config-only original trace had render_error0, intact guards, and the same reference output hash as the raw public oracle. Native angular step FLOAT320.2, radial minimum0/maximum14; the Mac dimensions are1800x15, matching that grid. This does not establish any numerical plane equality or first divergent Radial stage.
- The pre-F41b source was not run before the DG stop condition. Its admission for this case is UNKNOWN; the ticket's budget-relaxation suspicion is neither confirmed nor refuted.
- Radial saved-witness replay exited0: replay_complete, completed1, replay_matches_saved=true. Full corpus replay and all six requested n300 campaigns were NOT run. No zero-mismatch or zero-exact-loss claim is made.
- All launched diagnostic/replay processes exited. Regenerable adapter and plane build directories/binaries were deleted; retained scratch is5653767 bytes (<5GiB). No tool permission rejection occurred. DG evidence commit is `5560a9ec`; Radial packaging is the next commit.

inference:
- DG's original pre-filter plane retains fractions where current Mac has already rounded. Correcting that staging alone and reusing either attempted bilateral body is insufficient. The bilateral post-filter arithmetic needs a new paired boundary before another candidate.
- Saved mismatch results are regression witnesses of unresolved behavior, not passing conformance evidence.

changed_files:
- `tools/emulation/trace_distancegradation_blur_C14.py`: optional seed selection, default unchanged.
- `tools/fuzz/reproduce_C39.py`: bounded original-case capture for either ticket plugin.
- `tools/fuzz/probe_distancegradation_C39.py`: reproduces the two rejected scratch-only candidates.
- `tests/fuzz_corpus/olmdistancegradation/seed45_case000002_C39.json`.
- `orchestra/reports/C39-evidence/*` and this report, including both rejection logs as `.txt`.
- `tools/fuzz/trace_radialblur_C39.py`: exact witness wrapper for existing Rotation tracer.
- `tests/fuzz_corpus/radialblur/seed45_case000008_C39.json`.

verify:
From this worktree (serially, no emulator rebuild):
```sh
s="$PWD/orchestra/state/C39-seed45-residual-mismatches"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/fuzz/reproduce_C39.py --plugin olmdistancegradation > "$s/reproduce-dg.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/emulation/trace_distancegradation_blur_C14.py --seed 45 --index 2 --scratch "$s/dg-trace" --report "$s/dg-trace.json" > "$s/dg-trace.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C39.py --body general-scalar > "$s/general-scalar.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C39.py --body radius-one > "$s/radius-one.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation/seed45_case000002_C39.json --jobs 1 --scratch "$s/replay-dg" --report "$s/replay-dg.json" > "$s/replay-dg.log" 2>&1
git diff --check
```
Candidate probes require their respective `dg-general-scalar` / `dg-radius-one` scratch directories not to exist. Expected numerical results are the known-red counts above, not zero mismatches. The trace requires MAIN's existing Python environment. All required inputs and diagnostic source are committed; scratch sources/binaries are regenerable.

Radial saved witness verification (expected saved mismatch, exit0):
```sh
python3 tools/fuzz/reproduce_C39.py --plugin radialblur > "$s/reproduce-radial.log" 2>&1
python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur/seed45_case000008_C39.json --jobs 1 --scratch "$s/replay-radial" --report "$s/replay-radial.json" > "$s/replay-radial.log" 2>&1
```
Optional reproduction of the incomplete trace (requires absent `$s/radial-trace2`, expected nonzero exit at plane capture):
```sh
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/fuzz/trace_radialblur_C39.py > "$s/radial-trace2.log" 2>&1
```
The latter is a retained failure reproducer, not a passing verification. For a follow-up, chunk capture into smaller watch batches and retain worker stderr, then compare the original normalized plane before investigating final sampling. Remove regenerated build directories after checks.

next:
- Follow-up DG ticket: capture the original radius-one bilateral body using the exact unrounded pre-filter floats, compare its taps/weights/accumulation and cvConvertScale boundary before testing another implementation. Alternatively prove a principled admission restriction with zero exact losses.
- Resume Radial investigation in a separate follow-up after this stop. Determine pre-F41b admission and obtain paired planes before any numerical/admission change.
- Both plugins still require seed1/44/45 n300, zero Smart mismatches, per-case zero exact losses, and full saved corpus replay after a proven fix or refusal change.
