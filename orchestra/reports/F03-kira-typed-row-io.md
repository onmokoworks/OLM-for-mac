status: blocked

summary:
- Implemented byte-copy pixel reads/writes and proved the AEX byte-row addressing contract on bounded worlds.
- Removed typed-alignment and fixed `+12` padding guards after sanitizer-clean gate-off evidence; added address-span overflow validation.
- Focused public tests: 78 refusals become exact; 54 exact and 12 existing mismatches retain their bytes. Production fuzz stays 0 exact / 300 refused per route.
- Final all-gates-off ASan/UBSan: Classic 184 exact / 103 mismatch; Smart 85 exact / 52 mismatch / 163 refused; zero sanitizer errors.
- Full ticket acceptance is blocked: C28 and other numerical mismatches persist, and two saved production corpus records differ only in callback counts. Corpus was not updated.

facts:

Base commit: `ae28f1391011edb08bf707bd28fe23e5cb8fb645`, branch `orch/F03-kira-typed-row-io`. Read `AGENT_GUIDE.md`, emulator GOTCHAS, the compatibility plan, KiraKira restrictions, and T06. No release gate, ledger, other plugin, MAIN file, or emulator source was changed. No worker was rebuilt.

Machine evidence: `reports/fuzz/olmkirakira_row_io_F03.json`. It retains focused per-layout outcomes, intermediate source-plane/writer hashes, corpus replay records, build identities, campaign summaries, canonical result-array digests, and boundary cases. All campaigns completed at seed 1, n=300, jobs=2. Reproduction commands below regenerate the full campaign reports in scratch.

Original AEX SHA256: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
Retained public worker SHA256: `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`, at `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker` (the existing T06/default worker). The cache INDEX was inspected; it lists radial-specific workers, not this retained KiraKira session worker. MAIN's original `plugins_2025/OLMKiraKira.aex` and emulator Python venv were used by absolute path.

Host/row contract, observed rather than inferred:

- Original disassembly in MAIN `disasm/OLMKiraKira.aex.asm.txt`: PF8/PF16/PF32 address leaves `1812309f0`, `181230a20`, `181230a50` compute `data + y*rowbytes + x*(4/8/16)`. World data and rowbytes are at offsets `+0x18`, `+0x20`. The multiply is signed 32-bit before sign extension; this probe does not certify large wrapped offsets.
- Original reader leaves `181230a80`, `181230af0`, `181230b60` load ARGB scalar bytes/words/dwords and produce float RGBA. Integer conversion retains the binary reciprocal multiplication; PF32 reorders words. Original writer leaves `181230b90`, `181230bd0`, `181230c20` store ARGB bytes/words/dwords, with the integer multiply/truncate order unchanged.
- Used `aex_witness.leaf_check` and the actual AEX under Unicorn, without numerical detours. Sixty combinations: 3 depths × padding {0,1,3,7,16} × base offsets {0,1,2,3}, each a 3×3 world. All 540 pixel addresses, 2,160 decoded float words and 2,160 writer samples match the Mac IO probe byte-for-byte. Input bytes and destination non-pixel bytes remain unchanged. Each of the 60 final probes also checks nine invalid-layout predicates, including nulls, zero/negative stride, short rows, zero dimensions and pointer-end overflow, plus valid layout acceptance.
- The local port contract requires a non-null host-owned buffer, positive dimensions/stride, active bytes fitting each row and a representable last active-byte span. Input/output strides and base alignment are independent. Existing geometry, format, tuple/source, extent, world flags and overlap rules remain. The API cannot prove actual allocation size; that remains the host's obligation. Negative strides are still rejected.
- These are CPU AEX leaf and fake-SDK-host facts. Native AE's production of odd strides, negative stride semantics, huge allocations and arbitrary wrapped AEX row offsets remain unverified. Packed public oracle renders alone are not evidence of native odd-stride support.

Production fix:

- Replaced both typed-pointer helpers with `LoadWorldPixel` / `StoreWorldPixel`, using `memcpy` and aligned local values. Updated `ReadPixels`, render output, exact-source admission and generic finite-SDR admission (all seven dereference sites).
- Removed alignment-only rejection and the two Classic / one Smart fixed-padding predicates. Full-frame/source/tuple restrictions are unchanged. `WorldLayoutIsSafe` now also checks the data address plus active span for overflow.
- The T06 triage script recognizes that the alignment predicate no longer exists; its experiment remains scratch-only and does not bypass span checks. Updated one existing source assertion to name the new store helper, preserving its writer-owner check.

Measured campaigns (E/M/R/U = exact/mismatch/refusal/uncompared):

