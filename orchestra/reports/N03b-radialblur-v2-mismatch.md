status: blocked
summary:
- F54c exposes an original-AEX uninitialized Layer destination that overwrites the primary input world in both witnesses.
- The destination is 0x1000000001; the input descriptor begins at 0x1000000000. Its dimensions/data pointer are erased before the typed owner runs.
- Both traced outputs reproduce N03 hashes. Full requested polar/scalar windows and earlier descriptor/source boundaries are retained.
- No causal Mac sampling fix is justified by this allocator-dependent original memory corruption; no production change or corpus promotion.
- Acceptance remains unmet; general cropped-origin sampling was not established as the cause.

facts:
- Base: 118dd1365943287e95d1004e81b4477336416e12; branch orch/N03b-radialblur-v2-mismatch. Read AGENT_GUIDE, GOTCHAS, compatibility plan, RadialBlur ledger restrictions, N03, F54c, C57, R06 and original decompilation.
- Worker SHA256: 3d5eec0c6792f176a9cfbc38093c53b852f4ea1baae2cfd313345c02f55d6fba; original AEX SHA256: ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb. F54c remains experimental per its existing qualification; no worker rebuilt or changed.
- `PYTHONDONTWRITEBYTECODE=1 python3 orchestra/reports/N03b-radialblur-evidence/mac.py`: exit 0. Scratch instrumentation of current source reproduces both prior candidate hashes, PF32 0b1a0fb57f978ba0ea2a2ec66a4dae56eb0c2f51f9303fe7a1fb49c35cb440d3 and PF16 ee831fd1a52ccbb49bf9d57820878689bff8b227b0db19043638866a3558ad02. Build removed in finally block.
- `PYTHONDONTWRITEBYTECODE=1 python3 orchestra/reports/N03b-radialblur-evidence/trace.py`: exit 0. Expanded capture configurations sequentially from source/polar, through source-world/typed-owner, to builder/Layer-copy. Every invocation bound both original output hashes. Final configuration yields 21 PF32 and 24 PF16 before/after witness pairs, no truncation, no dropped witnesses and no reported unhookable sites. Raw exports equal JSON hex (checked by summarize.py).
- Original PF32 output SHA256: 5341e6b2646979a70e57653007a1f310169421ec9bdd9f1a5648f75ade005af1; PF16: 5b6fb58e61fa475939767d68a446f97f1bff02c0e5935a3ea8bb51e6515783d8. Both statuses ok, guards intact, sessions clean; output rectangles [0,0,1,16] and [0,6,1,16].
- At builder 8690 entry, context+A8 already contains 0x1000000001 in BOTH cases. At D9D0 entry R9 has that same destination. At 19F20 entry RDX has that same address; its 120 bytes become entirely zero on return.
- The overwritten region starts one byte into the input descriptor. Before that write, captured descriptor fields are PF32 data=0x40000840, rowbytes=17, width=1, height=16; PF16 data=0x400008d0, rowbytes=24, width=1, height=10. These fields are read at offsets relative to destination+1, not guessed from the pixel payload.
- At typed owner 7D30 / 6D10 entry, R8=0x1000000000 and the complete 128-byte input descriptor capture is zero. The pointer itself is preserved; the object it addresses has been destroyed. At 56F0 the owner input pointer remains 0x1000000000 with the same zero descriptor.
- First source-window word: PF32 original 00000000 vs Mac dee2773f; 62/64 words differ in 256 bytes. PF16 original 00000000 vs Mac 00bcb63e; 34/40 words differ in 160 bytes. These are requested memory windows through owner+98, NOT proof of valid original source allocation extents: the original input dimensions are already zero. Initial exploratory PF16 request used the full payload height18 (288 bytes); corrected to checkout height10 (160 bytes) before retained comparisons.
- Pre-B150 polar windows: PF32 1,708,800 bytes, 427,200 differing words, first original 00000000 / Mac 7c035b3f. PF16 713,760 bytes, 32,612 differing words, first original 00000000 / Mac 00d61a3f. Scalar windows: PF32 427,200 bytes / 106,800 differing words; PF16 178,440 bytes / 8,153 differing words. Source, scalar and polar original windows are all zero. Sizes cover the complete corresponding Mac planes; zeroed original geometry prevents treating these as healthy original logical planes.
- B150 before/after captures also retain context, prepass, span, accumulator and maximum; A9D0 accumulator and 56F0 final windows are retained. The 9D80 function watch produced zero witnesses, as did source-conversion 17360/173D0. Missing watch IDs are explicit in summary.json; absence is not successful coverage. 17290/172C0 captured output-writer calls, not source-conversion calls.
- `PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/static_radialblur_C57.py --output orchestra/state/N03b-radialblur-v2-mismatch/static`: exit 0, 4287 lines, original hash asserted. Compressed complete disassembly and metadata retained.
- Static facts: Smart 40F0 puts context at RSP+40, initializes checkout-pointer slots but does not initialize context+A8. 88B0 selects Type3; 88B6 loads R9 from context+A8. D9D0 passes the destination to 19F20, whose seven 16-byte stores and final 8-byte store copy 120 descriptor bytes. The typed source loops and allocations use input-world dimensions. This confirms an uninitialized pointer read and a destructive write, not a polar-coordinate arithmetic difference.
- `PYTHONDONTWRITEBYTECODE=1 python3 orchestra/reports/N03b-radialblur-evidence/summarize.py`: exit 0; validates bindings, all raw/hex snapshots, corrupt descriptor addresses and values; retains compressed captures, comparison counts and file hashes.
- No mathematical patch hypothesis was refuted. New earlier boundaries were obtained; the two-refuted-hypotheses stop rule was not triggered. Stop reason is demonstrated original undefined memory behavior with no general defined sampling correction to implement within this ticket.
- Acceptance campaigns (realistic-v2 1/2/3 n200, default 1 n300, all corpora, ref_vs_fast 1/2/8) were NOT run: production is unchanged and the two required witnesses remain mismatches. No exactness or acceptance claim.
- Scratch 67 MiB before final packaging; durable evidence approximately 2.1 MiB. No background process or build tree remains. No MAIN/cache/emulator/production/other-plugin/release-gate/ledger edits, /tmp writes, stash, push, history rewrite or delegation.

