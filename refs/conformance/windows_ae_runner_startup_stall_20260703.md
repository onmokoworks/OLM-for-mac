# Windows AE Runner Startup Stall

Date: `2026-07-03`

The latest load-only prewarm retries for:

- `olmsmoother2_current_aex_0004_load_prewarm_retry_20260703`
- `olmdirectionalblur_angle0_load_prewarm_retry_20260703`

show the same deeper blocker.

## Proven facts

- CDB launches successfully.
- AE startup logging reaches App Version / AppDirs / module initialization.
- `sxe ld:<target module>` was armed, but the target module load marker never appears.
- `ae_runner_log` is absent.
- `run_complete` is absent.
- No witness breakpoint was armed in these retries.

## Interpretation

The stall is now bounded to a stage before the JSX runner processes the request.

So the next Windows ask should not be:

- another witness-local breakpoint retry
- another module-load-only retry

It should be:

- startup / JSX-runner / request-dispatch diagnostics

## Required next diagnostics

For one exact-case request, return enough startup evidence to classify which of
these stages is the first one that fails to advance:

1. AE launched
2. startup scripts initialized
3. JSX runner script invoked
4. request directory discovered
5. request JSON loaded
6. target project/case dispatch started
7. plugin module load reached

## Minimum useful evidence

- the exact request directory/path given to the runner
- whether the JSX runner script started at all
- any runner-side stdout/stderr or file log tail
- whether request JSON enumeration happened
- whether case count was computed
- the exact last emitted startup line before timeout

## Rejected non-answers

- repeating only AE startup banners
- repeating only `sxe ld:<module>` setup
- another timeout report without new runner-stage evidence