| Campaign | Classic E/M/R/U | Smart E/M/R/U | Sanitizer aborts C/S |
|---|---|---|---|
| Fresh production before | 0/0/300/0 | 0/0/300/0 | not enabled |
| Fresh production after | 0/0/300/0 | 0/0/300/0 | not enabled |
| T06 all gates off, ordinary build (retained) | 184/103/0/13 | 84/52/164/0 | not enabled |
| T06 all gates off, ASan/UBSan (retained) | 121/72/0/11 | 51/31/164/0 | 96/54 |
| Copy-only change, all gates off, ASan/UBSan | 184/103/0/13 | 84/52/164/0 | 0/0 |
| Final change, all gates off, ASan/UBSan | 184/103/0/13 | 85/52/163/0 | 0/0 |

Every campaign had 287 AEX successes / 13 AEX rejections. No production exact count decreased. Copy-only sanitized results equal **all 300 complete T06 ordinary gate-off result dictionaries**, not merely their counts. Final gate-off changes only index 66: Smart refusal → exact (Classic was already exact); all other result dictionaries match T06. The remaining AEX rejections are the existing unsupported/bad dependency cases, not comparable outputs.

After production guard relaxation, the 254 observed alignment refusals disappear, but those random inputs meet later guards: Classic 300 tuple/layout/source refusals; Smart 163 request and 137 tuple/source refusals. All 600 production route statuses and all AEX records are unchanged. Of 300 complete result dictionaries, 218 are identical; 82 Smart records now have balanced parameter checkout/checkin counts where the earlier alignment guard performed none.

Focused public oracle comparisons, using independent input/output padding and base offsets, both routes, all three depths:

| Source/tuple set | Existing exact retained | Refusal → exact | Existing mismatch retained | Sanitizer errors |
|---|---:|---:|---:|---:|
| 5×3 closure, 9×7 and 17×11 m1_h7; six layouts each | 34 | 62 | 12 | 0 |
| 32×18 m3_h50 closure; six layouts each | 20 | 16 | 0 | 0 |

The first row was measured with layout gates disabled in a scratch copy **before** production relaxation: every newly unblocked result was exact. Final production matches that experiment. The 32×18 run additionally validates both the exact-source and generic paths after relaxation. The 12 unchanged mismatches are all 17×11 PF8 (six layouts × two routes), already admitted by the old code. First difference is byte 306 = (8,4), green, AEX `54`, Mac `55`; exactly one byte differs. AEX hash `67d32449ae837cc4ab3bbd172703ad960ecb672c1d1b31c58aac76787fc18c66`, Mac hash `e8c7f99c3609a98700004db086479731323383a4c49e8dabc9ae20e98b482910`, identical across all layouts.

Corpus replay before/after table (saved production corpus → fresh final replay):

| Fixture index | Classic status | Smart status | Smart COUNTS before → after | Complete saved result equal |
|---|---|---|---|---|
| 0 | refusal → refusal | refusal → refusal | `1 1 1 26 26` unchanged | yes |
| 1 | refusal → refusal | refusal → refusal | `0 0 0 0 0` unchanged | yes |
| 2 | refusal → refusal | refusal → refusal | `1 1 1 0 0` → `1 1 1 25 25` | no |
| 3 | refusal → refusal | refusal → refusal | `1 1 1 0 0` → `1 1 1 26 26` | no |
| 7 | refusal → refusal | refusal → refusal | `1 1 1 27 27` unchanged | yes |
| 8 | refusal → refusal | refusal → refusal | `0 0 0 0 0` unchanged | yes |
| 16 | refusal → refusal | refusal → refusal | `0 0 0 0 0` unchanged | yes |
| 38 | refusal → refusal | refusal → refusal | `1 1 1 26 26` unchanged | yes |

No corpus files were updated. The strict production replay exits 1: **6/8 complete-result matches**, with identical refusal/error codes, AEX hashes and untouched outputs in all eight. These two changes are lifecycle metadata, not changes toward exact; therefore this report does not claim the literal corpus acceptance requirement passed. Do not silently bless them by updating expected records.

The separate shrunk gate-off T06 corpus replays **62/62 complete saved results under ASan/UBSan**, exit 0. That preserves, rather than resolves, the arithmetic mismatches. C28/seed-1 index 3 is now memory-safe but remains a one-word mismatch on both routes: shrunk witness byte 6998 = (16,22), blue, AEX little-endian `125a`, Mac `115a`; Mac hash `911bbe5662b0f0dda25483e577665a3998fa815d0d86508345dcddd80bf91689`. No outside-port cause has been proven. No numerical hypothesis was tuned or expected-value patch added.

Existing fast tests: 25 passed (generic-beta lane 9, merge2 float oracle 6, outer compose oracle 9, bounded writer-owner source assertion 1). Parameter-surface tests initially failed setup because their untracked manifest is absent in the worktree; redirecting only that read-only manifest to MAIN gives 5/5 passed, with Mac inputs still from this worktree. The new probe initially had a C++ `PixelTraits` namespace ambiguity; corrected by placing its helper in the same anonymous namespace. These were harness/build issues, not AEX numerical hypotheses.

inference:

