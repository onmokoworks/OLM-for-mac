status: done
summary:
- Bound real F46-derived resident Smart traces to all four C51 public outputs, byte for byte.
- Restored SSE NaN operand order/sign, scatter MAXSS selection, ordered-positive component masks, and PF32 MINSS writeback.
- All four witnesses now match at populated, rotated, inverse-input, writer-plane, and final-output boundaries.
- Seed 1/104/fresh 219 n300: 893 Smart exact, 0 mismatch, 0 refusal, 7 oracle timeouts; O2/ASan/UBSan agree on all 900.
- Removed only the generic PF32 feature finite-input gate; corpus replay preserves 83/83 saved results.

facts:

FACT: Base `dab0232d7f5a3b295cd664d57c242b84fe00bdb0`, branch
`orch/F49-dblur-nonfinite-pf32`. Read C51 and its retained evidence, AGENT_GUIDE,
GOTCHAS, the DirectionalBlur ledger row and compatibility plan. MAIN,
04_Tools/AEXCompat*, release gates, forbidden-action lists, corpus expectations,
and other plugins' implementation files were not changed. Existing x86_float
helper behavior is retained; new SSE helpers are opt-in.

FACT: Oracle scope is original 2025 CPU AEX in Unicorn versus the public Mac
EffectMain fake SDK host, typed ARGB, origin zero, Smart. No native AE or native
Windows claim. AEX SHA256:
`d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
F46 SHA256:
`6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.

FACT: `build_F49.py --first-only` and `build_F49.py` copy the hash-verified F46
source snapshot. The only worker changes enable opt-in resident SMART_RENDER
checkpoint watches, serialize the trace to a separate file, and raise the
read-only snapshot limit. No math/host/import semantics are changed.
The first build recipe had an assertion before Cargo because the snapshot-limit
constant was in x64.rs, not x64/types.rs; this was corrected before building.
Both Rust builds exited 0, with one pre-existing dead-code warning, jobs=1,
memory free 45% and 50% respectively. Build trees were deleted. Durable binaries,
source snapshots and build manifests are in the cache, with locked INDEX entries:

| Worker | SHA256 |
|---|---|
| `~/.cache/olm-emu/worker-F49-trace/aex-guest-worker` | `44257f7a9244f351d1603d8796bc4b32433f24be053a07109cc152440e15c344` |
| `~/.cache/olm-emu/worker-F49-trace-v2/aex-guest-worker` | `25e57ac6b6ebbb26b68bb0631b9e1b8d8a7daf7290a03d9cd04e37cd87bb0c9d` |

The first worker captures the first RGBA rotation. V2 captures both rotations,
including the complete plane entering inverse rotation and leaving it. The
original AEX stores the latter pointer at context+0x8090 (0x636d), which the
PF32 writer reads (0x6bd0). Traces have no unhookable watches. For each of the four
inputs, regenerated input hashes and untraced F46 output hashes equal C51;
both traced workers' complete output hashes equal untraced F46. Final probe
asserts binding before using any captured values. The Python fixture is not
used as an arithmetic oracle.

FACT: Baseline populated planes match completely. The first observed divergent
stage is RGBA rotation for every witness. The first differing float words all
have AEX `ffc00000` versus Mac `7fc00000` (hex integer bit notation):

| Seed:index | Plane bytes | Baseline differing rotation words | First word index | Baseline differing final words | Final differing words |
|---|---:|---:|---:|---:|---:|
| 1:109 | 14880 | 449 | 521 | 969 | 0 |
| 1:299 | 7744 | 297 | 456 | 728 | 0 |
| 104:137 | 61504 | 167 | 7660 | 360 | 0 |
| 104:271 | 1296 | 18 | 121 | 30 | 0 |

FACT: Causal changes and measurements, with static instruction bytes retained:
- Rotation 0x204e..0x21b7: SSE generated invalid NaNs are negative; arithmetic
  selects the first NaN operand and quiets it. Red TR/BL multiply weight first;
  green/blue sums start at TR. Restoring these makes all four first-rotation
  planes exact, while final differences remain 880/634/320/27 words.
- With exact rotation, 104:137 also has an exact writer-entry plane. Its output
  difference is the MINSS(value,1) selection at 0x6c21/0x6c2c/0x6c34: unordered
  selects operand two. Gain is operand one in the preceding MULSS instructions.
- Row SSE arithmetic plus that writer correction leaves 100/53/0/2 final
  differing words. Scatter 0x1576..0x15c1 adds the newly weighted contribution
  before the accumulated destination and uses MAXSS(destination,contribution).
  Restoring both makes 1:109 exact at inverse-input, writer-plane and final;
  remaining final differences are 0/43/0/6 words.
