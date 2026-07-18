# OLMColorKey unresolved exactness audit

Date: 2026-07-18

Scope: Mac-only, read-only audit. It does not edit the plugin, ledger, AE
state, or Windows data.

## Finding

The Edge Thin caller amount boundary is closed by
`olmcolorkey_edge_thin_caller_amount_20260718`.

The Windows AEX loads disk ID `0x0d` through its integer accessor, stores the
unchanged `int32` at record `+0x28`, and converts it once with `CVTDQ2PS`.
Positive Edge Thin copies when `distance <= amount`; negative Edge Thin zeros
when `distance < abs(amount)`, retaining equality. The same comparator follows
all three distance-type dispatches.

The older files named `edge_thin_erode` and `edge_thin_actual_caller` actually
follow record `+0x40` into `FUN_180008320`, which is the separate Edge Blur
apply path. They remain useful Edge Blur evidence but are superseded as Edge
Thin ownership evidence.

The Mac host boundary now uses an integer slider, `u.sd.value`, and `A_long`.
The distance primitives and the explicit type-dependent translation remain a
separate proof lane; this is not an AE-exact claim.

The 32bpc host-path evidence remains separately blocked by host/input
conversion. No PNG tuning or leaf threshold patch is justified by the current
record.

## Command

```text
python3 tools/emulation/audit_olmcolorkey_unresolved_exactness_20260718.py
```

Machine-readable output: `olmcolorkey_unresolved_exactness_20260718.json`.

The next useful evidence is distance-primitive output or Mac AE conformance,
not another amount-normalization witness.
