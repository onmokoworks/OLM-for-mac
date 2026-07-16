# OLMRadialBlur natural B150 entry checkpoint (2026-07-17)

- Status: `pass`
- Classification: `bounded-natural-reader-owned-nonzero-b150-table-checkpoint`
- Scope: bounded Mac Unicorn actual-AEX caller and natural polar prefill through the first B150 entry; B150 itself is not executed.
- Harness: case `case_0009`, source `32x32`, quality-step override `90.0`, cap `2000000`.
- No Python prefill, B150 detour, full-size run, Windows, AE, or production claim.

## FACT

- Actual caller reached B150 once after `4` prefill-row entries and one prefill-complete boundary in `85992` instructions.
- B150 ABI geometry is width `49`, row limit `4`, assigned `[0,5)`, effective `[0,4)`: `196` input cells.
- `FUN_180008690` owns `param_ctx+0x6c/+0x70`: actual callsites `0x180008731/0x180008785` invoke integer reader indices `5/9`, mapped to Outer/Inner Edge Fade.
- All `13` checked-in reference cases supply Edge Fade `0/0`; the case_0009 baseline reaches B150 spans `0/0` with zero inline tables.
- The minimum host-reader variation Outer Edge Fade `1` reaches B150 spans `1/0`; inline table nonzero counts are `1` and `0` of `100`.
- The harness performs zero direct writes to `param_ctx+0x6c/+0x70` and zero direct writes to `work+0x4200/+0x4204` or either B150 inline table.
- Natural prefill changes RGBA and source-alpha to `196` and `196` nonzero cells; scale remains faithfully zero.
- JSON preserves exact caller pointers, kernel-call arguments, prefill before/after hashes, representative raw float32 input words, and complete inline table words.

## INFERENCE

- The zero baseline is explained by both checked-in Edge Fade values being zero. The paired fixture proves the smallest positive host parameter naturally propagates through the actual reader, core span owner, and table builder.
- This does not establish full-size values, Windows equivalence, B150 output equivalence, or any claim for spans greater than one.
