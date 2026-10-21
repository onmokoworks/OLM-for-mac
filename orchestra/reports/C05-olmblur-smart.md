status: done

summary:
- Restored the original Smart Smoothness getter: signed PF_Fixed high word -> float, shared by generic and retained-fixture owners.
- Seed 1 Smart improves 89/26/185 -> 102/13/185 exact/mismatch/refusal; fresh seed 3 improves 95/28/177 -> 107/16/177.
- Closed four saved mismatch clusters (15 corpus cases); all 184 base-exact campaign cases and all Classic results are unchanged.
- Paired public-AEX/Mac contexts, 30 boundary traces, 1,200 sanitized campaign routes, 78 sanitized corpus routes and 12 retained controls pass.
- One common getter correction closes all four clusters atomically; no admission or numerical worker changes. Stop at the ticket's three-cluster threshold.

facts:

Base `ad206f003a9908e1c7a77bdda1de665d543dd996`, branch `orch/C05-olmblur-smart`. Read `AGENT_GUIDE.md`, the OLMBlur ledger rows/forbidden actions, compatibility plan, emulator GOTCHAS, T09/F15/F17/F18 and F10/F12 methodology. MAIN, external emulator source and cached workers were read-only. No reference-worker rebuild, release-gate/ledger/other-plugin edit, install, push or history rewrite. All scratch is under this ticket (12 MiB at validation); temporary build directories are automatically deleted.

Machine evidence: `reports/fuzz/olmblur_smart_C05.json`. It retains complete changed campaign results, original-route hashes, all 39 corpus before/after records, paired contexts, boundary traces, build provenance and sanitizer positive controls. The original fuzz geometry is distinct from the saved shrunk corpus geometry.

| Identity | SHA256 |
|---|---|
| Original MAIN `plugins_2025/OLMBlur.aex` | `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b` |
| Cached `radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker` | `9ac2c86cb707e23de7c360c128d61b14d0b4c3b71b417baa3e7e116fe6af42b7` |
| Mac source before | `8512f063e79975dc2f20ab1349df71a05a0a397015f3150280fbbeb46b893241` |
| Mac source after | `9e89e2d077d606f1a8da8c866a4a473238e5262b3de39adeb5c7899a298e9dcb` |

The worker is an absolute prebuilt path from INDEX; its name reflects its historical RadialBlur additions. Original OLMBlur Smart outputs reproduce the 300-case F17 baseline and all 39 saved route results before this change. No worker arithmetic was changed for this ticket.

**First divergent stage (observed).** `trace_olmblur_smart_C05.py` reuses the original exported `EffectMain` SmartPreRender/SmartRender fixture and adds read-only hooks at the six typed worker entries. The Mac counterpart compiles the real SDK public host with a scratch-only context observer at `BlurRender`. The diagnostic build bypasses only the small-fixture gate. No numerical AEX instruction is detoured; the existing import/suite scaffold is retained. Every direct Unicorn trace's complete output binds to the independently cached public worker output before stage interpretation.

Seed-1 indices 29, 31, 33, 115, 141, 157 and 210 all first disagree in the worker context's Smoothness field. For index 29 (PF16 Legacy, 22x42), AEX receives `69.0` (`00008a42` little endian); Mac received `69.85856628417969` (`96b78b42`). Amount is identically `5.0`. Before: 1,639 bytes / 1,607 uint16 words differ, first byte 12, AEX word `445f`, Mac `415f`. After: contexts and full output are exact, hash `f4427091b42db636bfa8f0ee628d22c3cacef984a21cb4ef3d76e77cb9d01d51`. Mac's previous output hash was `c735cd71e3cc1dfc6153737e926704a6e6d139308a2faac933187cd99febd9a9`.

All seven paired contexts match after the change. Four full outputs also become exact; indices 31/115/141 still differ after the corrected context, with AEX word `0000` versus Mac `0080`. The latter are residuals, not claimed closed.

**Static cause.** MAIN `disasm/OLMBlur.aex.asm.txt` addresses `180009c4e..180009c5d` execute `MOVSX EAX,word ptr [RSP+0x50a]`, `MOVD`, `CVTDQ2PS`, then store at worker context `+0x24`. The local parameter record starts at `RSP+0x4d0`: offset `+0x3a` is the signed high word of PF_Fixed at `+0x38`. `decomp/OLMBlur.aex.c.txt`, `FUN_180009b40`, agrees. The Mac exact-fixture path already implemented this conversion only for three fractional-Smoothness fixtures. It now occurs in the common public getter. The complete raw fixed value still controls admission; the duplicate fixture-only conversion is removed.

