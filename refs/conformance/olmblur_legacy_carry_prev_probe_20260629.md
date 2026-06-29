# OLMBlur Legacy Carry-Prev Probe - 2026-06-29

## Scope

- Plug-in: `OLMBlur`
- Paths changed:
  - `cli/OLMBlur/main.cpp`
  - `mac/OLMBlur/OLMBlur.cpp`
- Goal: test the decomp-backed Legacy `all_same` rule where the comparison
  state carries forward across pixels with an initial sentinel `-1.0`

## Binary-grounded reason

`decomp/OLMBlur.aex.c.txt` shows both Legacy helpers use a carried previous
sample state, not the current port's per-pixel `have_prev=false` reset.

- `FUN_1800014f0` seeds horizontal compare state from `DAT_18000d27c`
  (`-1.0f`) and keeps `fVar24/fVar26/fVar28` outside the inner pixel loop.
- `FUN_180001ea0` does the same for the vertical helper with
  `fVar19/fVar21/fVar23`.
- `.rdata` confirms:
  - `DAT_18000d27c = -1.0f`
  - `DAT_18000d250 = 1.0f`

So the current port's "reset previous sample every pixel" behavior was too
simple.

## What changed

The port now carries the previous comparison RGB through the Legacy helper
scan instead of resetting it at each destination pixel. The sentinel starts at
`-1.0f`, and the carry updates only when the helper actually consumes at least
one sample.

## CLI result

Using the old 8bpc Software reference set:

- Before:
  - `case_0007` had 3 nonzero residual pixels:
    - `(0,0)` = `1`
    - `(488,941)` = `250` vs Windows `251`
    - `(488,942)` = `250` vs Windows `251`
- After:
  - `case_0007` drops to 1 residual pixel:
    - `(488,941)` = `250` vs Windows `251`

Witness trace:

- Before:
  - `(0,0) = 1.49396968`
  - `(488,941) = 250.499954`
  - `(488,942) = 250.499985`
- After:
  - `(0,0) = 0`
  - `(488,941) = 250.499985`
  - `(488,942) = 250.500015`

That is the same direction as the Windows runtime facts: the top-left spill is
removed, and one of the two `250.5` boundary witnesses crosses to `251`.

## Mac AE 16bpc result

Single-case live probe:

- Report:
  `refs/reports/ae_single_case_olmblur_carry_prev_probe_20260629/probe_report.md`
- Candidate PNG:
  `refs/reports/ae_single_case_olmblur_carry_prev_probe_20260629/olmblur__case_0007/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0007.png`

Key witness:

- `(0,0)` is now:
  - raw `0`
  - stored `0`

PNG comparison against the normalized Windows 16bpc reference:

- `max_diff=1`
- `nonzero_px=1/2073600`
- only remaining pixel:
  - `(345,672)` blue channel `98` vs Windows `97`

This retires the old localized Legacy `(0,0)` anomaly as an active blocker.

## Interpretation

The decomp-backed carry-prev rule is a real behavioral fact, not a cosmetic
refactor:

- it removes the old top-left Legacy spill
- it preserves the passing exact 8bpc cases
- it collapses the 16bpc Legacy outlier from a `383`-scale witness to a single
  `max=1` pixel

## Remaining gap

`OLMBlur case_0007` is not fully exact yet.

Remaining work:

- one last 8bpc witness at `(488,941)` (`250` vs `251`)
- one last 16bpc witness at `(345,672)` blue `98` vs `97`

That looks like a narrow residual family rather than the old border/all_same
structural mismatch.
