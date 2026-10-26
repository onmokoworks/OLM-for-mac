status: blocked
summary:
- F54b preserves both cropped-geometry original hashes; the diagnostic Mac build preserves both saved candidate hashes.
- First observed divergence is already in the pre-B150 polar plane: complete PF16 plane and a PF32 prefix differ.
- F54b has F49 watches, not C53b's configurable resident watches: no pointer dereferences and a 1 MiB limit.
- The earlier source boundary and complete downstream planes remain unavailable through that resident interface; no causal production fix or undefined-read finding is claimed.
- Both witnesses remain unresolved; no corpus promotion, production edits, or acceptance claim.

facts:
- Base: `41369ff07d1a785849597fe57f9b294cc0b3deb0`; branch `orch/N03-radialblur-v2-mismatch`.
- Read AGENT_GUIDE, GOTCHAS, compatibility plan, RadialBlur ledger row, N02/C53b/C57 evidence, R06 trace recipe, current RadialBlur source and original decompilation. MAIN, emulator source, cache, release gate, ledger and all production sources remained read-only.
- Worker: `/Users/onmk/.cache/olm-emu/worker-F54b/aex-guest-worker`, SHA256 `e9d99f8af2dc5582e4f2faa71211b5ec2af405d26598f483768e3406034deb10`; retained source head `e96d6ed9b0a8170e1d3d427ac6cf65e07dc3144e`.
- AEX SHA256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- Initial reuse of N02's `AEXCOMPAT_RESIDENT_TRACE/WATCHES` with F54b: successful bound output for both, zero trace files. Inspection of F54b `classic.rs:5137` established the correct interface: `AEXCOMPAT_SMART_TRACE`, `AEXCOMPAT_SMART_TRACE_WATCH=hex-rva,decimal-bytes,first|all`. The parser constructs only RCX/RDX, with `dereference_offset: None`, and rejects sizes above 1048576. This is a capability distinction, not a failed arithmetic hypothesis.
- Ran `python3 orchestra/reports/N03-radialblur-evidence/trace.py --watch SPEC` for each of `56f0,272,first`, `b150,1048576,first`, `b150,16944,first`, `a9d0,1048576,first`, `9d80,1048576,first`, `a270,256,first`, `9fc0,160,first`. All commands exit 0; all 14 Smart originals bind to N02 hashes, with intact guards and clean sessions. Traces report no truncation or dropped witnesses. Summary and compressed captures are committed.
- Original hashes: PF32 `403be984da1ad8593fa159b4` = `5341e6b2646979a70e57653007a1f310169421ec9bdd9f1a5648f75ade005af1`; PF16 `ab18858afb75411545de86c7` = `5b6fb58e61fa475939767d68a446f97f1bff02c0e5935a3ea8bb51e6515783d8`.
- Ran `python3 orchestra/reports/N03-radialblur-evidence/mac.py`: exit 0. Scratch-only instrumentation dumps source, polar, source-scalar, span, normalized and public output without modifying arithmetic or admission. Both Smart candidates succeed. PF32 output SHA256 `0b1a0fb57f978ba0ea2a2ec66a4dae56eb0c2f51f9303fe7a1fb49c35cb440d3`; PF16 `ee831fd1a52ccbb49bf9d57820878689bff8b227b0db19043638866a3558ad02`. These equal N02 candidate hashes. Thus instrumentation did not repair either mismatch. The N02 final mismatch counts remain applicable by hash identity (PF32 64 words/168 bytes; PF16 40 words/54 bytes).
- Ran `python3 orchestra/reports/N03-radialblur-evidence/summarize.py`: exit 0; 14 output-bound trace runs, 65 archived files, per-file SHA256 manifest.
- PF32: Mac polar 1,708,800 bytes; original B150 RDX capture 1,048,576 bytes, all zero. All 262,144 compared words differ; first word 0, original little-endian bytes `00000000`, Mac `7c035b3f`. This is explicitly a prefix comparison, NOT a complete plane check.
- PF16: Mac polar 713,760 bytes; original B150 RDX capture covers that entire plane, all zero. 32,612 differing words; first word 0, original `00000000`, Mac `00d61a3f`.
- Original B150 context corroborates radial ranges: PF32 0..14, PF16 2..11; centers (0.5,12) and (0.5,9). Original polar pointers: `0x10021c000` and `0x1000ec000`; accumulator pointers: `0x10000f000` in each separate session. These are different allocations, not interchangeable snapshots. Full context and source-scalar/span pointer values are retained in captures.
- A270 and 9FC0 source-sampler watches each report zero witnesses with explicit `no direct call site targets the function ... not indirect calls`. D80 watches yield zero witnesses. B150/A9D0 large RCX snapshots are unmapped; their RDX snapshots capture the polar allocation, not the accumulator. The smaller B150 RCX capture succeeds.
- F54b `main.rs:116` restricts CLI `--watch`/`--watch-output-pixel` to `render-trace-png`; it is not a replacement for the typed cropped resident session. No changed-geometry or PNG substitution was used.
- No full original source, source-scalar, prepass, accumulator or final float-plane comparison was achieved. No original undefined-memory read was established.
- No mathematical patch hypotheses were tested/refuted; the two-refuted-hypotheses stop rule is not claimed as triggered. Blocker is the retained worker's missing resident capture capabilities. No worker rebuild was authorized by this ticket's reuse instructions or performed.
- Acceptance campaigns (realistic-v2 seeds 1/2/3 n200, default seed1 n300, all corpora, ref_vs_fast caps 1/2/8) were NOT run: no production fix exists, and both witnesses remain non-exact. P05b/P07e and R10 remain unchanged.
- `git diff --check` passes. Scratch is 23 MiB; diagnostic build directory was deleted. No background process remains. No /tmp writes, push, stash, history rewrite or delegation.

