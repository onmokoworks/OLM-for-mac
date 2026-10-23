status: blocked

summary:
- Reproduced Smart seed1 n300: 285 exact / 1 mismatch / 12 refusal / 2 uncompared; all 300 result dictionaries equal C18.
- No production admission or numeric change is justified by this investigation; all production sources and corpus expectations remain unchanged.
- Broad PF8 Front Fade gate removal admits a known 11-byte mismatch despite clean O2/ASan/UBSan comparisons over seed1 and fresh seed5.
- Recorded the expf call site and reproduced the PF32 nonfinite oracle/ISA boundary.
- New negative-Offset allocator evidence and final verification are recorded below.

facts:

Base: `c4a0b92a535bd3c5c4141ffef1b0eaa7d8039ab5`, branch `orch/C25-dblur-smart-r4`. Read the shared guide, DirectionalBlur ledger row (line5000), compatibility plan, GOTCHAS, T10/F05/F06/F16/C02/C09/C18 and F10/F12 method reports. MAIN, original AEX, external emulator sources and cached worker remain read-only. No release gate, ledger, production plugin/core, other-plugin code, installed bundle or corpus expectation changes. No push, stash, history rewrite or permission rejection.

Scope: original AEX CPU Smart under Unicorn and current Mac EffectMain fake host, full-frame typed ARGB. Neither Windows native AE/UCRT nor general allocator semantics are certified.

Required campaign exits0, jobs1, scratch corpus, shrink-attempts0. Smart285/1/12/2; Classic4/284/12/0 remains a separate oracle. All300 case.result dictionaries equal committed C18 pf32-after.json. Case84 differs in2 bytes/2 PF16 words, first byte2508: AEX `6841`, Mac `6941`.

Largest cluster: six negative-Offset/core refusals4/7/127/246/280/284. C18 directly established invalid sampled cells for7/127/246. This ticket runs the existing actual-builder/full-render allocator probe on4/280/284, retaining native-f32 imports and the original sampler/rowdriver. Padding variants are counterfactual host allocations, never replacement oracles. The 404-byte random table itself is identical across each case's three trials.

Allocator probe exits0. All three unmodified fixtures equal cached Smart output; all three actually sample invalid cells. Original reads at RVA37f3/37f8 index outside the404-byte table. First reads are indices-2/-3/-8 (byte offsets-8/-12/-32); all observed first values are `00000000`, without any valid-allocation guarantee.

| Seed1 case | Outside reads | Invalid cells sampled | Padding-changed field words | Padding-changed output bytes | First final byte (padding0→1) |
|---|---:|---|---:|---:|---|
|4|26|392,436,487,494,512,518,626|19|1306|1677:17→21|
|280|18|8|9|38|0:73→83|
|284|6|4|3|0|none|

This is new final-output allocator dependence for4/280, not merely field dependence. Case284's unchanged final bytes do not remove its observed invalid demand. All six residual negative-Offset cases now have actual invalid-demand evidence across C18/C25. No unsafe gate-off dereference is attempted in Mac code.