The independent boundary matrix uses all three depths x both Legacy values x Smoothness {1, 1+1/65536, 62.5, 100-1/65536, 100}: **30/30 paired contexts and full raw outputs exact**. These singleton controls isolate getter semantics and do not claim general small-frame admission.

**Measured campaigns**, all `--n 300 --jobs 2`, no shrinking, scratch corpus:

| Seed / build | Smart exact | mismatch | refusal | sanitizer abort |
|---|---:|---:|---:|---:|
| 1 before | 89 | 26 | 185 | 0 |
| 1 after O2 and ASan/UBSan | 102 | 13 | 185 | 0 |
| 3 before | 95 | 28 | 177 | 0 |
| 3 after O2 and ASan/UBSan | 107 | 16 | 177 | 0 |
| 1 small gate off before, ASan/UBSan | 224 | 74 | 0 | 2 |
| 1 small gate off after, ASan/UBSan | 257 | 41 | 0 | 2 |
| 3 small gate off before, ASan/UBSan | 231 | 69 | 0 | 0 |
| 3 small gate off after, ASan/UBSan | 271 | 29 | 0 | 0 |

Classic remains 13 exact / 287 refusal (seed 1), 22 exact / 278 refusal (seed 3). AEX Smart succeeds for all 600 inputs. Original route results/hashes are identical before/after. All 184 base-exact Smart cases are byte-identical. Every changed campaign result either becomes exact or decreases both differing byte and word counts. The remaining changed mismatches are explicitly recorded: seed 1 index 115, 1,985 -> 117 words; index 272, 17,724 -> 38; seed 3 index 146, 315 -> 105; index 161, 2,475 -> 2,472. They were not added to the exact corpus.

ASan/UBSan production result dictionaries equal ordinary O2 results for all 1,200 route executions, with no sanitizer findings. The gate-off PF8 Legacy findings at seed-1 indices 77/112 remain excluded in production. No new admission was made. Leak checking is disabled, not claimed.

**Corpus rebaseline and cluster closure.** All saved inputs, operations and reductions are unchanged. Each changed JSON retains its previous complete result in `C05_smart_update`. Four parameter-signature/depth clusters from T09 close under the same getter correction:

| Nondefault slots / depth | Cases | Smart before -> after |
|---|---:|---|
| [2,5] / 16 | 6 | mismatch -> exact |
| [2,5] / 32 | 5 | mismatch -> exact |
| [2,5] / 8 | 3 | mismatch -> exact |
| [1,2,5] / 8 | 1 | mismatch -> exact |
| Remaining Smart mismatches | 11 | unchanged |
| Smart refusals | 13 | unchanged |
| Classic exact / refusal | 13 / 26 | unchanged |

One atomic commit contains this shared cause and its four closed clusters: dividing the fix by signature would require forbidden case-specific behavior. Final sanitized corpus replay is **39/39 matches_saved**, 78 route executions, no sanitizer errors. The original 24x24 six depth/Legacy fixtures with optional checkin present/absent are **12/12 sanitizer-clean**, including active bytes, padding, guards and callbacks. `PYTHONPATH=tests python3 -m unittest test_olmblur_generic_classic_beta_20260822 test_olmblur_generic_beta_lane_20260820` gives **7 tests OK**. `git diff --check` passes.

inference:

- The observed worker-context boundary and original signed-word load explain the four corpus clusters as a public getter port defect. A shared parameter conversion fixes the cause without touching kernel arithmetic or final samples.
- Residual PF16 `0000` vs `0080` is consistent with the current Legacy writer's saturation of positive infinity versus original integer conversion semantics, but pre-store infinity was NOT captured here; this remains a follow-up hypothesis. The earlier commentary's infinity description was too strong.
- Gate-off exact gains are diagnostic only: unresolved mismatches and PF8 sanitizer findings prevent broad promotion. The stop condition is four saved clusters closed, not universal compatibility.
- These are original CPU-AEX emulation and real-SDK fake-host observations with retained math imports, not new native Windows UCRT/AE, installed Mac AE, GPU or ROI/downsample proof.

