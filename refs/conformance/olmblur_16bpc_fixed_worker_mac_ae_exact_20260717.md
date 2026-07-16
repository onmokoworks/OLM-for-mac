# OLMBlur fixed-worker Mac AE 16bpc exact proof

Date: 2026-07-17 (Mac)

## Result

The declared normalized OLMBlur 16bpc seven-case slice is `AE exact`:

```text
case_0001 max=0
case_0002 max=0
case_0003 max=0
case_0004 max=0
case_0005 max=0
case_0006 max=0
case_0007 max=0
ok=7 fail=0 missing=0 total=7
```

## Bound execution identity

- Mac AE: `26.3x87`
- renderer: `SOFTWARE`
- project depth: `16bpc`
- working space: `None`
- linear blending: `false`
- loaded module PID: `7653`
- loaded module: `/Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMBlur.plugin/Contents/MacOS/OLMBlur`
- loaded binary SHA-256: `71df7efc027b463327fefa23575fff5f80d4b38ff529ae97418d79297f4f0d72`
- source fix commit: `e053c3dc`

The loaded path was observed with `lsof` in the rendering AE process and the
same on-disk module was hashed before the seven-case run.

## Root cause

The earlier double-precision `exp` candidate had been applied only to the old
inline render path. The live 16bpc host dispatch enters
`render_16bpc_nonlegacy_adapter` and then
`core/olmblur_worker16_nonlegacy.cpp`, whose coefficient generation still used
the float overload. Commit `e053c3dc` applies the binary-grounded
float-exponent/double-`exp` sequence to that actual worker.

Before the fix, `case_0004` retained two red samples (`max=2`). With the fixed
worker, both `case_0004` and the Legacy control `case_0003` are exact, and a
fresh same-binary rerun confirms all five previously exact cases remain exact.

## Claim boundary

This promotes only the declared normalized OLMBlur 16bpc seven-case cell to
`AE exact`. It does not promote 32bpc, broaden the covered parameter space, or
claim that CLI output substitutes for AE-host validation.
