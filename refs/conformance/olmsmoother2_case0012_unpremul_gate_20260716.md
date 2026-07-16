# OLMSmoother2 case_0012 unpremultiply gate - 2026-07-16

- Status: `BINARY_GROUNDED_TYPED_WITNESS_MATCH`
- Scope: current-AEX legacy key/gamma `case_0012`, 8bpc producer lane
- Production change: do not tie frame-setup unpremultiply to `Enable Color Key`

## FACT

- The 8bpc host path calls `FUN_180003eb0`, which calls `FUN_180002e90`.
- `FUN_180002e90` gates `FUN_180002840` on byte
  `[render_params + 0x18]`.
- `FUN_180005180` returns `setter_base + 8`, so the gate is setter byte
  `+0x20`.
- `FUN_180004e10` initializes setter `+0x20` to zero and does not set it from
  `Enable Color Key`. The Mac port previously used `p.enable_key` as this
  gate and therefore unpremultiplied every key-enabled frame.
- With that false gate removed, the Mac case_0012 trace at `(92,841)` now
  matches the accepted Windows actual-AEX witness:
  - class bytes at `(92,840)`: `255,0,0,0`
  - class bytes at `(92,841)`: `255,255,0,255`
  - cardinal6 descriptor: `92,841,1,92,842,2`, key `20`
  - `e170 c=7`
  - first append source `(92,840)`:
    `rgba=(0.18447499,0.18447499,0.18447499,0.68235296)`,
    `weight=0.28448275`
- The Windows returned words decode to the same values within float print
  precision: RGB `0.18447503`, alpha `0.68235296`, weight `0.28448275`.

## INFERENCE

The first upstream descriptor divergence was caused by an incorrect Mac frame
setup gate, not by `d3b0`, `da50`, `e170`, `f270`, or `e3a0`. Those downstream
functions should remain unchanged for this witness.

## Provenance Caution

The broad legacy CLI smoke uses AE-saved `before_effects` PNGs for most cases.
Those files are already premultiplied exports and are not a host-input oracle;
after this binary-grounded fix their aggregate PNG metrics become worse. That
does not override the same-run Windows runtime witness. Mac AE validation is
still required before any `AE exact` promotion.

## Verification

```text
refs/scripts/build_olmsmoother2_cli.sh
python3 refs/scripts/smoke_olmsmoother2_case0012_unpremul_gate.py
```

## Mac AE Host Debug

The rebuilt universal Debug bundle was installed as the only
`OLMSmoother2.plugin` under MediaCore and rendered successfully in Mac AE
`26.3x87`, Software, 8bpc, working space None, linear blending off. This proves
host load/render viability only. Against the current Windows full-frame
case0012 reference the single-case output remains known-red:

- `max=151`
- `mean=0.21710720486111112`
- `19891 / 2073600` differing pixels

An old/new installed-bundle A/B used the same request and host context:

- pre-fix bundle: `max=115`, `mean=0.1616552131558642`, `19486` differing pixels
- grounded bundle: `max=151`, `mean=0.21710720486111112`, `19891` differing pixels
- grounded versus pre-fix: `max=147`, `mean=0.07201111593364197`,
  `13589` differing pixels
- at `(92,841)`: Windows `[233,233,233,237]`, grounded
  `[210,210,210,239]`, pre-fix `[246,246,246,252]`

The aggregate regression does not invalidate the typed producer match. It
shows that the old false unpremultiply gate accidentally compensated for a
remaining downstream producer/composite residual. Reintroducing that gate is
therefore forbidden; the next investigation stays downstream of the matched
first append.

The single-case runner is not the canonical 8bpc batch context, and the result
is not `AE exact`.
