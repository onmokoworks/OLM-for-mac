# Smoother2 / DirectionalBlur Startup-Stall Retry Contract

Date: `2026-07-03`

The 2026-07-02 narrow witness-gate retries changed the blocker again.

They did not fail from broad hit storms. They failed earlier:

- AE startup reached `sxe ld:<module>`
- the target module load marker never appeared
- no visible modal was reported
- AfterFX and CDB both stayed responsive but produced no further progress

This means the next retry should not start from exact witness gating. It should
first stabilize target module load for the exact case/project path.

## Current exact failure

### OLMSmoother2

- request: `olmsmoother2_current_aex_0004_writer_gate_retry_20260702`
- exact condition attempted:
  `bp OLMSmoother2+0x350b if dwo(@rsp+0x34)==0x76f and dwo(@rsp+0x38)==0x207`
- failure:
  no target module load marker before timeout

### OLMDirectionalBlur

- request: `olmdirectionalblur_angle0_helper_gate_retry_20260702`
- exact condition attempted:
  `bp OLMDirectionalBlur+0x13e0/+0x38d0/+0x4a20/+0x6b30/+0x4880`
  on real case `db_existing_case_0001_software_pair`
- failure:
  no target module load marker before timeout

## Required next strategy

For both plug-ins:

1. use the exact real project/case that should exercise the plug-in
2. do not begin with narrow witness breakpoints
3. first prove the target module actually loads in that render path
4. only after the load marker is confirmed, bind one narrow breakpoint family
5. if the session stalls before load again, return the exact startup/log tail
   that shows where progress stopped

## Successful return threshold

A useful next return must contain one of:

- confirmed target module load for the exact case/project path
- or a fresh exact startup-stall signature that is narrower than the current
  “responsive but no load marker before timeout”

It does not yet need the final witness-local values if module-load stabilization
itself is the only new result.
