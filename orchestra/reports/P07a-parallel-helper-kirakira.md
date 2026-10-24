status: done
summary: |
  Added deterministic GCD row helper and threaded KiraKira's profiled warp stages.
  Default single-frame speedup is 1.59–1.73x; sampled heavy case is 1.49–1.64x.
  Required campaigns: 850 cases, 832 Smart-exact, 18 shared refusals, no Smart mismatches.
  All 387 retained corpus cases replay true; 50 TSan cases pass.
  Original and final unit failure/error sets match; durable bundles are registered.

facts:

- Base: `c101e2880a4b423e5e285c36baf120cbedd609b3`. Production changes are only
  `core/olm_parallel.h` and `core/kirakira_warp.h`. Neither existing blur driver
  was migrated: their independent hash/conformance validation was not performed.
- `lockf -k ~/.cache/olm-emu/bench.lock python3 orchestra/reports/P07a-evidence/profile.py`
  sampled the registered P00b default 4K/PF32 render. The retained call graph
  repeatedly enters `warp_get_rotation_matrix_2d` / `warp_sample_bilinear_zero`.
  The box filter's four-row recurrence remains unchanged.
- The helper uses `dispatch_apply_f` at `QOS_CLASS_USER_INITIATED`, joins each pass,
  preserves/restores worker floating-point environments, and supports
  `OLM_PARALLEL_MAX=1/2/8`. Non-Apple builds fall back to the serial loop.
  Each warp callback writes exactly one destination row; interpolation operand
  order is unchanged. Below 65,536 destination pixels the warp remains serial.
- `warp_bench.py` (internally locked) measured 256x256 at 0.000412923 s serial
  versus 0.000235240 s cap8. At 1080x1080: 0.008462481 versus 0.002169038 s.
  Its raw comparisons all passed. The shared helper's 385 coverage/grain/override/
  rounding-environment checks passed (`helper_test.cpp`).
- `threads.py`: 50 generated cases, including 25 enlarged to 257x259; depths
  PF8=22, PF16=12, PF32=16. Profiles: SDR=42, HDR=4, signed=3, nonfinite=1.
  All raw SHA-256 values agree at caps 1/2/8. The same 50 cases passed an
  instrumented `-fsanitize=thread` SDK host with `halt_on_error=1`, no reports.
- `original.py`: a private snapshot with the pristine base warp header matched
  all 50 candidate hashes. `frame_hashes.py` streamed 48 full-frame Smart outputs
  to disk: original/1/2/8 × default/corpus05 × 1080p/4K × PF8/PF16/PF32.
  All 12 comparison groups matched exactly; first differing word: none.
  The frame-hash default uses the Mac's legal gain 1.0. The captured AEX default
  0.10000000149011612 is below the declared range and was refused by this
  general-input host when initially tried; no production guard was changed.
- `concurrent.py` (internally locked): four `RenderTyped<PF_Pixel8>` calls in
  four threads in one process, 1920x1080, four ray lengths 100, three repetitions
  per cap. All outputs identical; no deadlock. Median four-render batch times:
  cap1=0.395677542 s, cap2=0.337744291 s, cap8=0.331987750 s. This tests concurrent
  production kernels, not native AE's callbacks/UI or its scheduler.

Required Smart campaigns (`verify.py`, jobs=1, shrink-attempts=0):

| Geometry | Seed | Cases | Smart exact | Shared AEX/Mac refusals | Smart mismatches | Mac-only refusals |
|---|---:|---:|---:|---:|---:|---:|
| default | 1 | 300 | 287 | 13 | 0 | 0 |
| realistic-v1 | 1 | 100 | 100 | 0 | 0 | 0 |
| realistic-v1 | 20261025 | 100 | 99 | 1 | 0 | 0 |
| realistic-v2 | 1 | 100 | 99 | 1 | 0 | 0 |
| realistic-v2 | 20261025 | 100 | 98 | 2 | 0 | 0 |
| odd-even-v1, max 1080x1080 | 2026 | 150 | 149 | 1 | 0 | 0 |

An additional 150-case odd/even run at max 1920x1080 also had 149 Smart-exact
and one shared refusal. It is retained separately as `odd-wide`, not substituted
for the corpus's T15b flags. The first odd replay reported a max-size setup error;
matching the retained 1080 flag resolved it. Classic is outside this ticket's
contract route; its mismatches/refusals are retained in `summary.json`.

Standard `run.py --replay` results, with saved workers and matching geometry flags:
8 default + 62 gate-off + 41 gate-off reductions + 272 realistic + 4 odd/even =
387/387 `replay_matches_saved: true`. No oracle was rebuilt or replaced.

Source-matched Universal bundle timings below use the P00b driver and host,
`--phase matrix --situations full 4k --plugins olmkirakira --cases default corpus05 --jobs 1`.
Each timing command held `bench.lock`. These are single shared-machine measurements,
not isolated medians; concurrent non-benchmark work may affect them. Before uses
this ticket's pristine-header snapshot; after uses the final source. Initial P00b
sampling of all 11 cases completed 66/66 cells and selected `corpus05` as the
slowest sampled corpus case (not an exhaustive scan of all retained corpora).

