# ColorKeep PF16 extended-range current Mac AE boundary

The current installed Universal ColorKeep binary
`ccc89781fa547450acc3053cb77bff8d6983cd8c6835866c87449e7a64117cce`
was mapped by exact path in After Effects `26.3x87` PID `88521`.  The project
used Software rendering, 16bpc, working space None, linear blending off, and
the hash-bound Preserve RGB input template
`51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679`.
All three public RGB Color Control values read back exactly.

This does **not** close an AE exact extended-range cell.  The no-effect control
changed 14 FLOAT32 channel words and the effect output differed from the
actual-AEX expected image at 21 words.  The control localizes the difference
to AE's 16bpc input representation: values one PF16 unit above nominal white
and values up to `65535/32768` are clamped to 1.0; RGB above alpha is also
clamped/premultiplied.  Preserve RGB removes the unrelated EXR transfer-curve
conversion seen in the first exploratory run, but it cannot make imported
FLOAT EXR create extended PF16 host words.

Artifacts:

- candidate return SHA-256: `4b2a3e98e50bcff5aeb7f33dedadff826a87891a222bfe24b0e7812c7be0f175`
- no-effect EXR SHA-256: `e5d8935df5bcc69dcc4fd55dbb2bf99c82f3e934fd0117872d396779ce589c41`
- effect-on EXR SHA-256: `441935a57f1e9f3595549e31e53c66d2a2716cf58e06eb5db1193a480e724233`
- run: `refs/mac_validation_runs/colorkeep_pf16_extended_host_20260806_run2`

The separate installed-public proof remains exact for the original synthetic
PF16 world: all 120 bytes, including three eight-byte row-padding regions,
match the actual AEX payload SHA-256
`1fa0ee04a8e57924bfb14a3c57f9ac937c7737486daca69b2bec689f6afe4a5e`.
That evidence is not merged with this AE observation.

To observe extended PF16 words inside AE, the next fixture must use a bounded
upstream effect that writes those words directly into an AE-managed PF16 world;
ordinary FLOAT EXR import is now proven unsuitable.  Until such a source is
available, `ae_exact_claim` remains false and no ColorKeep algorithm change is
justified.
