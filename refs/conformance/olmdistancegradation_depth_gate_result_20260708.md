# OLMDistanceGradation depth-gated source-mask result - 2026-07-08

> 2026-07-09 correction: the source-mask rule and `case_0023` closeout remain
> valid, but the `7/16` extended-batch exact count below is superseded as a
> true16 conformance count. Re-verifying the same `/tmp/olmdg_16ext_depthgate2`
> artifacts with the canonical 16bpc verifier gives `5/16`.
> See `refs/conformance/olmdistancegradation_depthgate_true16_reverify_20260709.md`.

Author: Claude (auditor/orchestrator session). All numbers below are FACT
(measured in this session, Mac AE 2026 host via `scripts/run_ae_single_case.py`,
compared against the request `expected/` references with numpy int64 abs-diff).

## Final source state (worktree, uncommitted)

`mac/OLMDistanceGradation/OLMDistanceGradation.cpp` = HEAD (bc1383d)
+ env-gated debug instrumentation (inert without `OLM_DG_*` env vars)
+ **depth-gated source-mask rule** (`source_mask_owns_alpha(alpha, pixel_size)`):

- 8bpc (`PF_Pixel8`): `alpha > 0` — identical to HEAD, so the packaged 8bpc
  behavior cannot regress by construction.
- 16bpc and deeper: `alpha > 1.5f/255.0f` — the 1-code (8U-equivalent) alpha
  fringe is NOT part of the source mask, matching the Windows
  8U-convert + `cvThreshold(thresh=1.0)` field staging
  (decomp `FUN_1811749a0` / `FUN_18117c580`, scale DATs read from the binary).

`DGParams.pixel_size = sizeof(P)` is set in `RenderBits<P>` and drives the
mask, `d_alpha`, and inside/outside seeds uniformly.

Reverted relative to the 2026-07-07 working state (and confirmed inert by the
C++ A/B harness `refs/conformance/olmdistancegradation_ab_regression_20260708.md`):

- `dt_to_normalized` denom: restored to `raw_max > 1.0f`.
- Both-combine: restored to `std::max(inside, outside)` (the `cv::add`
  latent diff stays FLAG-NOT-FIX, per the standing freeze).

Backups: `OLMDistanceGradation.cpp.full_changes_backup` (2026-07-07 global
threshold + denom + both changes) and `.cpp.splitrule` (rejected role-split
variant) in the session scratchpad.

Installed plugin (`~/Library/Application Support/Adobe/Common/Plug-ins/7.0/
MediaCore/OLMDistanceGradation.plugin`) = this depth-gated build (2026-07-08
14:26, binary 294656 bytes).

## Results (FACT)

### 16bpc case_0023 (the target lane)

`nonzero_px=0 max=0` against the packaged 16bpc reference, re-verified twice
on the depth-gated build (plus bg_on/bg_off `nonzero_px=0` on 2026-07-07 with
the global-threshold build, whose 16bpc behavior is identical). The packaged
reference itself is sha256-identical to the 2026-07-03 and 2026-07-06 Windows
current-AEX recaptures (`refs/conformance/olmdistancegradation_case0023_reference_export_audit_20260707.md`),
so this is exact against live Windows output, not a stale PNG.

### 16bpc extended batch, depth-gated build (`/tmp/olmdg_16ext_depthgate2/results.csv`)

| case | nonzero_px | max | mean |
|---|---:|---:|---:|
| 0008 | 0 | 0 | 0 |
| 0010 | 0 | 0 | 0 |
| 0011 | 0 | 0 | 0 |
| 0012 | 272839 | 64 | 1.297803 |
| 0013 | 166114 | 64 | 0.935583 |
| 0014 | 377093 | 64 | 1.625522 |
| 0016 | 13288 | 38 | 0.103834 |
| 0020 | 0 | 0 | 0 |
| 0021 | 0 | 0 | 0 |
| 0022 | 0 | 0 | 0 |
| 0023 | 0 | 0 | 0 |
| 0024 | 3984 | 1 | 0.000480 |
| 0025 | 12291 | 1 | 0.001482 |
| 0026 | 2570 | 1 | 0.000310 |
| 0027 | 489 | 1 | 0.000060 |
| 0028 | 14287 | 12 | 0.027857 |

**Superseded exact count:** this report originally recorded `7/16` here, but
the 2026-07-09 canonical true16 reverify gives `5/16`. Keep the family notes
below as historical byte-view triage, not as current true16 conformance.
Remaining families:

- `0012/0013/0014` (max=64, broad): the known Layer-source family — a
  separate lane, unchanged by this work.
- `0024..0027` (max=1, small counts): NEW near-miss family — one-word
  residuals, good candidates for the next narrow witness.
- `0016` (max=38), `0028` (max=12): unclassified small families.

## The two measurement traps this closed over (record for the ledger)

1. **`run_ae_single_case.py` carries over project depth.** The 8bpc request
   `reference_manifest.json` files have no `project.bits_per_channel`, so the
   jsx leaves the project at whatever depth the previous run set (observed:
   `pixel_size=8` = `PF_Pixel16` while running an "8bpc" request). Every
   "8bpc regression" number measured through this runner on 2026-07-08
   (136K-196K px, max=2) reproduces **identically on a HEAD build** — it is a
   runner-context artifact, not a code regression. A HEAD-control build is
   the mandatory control for any future claim from this runner.
2. **The single-case runner does not reproduce the 2026-06-19 canonical 8bpc
   batch context even with `bits_per_channel=8` forced** (constant ~195K px
   max=2 offset vs `expected/`, HEAD build included). 8bpc verdicts must come
   from the canonical `ae_pixel_validation` batch flow only. The runner IS a
   trustworthy byte-exact judge for the 16bpc request family (multiple exact
   results in this session).

Corollary recorded on 2026-07-08: a temporary C++ CLI re-implementation of
the plugin ("A/B harness") is valid for *attributing which source change
moves which case* but NOT for verdicts against Windows references — its
fringe-region behavior diverges from the real plugin.

## Attribution history (how we got here)

- 2026-07-07: global `alpha > 1.5/255` threshold closed 16bpc case_0023
  (bg_on/bg_off exact) but was unverified elsewhere.
- C++ A/B harness attributed all 43/45 changed CLI outputs to the threshold
  change (a); denom (b) and Both-combine (c) inert on the case set.
- AE-host sentinels initially appeared to show broad 8bpc regressions from
  (a); the HEAD-control experiment exposed trap 1 (depth carryover), and the
  forced-8bpc rerun exposed trap 2. The real depth story: Windows includes
  1-code fringe at 8bpc (2026-06-19 packaged exactness) and excludes it at
  16bpc (case_0023) — hence the depth-gated rule.
- A role-split variant (inside inclusive / outside+d_alpha strict) was
  falsified: it reintroduced an 8px threshold-family residual at 16bpc
  case_0023 (needs strict inside seeds too).

## Next steps

1. Rewrite the CONFORMANCE_LEDGER Latest Overrides + DG row from this report
   plus the 2026-07-09 true16 correction (16bpc case_0023 closed by the
   depth-gated rule; extended true16 count is `5/16`; 8bpc structurally
   HEAD-identical, canonical-batch reconfirmation pending).
2. Canonical 8bpc batch reconfirmation (low priority; 8bpc code path is
   HEAD-identical).
3. Classify the new `0024..0027` max=1 family and pick the next witness.
4. `0012/0013/0014` Layer family stays its own lane.