inference:
- The C57 uninitialized Layer destination defect now aliases a live primary world in these realistic-v2 sessions. The fact that both addresses match numerically is observed; dependence on broader allocator/stack history is an inference grounded in the uninitialized pointer and overlapping write.
- Source expansion is skipped after the input descriptor is erased. Reading zeros from the subsequent source memory window does not establish a legitimate zero-source rule or a portable allocation contract.
- Emulating this numeric address alias with a width/height/coordinate special case would violate the general-cause requirement. Unlike C57's empty-layer span rule, this failure destroys unrelated primary host state. Changing Mac sampling to zero these witnesses would encode host memory corruption, not recovered sampling semantics.
- Correct next scope is original/oracle undefined-behavior qualification and independent non-aliasing controls. No native AE behavior or universal allocator behavior is claimed.

changed_files:
- orchestra/reports/N03b-radialblur-v2-mismatch.md
- orchestra/reports/N03b-radialblur-evidence/{mac.py,trace.py,summarize.py,summary.json,manifest.json,original.asm.gz,static.json.gz}
- orchestra/reports/N03b-radialblur-evidence/captures/** (compressed full trace/watch/result records and Mac stages)

verify:
```sh
mkdir -p "$PWD/orchestra/state/N03b-radialblur-v2-mismatch"
export TMPDIR="$PWD/orchestra/state/N03b-radialblur-v2-mismatch"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 orchestra/reports/N03b-radialblur-evidence/mac.py > "$TMPDIR/verify-mac.log" 2>&1
python3 orchestra/reports/N03b-radialblur-evidence/trace.py > "$TMPDIR/verify-trace.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/static_radialblur_C57.py --output "$TMPDIR/static" > "$TMPDIR/verify-static.log" 2>&1
python3 orchestra/reports/N03b-radialblur-evidence/summarize.py > "$TMPDIR/verify-summary.log" 2>&1
git diff --check
```
Expected: all exit 0; both original and candidate hashes above; 45 witness pairs; Layer copy at 0x1000000001 clears the input descriptor at 0x1000000000 in both. Source-window differing words 62 and 34; polar 427200 and 32612. These reproduce a blocked mismatch, not an acceptance pass. Execution metadata may differ on regeneration.

next:
- Follow-up ticket for reference/original undefined behavior: preserve the corrupt baseline, vary allocator placement or poison the uninitialized context in a diagnostic worker, and capture the same builder/destination/input boundaries. Do not silently replace existing oracle evidence or call a passing alternate allocation AE exact.
- Obtain independent Type3/cropped controls whose Layer destination does not alias the primary world before proposing any general production rule. Any native-AE claim needs a SOFTWARE capture with valid host-state evidence.
- Keep both witnesses unresolved and all acceptance criteria pending. No source fix or corpus reclassification is requested for merge on this evidence alone.
