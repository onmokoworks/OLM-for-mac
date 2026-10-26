status: blocked
summary:
- ColorKey only; the ticket's olmsmall sentence was treated as a copy/paste error.
- Moved historical admission/fixture helpers to tests; harnesses include them explicitly.
- Removed subsumed admission fallback and unreachable source-specific alpha adjustment.
- Reused core world layout/overlap checks; retained per-depth arithmetic differences.
- Mandatory blocked status: automatic review rejected one scratch cleanup command; safe cleanup succeeded.

facts:
- Automatic approval review rejected `rm -rf` for this ticket's two generated Xcode trees: “rm -f style commands are not permitted. Use a safer approach”. A subsequent Python cleanup checked the exact scratch parent and refused symlinks, then successfully removed only those trees. Per worker brief, this report remains `blocked` even after recovery.
- Baseline: `ac9415d364d17d35b8a5f5834d6985325cdd6d6e`.
- Final G1 (`--cases 3000 --arch both --build both --jobs 1`) exited 0: 12,012 exact comparisons, zero differences/refusals/new refusals/execution errors. No first mismatch. The full run was performed once.
- Extraction commit: `d6357707`; intermediate G1 (500 random + 3 UHD cases, arm64, both builds) exited 0: 1,006 exact, zero differences/refusals/new refusals/execution errors.
- Native-only G2 replay of every saved ColorKey corpus with recorded flags: 102 observations per side, byte-identical JSONL; SHA256 `d388f3bcf3d980d830d22b8e22a486972acfe9221398d4af06ceea139f05be41`. No first mismatch.
- Universal Debug Xcode builds: base/head both succeeded. Warning occurrences 340 -> 338 (compiler warnings 338 -> 336; two unchanged build-system warnings each). Removed the two architecture instances of unused `ClassicWorldsMatch`. Remaining SDK/shared warnings were not suppressed.
- UI oracle: ColorKey 36 updates, 72 checks including reload, zero mismatches; overall command exited 0. Parameter UI parity: three checks passed.
- Parameter-order source test initially failed on both base and head (`ParamsSetup body not found`), because its next-function sentinel moved during the earlier split. Reader now ends at the function's closing brace; all four original tests pass, assertions unchanged.
- Moved Lab76 native harness compiled/executed successfully: 56 output bytes, SHA256 `6089bc28e43e4f42dc6a4c9f5a6f63ad502c3f6d95f8503fedf76f205c4e8257`. An initial diagnostic tried decoding these binary bytes as UTF-8 and failed after successful execution; the corrected check passed.
- Shared world-safety test passed (one compiled C++ contract). Real-SDK public-entry harness passed on both base/head (63 Classic + 63 Smart cells, 13 callback negatives), including the moved fixture include.
- Historical source-bound atomic harness compiled on both sides but failed identically: exit 3, 2,304 output bytes, SHA256 `2b05dfeed6c1385d4818cd727aabc6931581b6d39ce22f84a13461b91a33e740`, stderr `SOURCE_BOUND_ATOMIC pass=0 positives=0 negatives=0`. It stops at the first mutated-source rejection expectation. This pre-existing failure means G4 is not fully green; assertions were preserved.
- Production non-comment/nonblank `.cpp/.h/.inc` lines: 2,884 -> 2,553. No source file exceeds 1,000 lines. Counts strip block/line comments then count nonempty lines. Relocated test fixture: 308 lines (formerly compiled inside production); product plus relocated fixture totals 2,861, below the original 2,884.

| File | Before | After |
| --- | ---: | ---: |
| mac/OLMColorKey/AdmissionFixtures.inc | 324 | 0 |
| mac/OLMColorKey/BlurMath.inc | 230 | 230 |
| mac/OLMColorKey/ColorMath.inc | 126 | 126 |
| mac/OLMColorKey/Diagnostics.inc | 149 | 149 |
| mac/OLMColorKey/Distance.inc | 186 | 186 |
| mac/OLMColorKey/Kernel.inc | 581 | 572 |
| mac/OLMColorKey/OLMColorKey.cpp | 287 | 287 |
| mac/OLMColorKey/OLMColorKey.h | 146 | 146 |
| mac/OLMColorKey/OLMColorKey_Strings.cpp | 41 | 41 |
| mac/OLMColorKey/OLMColorKey_Strings.h | 34 | 34 |
| mac/OLMColorKey/Parameters.inc | 225 | 264 |
| mac/OLMColorKey/Pixels.inc | 159 | 159 |
| mac/OLMColorKey/Render.inc | 396 | 359 |

inference:
- The old bounded admission fallback is subsumed: every `IsBoundedEdgeInfo` blur tuple already returns true from `IsGenericEdgeBlurTuple`, independent of captured pixels/stride. Removing this tail does not broaden admission.
- The removed `nextafter` branch requires the public-owner Inside/type-3/amount-4 tuple. That tuple satisfies `IsRecoveredPublicBlur`, whose earlier writer continues before this branch. Its source-fixture scan therefore had no output effect.
- `validate_layout` checks the same active final-row span and `require_disjoint` checks the same address bounds/overlap; positive signed geometry is checked before size_t conversion. Redundant width/stride checks were removed from admission, with refusal tags retained.
- Render/read/write already use PixelT templates. PF8 rounding, PF16 truncation, PF32 SSE multiplication and normalization differences remain explicit; merging them would change arithmetic types/operations, so no extra template layer was introduced.
- This is native before/after equivalence evidence, not a new AEX/native-AE conformance claim. No release gate, installation, push, MAIN write, emulator rebuild, or other-plugin code change was performed.