Original AEX SHA256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`; cached worker SHA256 `16ab2412c00b6ce5d61cadbf9d1cd3aa3c991f36bc66c6af8c2595c32d075e3c`. Full input/control, source/probe, instruction and output hashes are retained in the committed measurement JSON.

Front Fade admission experiment: scratch-only omission of the PF8 fallback feature predicate, preserving all core safety checks. All600 O2/sanitized pairs agree (seed1+fresh5); strict ASan/UBSan, no diagnostics. Seed1 admits73/78/175 exact and200 mismatch; fresh5 admits21/32/119/147/148/193/274 exact. All other outcomes unchanged. This rejects blanket Front Fade promotion; it does not prove neighboring tuples safe. Case200 has11 differing bytes, first byte73: AEX `31`, Mac `32`.

`ucrt-math`: paired original-AEX trace for unshrunk84 and200 binds final fixture bytes exactly to the cached worker. At84 the rotated plane agrees and8/752 Gaussian words differ. At200 rotated/map/divisor and22 strength weights agree;1/80 Fade weights differs, then1459 row-output,381 denominator and54 alpha-max words differ. expf returns to `0x180001897`; original bytes at `0x180001892` are `e8d38d0000`, CALL `0x18000a66a`. Both cases share this call site. Existing C09 paired import evidence identifies the differing expf returns; this ticket records the call address and does not pursue another math implementation. Per orchestrator instruction these wait for F28 ucrtmath integration. Apple host-libm output is not a Windows UCRT contract.

Nonfinite109/299: fresh gate-off paired trace has identical populated planes; rotation is the first captured divergent stage (440/310 words), final2942/2025 bytes. Both original fixture frames equal the cached worker. Independent original SSE instruction probe:720 conditions,704 agree with macOS x86_64 execution via Rosetta,16 differ (four each ADDSS/SUBSS/MULSS/DIVSS; MINSS zero). The prior C02 explanation remains applicable: Unicorn's NaN operand choice is not a portable native-ISA contract. No emulator-specific NaN selection was added to production.

inference:
- Residual numerical boundaries require external dependency contracts; changing Gaussian/writer arithmetic or supplying allocator padding would satisfy a particular emulator environment without establishing the required port contract.
- Three residual families were investigated, but zero clusters were closed and zero new exact cases promoted. This is blocked, not completion. The two-refutations-without-new-boundary stop rule was not reached; allocator final-output dependence is new boundary evidence. Stop because all remaining measured families reach unresolved allocator, ucrt-math or nonfinite oracle contracts.

changed_files:
- tools/fuzz/probe_directionalblur_c09_admission.py: explicit --jobs 1/2, default1 for the shared machine limit.
- tools/emulation/probe_directionalblur_c02_stages.py: record expf return addresses without changing import behavior.
- tools/emulation/probe_directionalblur_c02_sse.py: caller-selected scratch directory.
- reports/fuzz/c25_dblur_smart/: measurement evidence.
- orchestra/reports/C25-dblur-smart-r4.md

verify:
```sh
S="$PWD/orchestra/state/C25-dblur-smart-r4"
W=/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker
P='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
B=c4a0b92a535bd3c5c4141ffef1b0eaa7d8039ab5
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 1 --scratch "$S" --worker "$W" --report "$S/baseline.json" --corpus "$S/corpus" --shrink-attempts 0 > "$S/baseline.log" 2>&1
python3 tools/fuzz/probe_directionalblur_c09_admission.py --baseline "$B" --seeds 1 5 --jobs 1 --scratch "$S" --worker "$W" --report "$S/gate.json" > "$S/gate.log" 2>&1
"$P" tools/emulation/probe_directionalblur_f16_allocator.py --indices 4 280 284 --observe --expf-leaf native-f32 --scratch "$S" --worker "$W" --report "$S/allocator.json" > "$S/allocator.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --indices 84 200 --gate-off --expf-leaf native-f32 --scratch "$S" --worker "$W" --report "$S/math-sites.json" > "$S/math-sites.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_stages.py --indices 109 299 --nonfinite-off --scratch "$S" --worker "$W" --report "$S/nonfinite.json" > "$S/nonfinite.log" 2>&1
"$P" tools/emulation/probe_directionalblur_c02_sse.py --scratch "$S" --report "$S/sse.json" > "$S/sse.log" 2>&1
python3 tools/fuzz/verify_directionalblur_c02.py --baseline "$B" --seeds 1 5 --jobs 1 --corpus --scratch "$S" --worker "$W" --report "$S/verify.json" > "$S/verify.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --jobs 1 --replay tests/fuzz_corpus/olmdirectionalblur --scratch "$S" --worker "$W" --report "$S/replay.json" --corpus "$S/replay-corpus" > "$S/replay.log" 2>&1
git diff --check
```
All commands must exit0. Expected numerical differences above are deliberately retained; exact means zero differing raw bytes. Run sequentially, at most2 concurrent emulator/build processes. Oracle budget cases remain uncompared.

next:
- F28: integrate the native UCRT math contract, then re-evaluate84 and guarded Front Fade; preserve accepted Gaussian evidence.
- Negative Offset: establish native allocator-independent semantics or an independently proven narrower demand rule before changing safety refusals.
- PF32 nonfinite: resolve the native opcode/oracle NaN contract before admitting109/299; do not emulate Unicorn's implementation accident.

Final verification facts:
- `verify_directionalblur_c02.py` exits0: PASS656, both public routes O2 versus strict ASan/UBSan, zero sanitizer failures. All656 Smart result dictionaries (excluding only the added diff detail) equal baseline; every baseline-exact hash is preserved.
- Route-aware corpus replay exits0,56/56 matches_saved. No rebaseline or expectation edits.

| Smart set | Before E/M/R/U | After E/M/R/U |
|---|---|---|
|seed1 n300|285/1/12/2|285/1/12/2|
|fresh seed5 n300|271/1/25/3|271/1/25/3|
|saved corpus56|54/2/0/0|54/2/0/0|

Corpus transition table:54 exact→identical exact;2 mismatch→identical mismatch. The campaign and all probes/regression/replay completed with exit0; `git diff --check` passes. The extra fresh-seed mismatch was not investigated as a new cluster and is not assigned a cause. Temporary build contexts removed all build trees; generated scratch corpora were deleted. No background process remains from this ticket. Final scratch contains logs/reports only, 5564410 bytes (<5GiB).