| Case | Size | bpc | Before s | After s | Speedup |
|---|---|---:|---:|---:|---:|
| default | 1080p | 8 | 0.416305 | 0.244680 | 1.70x |
| default | 1080p | 16 | 0.386472 | 0.243578 | 1.59x |
| default | 1080p | 32 | 0.407093 | 0.244886 | 1.66x |
| default | 4K | 8 | 1.712067 | 0.987666 | 1.73x |
| default | 4K | 16 | 1.648478 | 0.963084 | 1.71x |
| default | 4K | 32 | 1.649103 | 1.009861 | 1.63x |
| corpus05 | 1080p | 8 | 0.371509 | 0.249523 | 1.49x |
| corpus05 | 1080p | 16 | 0.414668 | 0.252627 | 1.64x |
| corpus05 | 1080p | 32 | 0.388661 | 0.251146 | 1.55x |
| corpus05 | 4K | 8 | 1.603589 | 0.986872 | 1.62x |
| corpus05 | 4K | 16 | 1.598303 | 1.011354 | 1.58x |
| corpus05 | 4K | 32 | 1.604537 | 1.033447 | 1.55x |

`corpus05` is `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000008.json`,
SHA-256 `397d581e136bdcc44c1bec7b18e3e279af4a39a91a848f4909fe95b928445d64`.
The P00b host reports timing/admission, not raw hashes; the separate streamed SDK
host checks above provide original-versus-threaded hashes.

Durable Universal candidate: `~/.cache/olm-emu/P07a-kirakira`, executable SHA-256
`1589a493f2730faea9bd5ca061216f1be48af15986860acd62044c8219a60575`.
Pristine-header Universal baseline: `~/.cache/olm-emu/P07a-kirakira-before`, SHA-256
`192224922c48b1df1f0dc4f6f6848adb4569eb156efac8b3a374463a2860aa8d`.
Both reuse P00b host SHA-256
`7ec265ebee76465adc0a0aef743cc8af46fff3f96e6c4d431ab724d1e9c5620e`
and are registered in `INDEX.json`. Numerical tests ran on arm64; x86_64 compiled
but was not executed. Memory-pressure checks were 57–62% free; scratch stayed
well below 5 GiB (large raw frames were streamed, then deleted).

Unit comparison: `OLM_TEST_JOBS=1 python3 -m unittest discover -s tests -p
'test_*kirakira*.py'` with TMPDIR in ticket scratch. The clean original-header
run (`original_units.py`) ran 143 tests in 96.717 s, with 24 failures and 43 errors.
The final run ran 143 tests in 94.427 s, with the identical 67 failure/error IDs.
These legacy suites are **not green**: missing historical worker paths and stale
source/provenance assertions are among their diagnostics. No failure ID was added.
Earlier missing-SDK and overlapping-header-edit runs are retained as diagnostics,
not used as the clean baseline. The helper checks, TSan and differential checks
above passed independently.

inference:

Independent warp rows explain the observed improvement without changing a
reduction order. These finite emulator/SDK-host comparisons support this change;
they do not establish all-input compatibility or native AE/Windows equivalence.
The existing blur-driver migrations can be a separate conformance-scoped ticket.

changed_files:

- `core/olm_parallel.h`
- `core/kirakira_warp.h`
- `orchestra/reports/P07a-parallel-helper-kirakira.md`
- `orchestra/reports/P07a-evidence/`: reproduction scripts, compact hashes,
  campaign summaries, build identities, profiles, and timing records.

verify:

Run from this worktree with the existing MAIN SDK/assets and registered workers.
The scripts use ticket scratch and jobs=1. Run these sequentially:

```sh
python3 orchestra/reports/P07a-evidence/threads.py
python3 orchestra/reports/P07a-evidence/original.py
python3 orchestra/reports/P07a-evidence/verify.py
lockf -k ~/.cache/olm-emu/bench.lock python3 orchestra/reports/P07a-evidence/frame_hashes.py
python3 orchestra/reports/P07a-evidence/concurrent.py
python3 orchestra/reports/P07a-evidence/warp_bench.py
```

Expected: 50 forced-cap + 50 TSan passes; 50 original-hash matches; all required
campaign counts and 387 true replays above; 48 full-frame hashes in 12 exact groups;
nine exact concurrent batches. `OLM_PARALLEL_MAX` is stripped by the generic fuzz
adapter/P00b driver; `threads.py` explicitly installs the cap in the candidate
environment, and the streamed-frame script passes it directly.

To rebuild the durable bundles, run `build.py` (candidate) and `build.py --original`
(after `original.py`). To repeat a timing cell, run the P00b command above under
`lockf -k ~/.cache/olm-emu/bench.lock`, with `--cache` set to either registered cache
and `--state orchestra/state/P07a-parallel-helper-kirakira/recheck-LABEL`.

next:

No required ticket work remains. Follow-up candidates: repair the legacy unit
fixtures/worker bindings, validate native AE preview/MFR, and separately qualify
blur-driver migrations. Scratch build products were deleted; logs and compact
evidence remain. No release gate, ledger, MAIN source or other plugin was changed.