inference:
- The final mismatch has an upstream polar-boundary manifestation, so a final writer adjustment would be unsupported.
- All-zero original polar data does not distinguish source expansion from source sampling, and does not prove undefined memory. The earlier C57 missing-layer diagnosis must not be transferred to these witnesses without the missing captures.
- A geometry-compatible C53b-style resident capture interface is needed to identify the first differing stage and decide whether a general production fix is justified.

changed_files:
- `orchestra/reports/N03-radialblur-v2-mismatch.md`
- `orchestra/reports/N03-radialblur-evidence/{trace.py,mac.py,summarize.py,summary.json,manifest.json}`
- `orchestra/reports/N03-radialblur-evidence/captures/**`: compressed original trace/result records and Mac stage/output captures.

verify:
```sh
export TMPDIR="$PWD/orchestra/state/N03-radialblur-v2-mismatch"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
python3 orchestra/reports/N03-radialblur-evidence/mac.py > "$TMPDIR/verify-mac.log" 2>&1
for spec in 56f0,272,first b150,1048576,first b150,16944,first a9d0,1048576,first 9d80,1048576,first a270,256,first 9fc0,160,first; do
  python3 orchestra/reports/N03-radialblur-evidence/trace.py --watch "$spec" > "$TMPDIR/verify-$spec.log" 2>&1 || exit 1
done
python3 orchestra/reports/N03-radialblur-evidence/summarize.py > "$TMPDIR/verify-summary.log" 2>&1
git diff --check
```
Expected: commands exit 0; both saved Mac and original hashes reproduced; 14 bound original runs; summary reports 262144 PF32 prefix and 32612 PF16 full-plane differing words. These are stable mismatches, not acceptance passes. Summarize regenerates the committed archive and manifest; execution metadata can differ.

next:
- Instrumentation follow-up: preserve F54b geometry/arithmetic while adding C53b resident JSON watches (register + dereference offsets, at least 16 MiB snapshots), using the prescribed space-free build and durable cache registration. Do not overwrite F54b.
- Capture owner source `+0x98`, size `+0x88`, span `+0x90`, final `+0xa0`; Zoom context polar `+0x38`, scalar `+0x40`, prepass factors `+0x48/+0x50`, accumulator `+0x4210` and maximum `+0x4218`, at the appropriate before/after boundaries. Bind every capture to the retained output hashes.
- Compare source expansion first, then polar generation. If an undefined read is demonstrated, retain actual addresses/bytes and provenance; otherwise fix the causal general path. Then complete all ticket acceptance campaigns and promote the witnesses only when justified.