changed_files:
- `mac/OLMBlur/OLMBlur.cpp` — common Smart Smoothness materialization; remove duplicate fixture-only conversion.
- `tools/emulation/trace_olmblur_smart_C05.py` — paired original-export/Mac context traces, output hash binding and boundary matrix.
- `tools/fuzz/blur_admission_campaign_C05.py` — reproducible baseline/gate-off/sanitizer campaigns on the current gate shape.
- `tools/fuzz/verify_blur_smart_C05.py` — monotonicity assertions, retained controls and narrowly validated corpus rebaseline.
- `tests/fuzz_corpus/olmblur/seed1_case000{025,029,055,092,104,115,120,157,176,206,210,214,244,247,272}_*.json` — 15 mismatch -> exact expectations, previous results retained.
- `reports/fuzz/olmblur_smart_C05.json` — machine evidence.
- `orchestra/reports/C05-olmblur-smart.md` — this report.

verify:

Run from this worktree. All generated artifacts stay in ticket scratch. Commands below regenerate before and after evidence even after rebaseline; the verifier checks the retained historical corpus result. Original baseline campaigns used `run.py`; the revision wrapper reproduces the same source and leaves the checkout untouched. No core file changed, so its current files also reproduce the base.

```sh
s="$PWD/orchestra/state/C05-olmblur-smart"
main='/Users/onmk/Documents/Projects/Personal/OLM as'
w='/Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker'
base=ad206f003a9908e1c7a77bdda1de665d543dd996
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
campaign() {
  label="$1"; seed="$2"; shift 2
  python3 tools/fuzz/blur_admission_campaign_C05.py "$@" --plugin olmblur \
    --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 \
    --worker "$w" --scratch "$s" --report "$s/$label.json" \
    --corpus "$s/$label-corpus" > "$s/$label.log" 2>&1
}
for seed in 1 3; do
  campaign "before-seed$seed" "$seed" --blur-source-revision "$base"
  campaign "gateoff-seed$seed" "$seed" --blur-source-revision "$base" --blur-small-off --blur-sanitize
  campaign "smooth-seed$seed" "$seed"
  campaign "smooth-seed$seed-sanitized" "$seed" --blur-sanitize
  campaign "smooth-gateoff-seed$seed" "$seed" --blur-small-off --blur-sanitize
done
for mode in before smooth final; do
  extra=()
  if [ "$mode" = before ]; then extra=(--blur-source-revision "$base"); fi
  if [ "$mode" = final ]; then extra=(--blur-sanitize); fi
  python3 tools/fuzz/blur_admission_campaign_C05.py "${extra[@]}" --plugin olmblur \
    --jobs 2 --replay tests/fuzz_corpus/olmblur --worker "$w" --scratch "$s" \
    --report "$s/$mode-replay.json" > "$s/$mode-replay.log" 2>&1
done
"$main/tools/emulation/.venv/bin/python" tools/emulation/trace_olmblur_smart_C05.py \
  --source-revision "$base" --scratch "$s" --report "$s/context-before.json" > "$s/context-before.log" 2>&1
"$main/tools/emulation/.venv/bin/python" tools/emulation/trace_olmblur_smart_C05.py \
  --scratch "$s" --report "$s/context-smooth.json" > "$s/context-smooth.log" 2>&1
"$main/tools/emulation/.venv/bin/python" tools/emulation/trace_olmblur_smart_C05.py \
  --boundaries --scratch "$s" --report "$s/context-boundaries.json" > "$s/context-boundaries.log" 2>&1
python3 tools/fuzz/verify_blur_smart_C05.py --scratch "$s" --report "$s/verify.json" > "$s/verify.log" 2>&1
PYTHONPATH=tests python3 -m unittest test_olmblur_generic_classic_beta_20260822 test_olmblur_generic_beta_lane_20260820 > "$s/tests.log" 2>&1
git diff --check
```

Expected: campaign table above; verifier PASS with four closed clusters and 12 retained controls; final replay 39/39; 7 unit tests OK. The verifier deliberately does not update corpus without `--rebaseline`. Initial migration used that flag once after all transition checks and retained controls passed.

next:
- Trace PF16 Legacy pre-store nonfinite values and original CVTTSS2SI/low-word store, especially unshrunk seed-1 index 115 and gate-off indices 31/141. Preserve base-exact output and establish the first remaining divergent stage before changing the writer.
- Investigate repeated non-Legacy coefficients/rounding and PF32 nonfinite payload residuals with paired stages. Seed-1 remaining public Smart mismatches are 13; the saved corpus retains 11 shrunk mismatches.
- Revisit `generic-small-fixture` admission only after seed 1 + fresh-seed and independent matrix evidence proves a general clean rule. Current refusal counts remain 185/177, and the two PF8 Legacy gate-off sanitizer errors remain unresolved.
