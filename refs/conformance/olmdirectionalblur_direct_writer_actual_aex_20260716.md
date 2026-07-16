# OLMDirectionalBlur direct-writer actual-AEX regression

- Status: `pass_actual_aex_writer_contract`
- Binary: `plugins_2025/OLMDirectionalBlur.aex` (`d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`)
- Entry: `0x180006b30`
- Scope: isolated 8bpc output callback semantics only; not AE exact.

## Static FACT

- `objdump` of the real binary matches the expected `0x180006b30..0x180006bc9` writer body.
- The callback reads `params+0x8090`, `params+0x28`, `params+0x8098`, `params+0x809c`, and `params+0x80a0`.
- RGB channels hit `MINSS` before `*255` and `CVTTSS2SI`; alpha skips `MINSS` and is stored with `MOVB` too.
- The store order is `A/R/G/B` at byte offsets `+0/+1/+2/+3`.

### Exact static lines

- `movq	0x8090(%rcx), %r9`
- `movss	0x28(%rcx), %xmm5`
- `imull	0x80a0(%rcx), %eax`
- `addl	0x809c(%rcx), %eax`
- `addl	%edx, %eax`
- `shll	$0x2, %eax`
- `minss	%xmm0, %xmm5`
- `movss	0xc(%r9,%rcx,4), %xmm3`
- `cvttss2si	%xmm5, %eax`
- `cvttss2si	%xmm3, %eax`
- `movb	%al, 0x1(%rcx)`
- `movb	%al, 0x3(%rcx)`
- `movb	%al, 0x2(%rcx)`
- `movb	%al, (%rcx)`

## Actual-AEX FACT

- `rgb_half_tie_truncation`: observed `[171, 127, 127, 127]` from target RGBA `[0.5, 0.5, 0.5, 0.6705882549285889]` at biased index `0` after `35` instructions.
- `rgb_clamp_alpha_unclamped_store`: observed `[62, 255, 153, 255]` from target RGBA `[0.75, 0.30000001192092896, 0.8999999761581421, 1.25]` at biased index `0` after `35` instructions.
- `biased_index_complete_overwrite`: observed `[63, 127, 255, 0]` from target RGBA `[0.5, 1.0, 0.0, 0.25]` at biased index `84` after `35` instructions.

## Coverage

- `rgb_half_tie_truncation`: `0.5 * 255 = 127.5` stores `127`, proving truncation.
- `rgb_clamp_alpha_unclamped_store`: RGB above `1.0` clamps to `255`, while alpha `1.25` stores the low byte of `318` (`62`) because it is not RGB-gained or clamped first.
- `biased_index_complete_overwrite`: non-zero `row0=3`, `col0=5`, `stride=11` selects the intended source cell and overwrites all four destination bytes.

## Remaining Windows Same-Run Blocker

- This harness proves the isolated callback rule only. The remaining missing same-run Windows fact is a live writer-entry capture at `OLMDirectionalBlur+0x6b30` on the real residual lane, so we can prove which RGBA floats the full render passes into the callback before the byte stores.
- Until that same-run writer-entry witness exists, this direct-writer pass does not close the full-render row-755 / host-column-1308 residual lane and does not justify any production change.

Reproduction: `python3 tools/emulation/test_dblur_direct_writer_actual_aex_20260716.py`
