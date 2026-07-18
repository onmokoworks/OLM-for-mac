# OLMBlur 32bpc Mac Validation Preparation (2026-07-18)

Status: `blocked_preflight`

No candidate EXR was generated in this run. The fail-closed launcher found no
pre-existing `After Effects` process (`pgrep -x "After Effects"` returned an
empty result), so it refused to start or attach to an unverified AE instance.
This is the exact blocker, not a render or algorithm failure.

## Pinned contract

- AE major/minor: `26.3`
- Project: `32bpc`, `SOFTWARE`, working space `None`, linear blending off
- Output template: `OLM EXR 32 Float`
- Output: uncompressed OpenEXR, RGBA float, two same-comp renders
  (`no_effect` and `effect_on`)
- Input SHA-256: `cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4`
- Request SHA-256: `dea49cdf4b6504a8080b351f38a1c11cf1be226776dc46ca38b8add6cd0d526d`

## Current plugin binding

The current source build and the installed bundle contain the same universal
binary. The recorded `Contents/MacOS/OLMBlur` SHA-256 is:

`71df7efc027b463327fefa23575fff5f80d4b38ff529ae97418d79297f4f0d72`

The existing actual-AEX adapter audit remains a separate Mac-only proof and
reports `12/12` fixture cases passing. It does not claim AE exactness.

## Re-run

With exactly one After Effects process already open and the current bundle
loaded, run:

```text
python3 scripts/run_olmblur_32bpc_mac_validation_20260718.py \
  --support-dir /tmp/olmblur_32bpc_mac_validation_20260718_support \
  --output-dir /tmp/olmblur_32bpc_mac_validation_20260718_return \
  --result-json /tmp/olmblur_32bpc_mac_validation_20260718_return/mac_validation_return.json \
  --provenance-json /tmp/olmblur_32bpc_mac_validation_20260718_return/provenance.json
```

The delegated runner performs the existing plugin mapping proof and FLOAT EXR
format checks. A successful candidate remains `ae_exact_claim: false` until
its raw FLOAT32 words are compared with the Windows effect/control pair.