changed_files:
- mac/OLMColorKey/OLMColorKey.cpp
- mac/OLMColorKey/Parameters.inc
- mac/OLMColorKey/Kernel.inc
- mac/OLMColorKey/Render.inc
- mac/OLMColorKey/AdmissionFixtures.inc -> tests/olmcolorkey_admission_fixtures.inc
- tests/test_olmcolorkey_parameter_order_static_20260728.py
- tools/emulation/probe_olmcolorkey_public_entries_real_sdk_20260813.cpp
- tools/emulation/probe_olmcolorkey_source_bound_atomic_20260813.cpp
- tools/emulation/test_olmcolorkey_lab76_multikey_order_closure_20260812.py
- orchestra/reports/C02-cleanup-olmcolorkey.md

verify:
From the worktree, choose a fresh scratch directory:

```sh
S="$PWD/orchestra/state/C02-cleanup-olmcolorkey/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
python3 tools/refactor/native_diff.py --plugin olmcolorkey --base ac9415d364d17d35b8a5f5834d6985325cdd6d6e --cases 3000 --arch both --build both --jobs 1 --scratch "$S/g1" > "$S/g1.log" 2>&1
scripts/setup_ae_sdk_links.sh > "$S/sdk.log" 2>&1
python3 -B tests/ui_oracle/compare_mac.py --scratch "$S/ui" > "$S/ui.log" 2>&1
python3 -B tests/test_olmcolorkey_parameter_ui_parity_20260806.py
python3 -B tests/test_olmcolorkey_parameter_order_static_20260728.py
python3 -B tests/test_olm_world_safety.py > "$S/world-safety.log" 2>&1
python3 -B tests/test_olmcolorkey_public_entries_real_sdk_20260813.py > "$S/public-entries.log" 2>&1
# Known baseline failure; expect probe exit 3, not a new cleanup regression.
python3 -B tests/test_olmcolorkey_source_bound_atomic_20260813.py > "$S/source-bound.log" 2>&1
xcodebuild -project mac/OLMColorKey/Mac/OLMColorKey.xcodeproj -configuration Debug -jobs 1 ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO MACOSX_DEPLOYMENT_TARGET=11.0 OBJROOT="$S/xcode/objects" SHARED_PRECOMPS_DIR="$S/xcode/pch" CONFIGURATION_BUILD_DIR="$S/xcode/products" build > "$S/xcode.log" 2>&1
python3 - <<'PY_CLEAN'
from pathlib import Path
import os, shutil
root = Path(os.environ['TMPDIR']).resolve()
p = root / 'xcode'
assert p.parent == root and not p.is_symlink()
shutil.rmtree(p)
PY_CLEAN
```

For G2, reuse the native-only replay code committed in `orchestra/reports/C01-cleanup-shared-math-and-tests.md`:

```sh
python3 - <<'PY_REPLAY'
from pathlib import Path
import os
s = Path('orchestra/reports/C01-cleanup-shared-math-and-tests.md').read_text()
marker = "cat > \"$S/replay_native.py\" <<'PY_NATIVE'\n"
a = s.index(marker) + len(marker)
Path(os.environ['TMPDIR'], 'replay_native.py').write_text(s[a:s.index('\nPY_NATIVE', a)])
PY_REPLAY
mkdir -p "$S/base"
git archive ac9415d mac core cli tools ucrtmath reports/radialblur_public_getters_aligned_20261001.json | tar -xf - -C "$S/base"
for name in Headers Util Resources; do ln -s "$PWD/$name" "$S/base/$name"; done
for side in base head; do
  TREE="$PWD"
  if [ "$side" = base ]; then TREE="$S/base"; fi
  python3 -B "$S/replay_native.py" "$TREE" "$PWD/tests/fuzz_corpus" "$S/g2-$side.jsonl" olmcolorkey > "$S/g2-$side.log" 2>&1
done
cmp "$S/g2-base.jsonl" "$S/g2-head.jsonl"
python3 - <<'PY_CLEAN'
from pathlib import Path
import os, shutil
root = Path(os.environ['TMPDIR']).resolve()
p = root / 'base'
assert p.parent == root and not p.is_symlink()
shutil.rmtree(p)
PY_CLEAN
```

Expected G1: 12,012 exact comparisons; zero differences, new refusals and execution errors. Expected G2: cmp exit 0, 102 observations/side and the SHA256 above. Expected Xcode: successful Universal build, 338 total warning occurrences. Expected UI/parameter tests: zero mismatches, three parity checks and four parameter-order tests passed.

next:
- Follow-up: replace the historical source-bound negative expectations with a separately reviewed contract for generalized admission. Do not weaken this ticket's assertions to claim G4 green.
- Cleanup implementation is ready for review; mandatory blocked status also records the recovered automatic cleanup rejection.
- Orchestrator runs the combined release gate after all C02 tickets; it was deliberately not run here.

Additional exact native Lab76 fixture check (uses MAIN's existing venv; does not run the AEX):

```sh
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" -B - <<'PY_LAB'
import sys, hashlib
sys.path.insert(0, 'tools/emulation')
import test_olmcolorkey_lab76_multikey_order_closure_20260812 as m
raw = m.production_effectmain()
print(len(raw), hashlib.sha256(raw).hexdigest())
PY_LAB
```

Expected: 56 bytes and the Lab76 SHA256 above. All started processes completed. Regenerable Xcode trees and baseline archive removed; scratch kept logs and small comparison records only, below 5 GiB.