- Component mask 0x618a COMISS followed by SETA is ordered `alpha > 0`.
  The previous `!(alpha <= 0)` admitted NaNs. Excluding NaNs from component
  membership makes the remaining two witnesses exact at inverse-input,
  writer-plane and final. The generic implementation applies to all coordinates.

No tolerance, coordinate table, output-byte correction or expectation rebaseline
was used. Every refinement gained an exact intermediate or final boundary;
the two-refuted-hypotheses-without-a-new-boundary stop condition was not reached.

FACT: Final campaigns all exited 0 and completed 300/300, jobs=1,
shrink-attempts=0, default 10-second oracle timeout:

| Seed | Smart exact | mismatch | refusal | uncompared |
|---|---:|---:|---:|---:|
| 1 | 298 | 0 | 0 | 2 |
| 104 | 297 | 0 | 0 | 3 |
| 219 (fresh) | 298 | 0 | 0 | 2 |

Uncompared entries are original Smart oracle timeouts, not successful numerical
comparisons. Classic diagnostics remain outside this ticket: exact/mismatch
counts are 4/296, 4/296 and 12/288. The final saved-corpus replay exits 0 with
`requested=83`, `replay_matches_saved=true`, using each saved hash-bound worker.

FACT: `verify_directionalblur_f49.py` exits 0: 900 public Smart O2/sanitized pairs
have identical status and raw bytes. All 900 hashes also equal the corresponding
campaign candidate hashes. ASan/UBSan halt-on-error flags are enabled; no
sanitizer diagnostic occurred. The existing UCRT static-library build is reused;
this does not claim instrumentation of that dependency. `check_f49_float.py`
exits 0: 1,350 operand/operation combinations for ADD/SUB/MUL/DIV/MIN/MAX match
literal x86 SSE under macOS Rosetta, in both arm64 O2 and ASan/UBSan builds.
The latter is ISA-helper validation, not a native Windows claim.

FACT: Final compressed reports, all four complete V2 traces and Mac/AEX planes,
static instruction evidence, intermediate measurements and both worker build
manifests are in `orchestra/reports/F49-evidence/`. `manifest.json` hashes
uncompressed bytes. All started processes completed. Scratch is below 5 GiB;
regenerable compiler trees were removed. `git diff --check` passes.

inference:

INFERENCE: These witnesses support general SSE arithmetic and comparison
selection semantics, rather than input-specific admission exceptions. The
finite gate is lifted only on the generic feature route exercised here. The
separate neutral PF32 nonfinite guard remains; it has a different implementation
and is not proven by this ticket. Finite random coverage and these retained
planes do not prove all possible PF32 payloads or native AE behavior.

changed_files:
- `core/x86_float.h`
- `core/dblur_rotate.cpp`
- `core/dblur_rowdriver.cpp`
- `core/dblur_frontonly.cpp`
- `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`
- `tools/emulation/probe_directionalblur_c02_stages.py`
- `tools/emulation/aexcompat_patches/build_F49.py`
- `tools/emulation/probe_directionalblur_f49.py`
- `tools/emulation/check_f49_float.py`
- `tools/emulation/capture_f49_static.py`
- `tools/fuzz/verify_directionalblur_f49.py`
- `orchestra/reports/F49-evidence/*`
- `orchestra/reports/F49-dblur-nonfinite-pf32.md`

verify:

Run sequentially from this worktree; use the registered cached workers (no
rebuild required). Expected: all commands exit 0; four fully bound/exact stage
probes; 1350+1350 exact helper comparisons; 900 sanitizer matches; campaign
Smart mismatch/refusal zero; saved replay 83/83 unchanged. Timeout counts may
vary with machine load.

```sh
S="$PWD/orchestra/state/F49-dblur-nonfinite-pf32"
P='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
"$P" tools/emulation/probe_directionalblur_f49.py > "$S/final-probe.log" 2>&1
python3 tools/emulation/check_f49_float.py > "$S/float.log" 2>&1
"$P" tools/emulation/capture_f49_static.py > "$S/static.log" 2>&1
for seed in 1 104 219; do
  python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed "$seed" --jobs 1 --scratch "$S/seed$seed" --report "$S/seed$seed.json" --corpus "$S/corpus$seed" --shrink-attempts 0 > "$S/seed$seed.log" 2>&1 || exit
done
python3 tools/fuzz/verify_directionalblur_f49.py > "$S/sanitizer.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --replay tests/fuzz_corpus/olmdirectionalblur --jobs 1 --scratch "$S/replay-final" --report "$S/replay-final.json" > "$S/replay-final.log" 2>&1
git diff --check
```

next:
- No remaining blocker for the four C51 generic-feature refusals.
- Separate follow-up: prove the neutral PF32 nonfinite route before removing its
  independent guard; investigate oracle-budget cases with adequate budgets.
- Native AE/Windows and wider arbitrary-payload coverage remain separate work.
