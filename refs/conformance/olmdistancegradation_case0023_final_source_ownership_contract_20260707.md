# OLMDistanceGradation case_0023 Final/Source Ownership Contract - 2026-07-07

Target:

- request id:
  `olmdistancegradation_case0023_final_source_ownership_20260707`
- case:
  `olmdistancegradation_extended__case_0023`
- render set:
  Windows AE Software 16bpc

Purpose:

- explain the last two sampled representative mismatches after Mac-side
  source, field, shade, store, and PNG-export checks were bounded
- decide whether the remaining `73px` residual is due to Windows source/mask
  ownership, final compose/writeback ownership, or an export/path split

Mac-side facts to preserve:

- packaged/current Windows references are byte-identical for this case
- Mac shade source matches the request input PNG under AE `PF_Pixel16`
  promotion
- Mac shade stores match the Mac PNG after transparent-RGB zeroing
- the checked 3x3 neighborhoods disagree with Windows only at:
  - `(1699,7)`
  - `(415,393)`

Required witnesses:

- mismatch representatives:
  - `(1699,7)`
  - `(415,393)`
- matching controls:
  - `(1698,7)`
  - `(1700,7)`
  - `(414,393)`
  - `(415,394)`
  - `(416,393)`

For each witness, return same-run typed values:

- source input RGBA16 seen by the Windows effect
- source alpha / mask value used for ownership
- binary mask value before distance transform if still available
- inside/outside distance values before threshold if still available
- field value after Constant threshold, before final compose/writeback
- field value consumed by final compose/writeback
- final pre-store RGBA/word values
- final stored RGBA16
- exported RGBA16

Acceptance:

- `answered`: the return explains both `(1699,7)` and `(415,393)` as one of:
  source/mask ownership, final compose/writeback ownership, or export/path
  split, with direct typed values or clearly marked inference.
- `answered_partial`: one representative pixel is explained, or the closest
  retained frame exposes source words, consumed field, output address, and
  pre-store words for at least one representative.
- `failed_partial`: the hook/watchpoint cannot be isolated, but the return
  includes the exact failed condition/address and the closest retained frame.
- `failed`: broad callback activity, final PNG restatement only, or no
  representative-pixel binding.

Forbidden:

- do not resend the old stack/refcon package as-is
- do not retune broad field generation, Both merge, compose, or source-input
  rules from this proof
- do not use final PNG values alone as answered evidence