- The misaligned typed references were C++ undefined behavior introduced by the port's access pattern; the original scalar AEX access leaves impose no corresponding alignment restriction over the probed spans. Byte copies remove this cause without changing arithmetic.
- The unchanged aligned/unaligned numerical mismatches originate after or outside this IO operation. Their algorithmic cause is not established here; a full-render internal stage trace is needed. In particular, fixing the sanitizer abort is not proof that C28 became exact.
- The observed newly admitted focused layouts justify the layout-only relaxation for the existing supported render families. This is not a claim of all-input AEX or native-AE compatibility.
- Overall status remains blocked because acceptance (1) requires the targeted shrunk witness to become exact or a proven outside-port cause, and strict acceptance (3) does not permit silently updating refusal-only metadata changes. The safety fix and its layout evidence are ready for orchestrator review; no permission request is needed.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_typed_row_io_F03.py`
- `tools/fuzz/triage_kirakira.py`
- `tests/test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.py`
- `reports/fuzz/olmkirakira_row_io_F03.json`
- `orchestra/reports/F03-kira-typed-row-io.md`

verify:

Run in this worktree. These commands use only ticket scratch for generated files. Baseline retrieval is read-only; no history is rewritten. The full run commands below are the commands actually used, with the optional scratch report names normalized for reproduction.

```sh
s="$PWD/orchestra/state/F03-kira-typed-row-io"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show ae28f1391011edb08bf707bd28fe23e5cb8fb645:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"

"$py" tools/emulation/probe_kirakira_typed_row_io_F03.py --source "$s/before.cpp" --scratch "$s/layout-before" --report "$s/layout-before.json" --sanitizers > "$s/layout-before.log" 2>&1
"$py" tools/emulation/probe_kirakira_typed_row_io_F03.py --scratch "$s/layout-after" --report "$s/layout-after.json" --baseline-report "$s/layout-before.json" --sanitizers > "$s/layout-after.log" 2>&1
"$py" tools/emulation/probe_kirakira_typed_row_io_F03.py --source "$s/before.cpp" --scratch "$s/mode3-before" --report "$s/mode3-before.json" --mode3-closure --sanitizers > "$s/mode3-before.log" 2>&1
"$py" tools/emulation/probe_kirakira_typed_row_io_F03.py --scratch "$s/mode3-after" --report "$s/mode3-after.json" --baseline-report "$s/mode3-before.json" --mode3-closure --sanitizers > "$s/mode3-after.log" 2>&1

python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 2 --scratch "$s" --report "$s/verify-production.json" --corpus "$s/verify-corpus" > "$s/verify-production.log" 2>&1
python3 tools/fuzz/triage_kirakira.py --experiment all --sanitizers --plugin olmkirakira --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/verify-sanitized.json" --corpus "$s/verify-gate-off-corpus" > "$s/verify-sanitized.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/verify-corpus.json" --corpus "$s/verify-corpus" > "$s/verify-corpus.log" 2>&1
# Expected exit 1 for the preceding strict metadata replay; continue explicitly.
python3 tools/fuzz/triage_kirakira.py --experiment all --sanitizers --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira_gate_off_T06 --scratch "$s" --report "$s/verify-clusters.json" --corpus "$s/verify-corpus" > "$s/verify-clusters.log" 2>&1

PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820 test_olmkirakira_merge2_float_oracle_20260728 test_olmkirakira_outer_compose_oracle_20260728 test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.Mode4FullCallerHostlessExactTests.test_mac_production_owns_the_bounded_highlight_and_typed_writer > "$s/fast-tests.log" 2>&1
PYTHONPATH=tests python3 - <<'PY' > "$s/surface-tests.log" 2>&1
import unittest
from pathlib import Path
import test_olmkirakira_parameter_surface_contract_20260717 as test
main=Path.cwd().parent.parent
test.contract.ROOT=main
test.contract.load_windows_surface.__defaults__=(main/'refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMKiraKira/reference_manifest.json',)
r=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(test))
raise SystemExit(not r.wasSuccessful())
PY
git diff --check
```

Expected: focused summaries `60 leaf exact; 96 public exact / 12 unchanged mismatch; 62 refusal→exact` and `60 leaf exact; 36 public exact; 16 refusal→exact`; production `0 exact / 300 refusals` on each route; sanitized final `184/103/0/13` Classic and `85/52/163/0` Smart with zero sanitizer errors; strict production corpus 6/8 matches (exit 1), shrunk corpus 62/62 (exit 0); fast tests 25/25 and surface 5/5. The earlier fresh baseline was the same production command with `before.json` / `before-corpus`, run before edits. Copy-only gate-off results and the pre-relaxation layout experiment remain hash-bound in the machine evidence.

next:
- Follow-up numerical ticket: localize C28's first differing internal value (retain its exact shrunk input); do not tune the writer or accept a tolerance. Keep the other T06 arithmetic clusters separate from IO.
- Orchestrator must explicitly reconcile the two refusal-only corpus lifecycle changes before approving an expectation update; this worker did not change them.
- Validate native AE layout guarantees and additional modes/layout combinations separately if broader native-host compatibility is required. No native AE run, deployment, push or merge was performed.
