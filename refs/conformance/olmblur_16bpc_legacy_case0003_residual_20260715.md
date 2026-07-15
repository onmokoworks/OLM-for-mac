# OLMBlur 16bpc Legacy `case_0003` Residual - 2026-07-15

## Result

The current-plugin Mac candidate differs from the Windows expected PNG in
exactly 20 exported samples. Every difference is red only: 19 are
`candidate - expected = +2` PNG samples and one is `-2`.
Because the PNG exporter doubles the AE 0..32768 word domain at these odd
samples, this is an inferred candidate-minus-expected split of `+1` word for 19
samples and `-1` word for one sample.

The exact witnesses are recorded by:

```text
python3 tools/emulation/test_olmblur_worker16_legacy_case0003_residual.py
```

They are `(936,1), (739,2), (23,36), (59,76), (640,85), (383,124),
(204,179), (250,213), (273,218), (273,221), (298,228), (227,278),
(564,281), (165,345), (165,346), (129,403), (362,406), (362,408),
(756,425), (25,482)`. The first 19 have expected-minus-candidate `-2`; only
`(756,425)` has `+2`.

## Binary boundary

The actual Windows AEX is `plugins_2025/OLMBlur.aex`, SHA-256
`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`, and the
Legacy worker entry is `FUN_180005f20` at `0x180005f20`. Its decompilation
shows direct PF16 little-endian A/R/G/B word loads converted to float32 at
`0x18000632e..0x180006364`, with alpha validity set from a nonzero word at
`0x180006368..0x18000636f`. The portable
`core/olmblur_worker16_legacy.*` preserves that contract and the six-chunk
Legacy helper schedule.

The complete actual-AEX fixtures in
`tools/emulation/fixtures/olmblur_worker16_legacy/` pass byte-for-byte for
basic, large-radius reverse, and mixed-alpha reverse cases. The focused replay
command is:

```text
python3 tools/emulation/smoke_olmblur_worker16_legacy.py
```

The AEX writer evidence also separates the Legacy/alternate direct
`CVTTSS2SI` word-store family from the standard `+0.5` writer. Therefore a
global Legacy rounding change is not supported by this case.

## Decision

No worker or core change is evidence-backed. The residual remains unlocalized
upstream of the final exported word. Its sign-mixed one-word pattern rejects a
single uniform offset, but does not by itself exclude every input-dependent
rounding implementation. The exact AEX staging/helper fixtures exclude a
structural Legacy worker mismatch only for those fixture inputs; they do not
bind the live `case_0003` coordinates. Same-run Mac and Windows captures of the
pre-store float bits, writer input, stored PF16 word, and exported PNG word are
required before reopening the worker, helper, or writer.
