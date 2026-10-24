status: blocked
summary:
- Corrected R05's tracer-capability conclusion: registered C53b captures raw typed Radial intermediate planes.
- Seventeen retained first witnesses: 68 fresh original sessions; 91 intermediate-plane and 17 final comparisons exact against current Mac builds.
- Full-size fixture165 needs 31,795,200-byte RGBA planes; whole-plane and displaced-window configurations both rejected by C53b.
- Stopped under the two-refuted-hypotheses rule. No numerical pins, production code, assertions or release predicates changed.
- Groups 2 and 3 remain unperformed; the requested release-gate closure is NOT achieved.

facts:

Base: `81c6d45d`, branch `orch/R06-release-gate-closure`. Only R06 report/evidence/driver files change. MAIN, external emulator source, cache workers, installed bundles, release gate inputs and forbidden-action lists are unchanged. No worker was rebuilt. SDK links were created in this worktree by the existing setup script. Scratch stayed below 300 MiB; temporary build directories were automatically removed. All task subprocesses exited.

Before/after gate table (R05 is retained historical evidence, **not a new R06 gate run**):

| Check | Before, R05 | After, R06 |
|---|---|---|
| Generic gate | 45 PASS / 8 FAIL / 0 SKIP | Not rerun; inputs unchanged, no failures closed |
| Release aggregate | invalid; `releasable=false` | Not rerun; no release claim |
| Radial selected intermediate witnesses | unavailable with attempted F46 raw tracer | 17 first witnesses, 91 planes exact; full-size165 unresolved |
| Radial complete legacy fixture commands | 18 unresolved | Still unresolved: remaining cases, planes and negatives not replaced |
| R03 runtime/contract failures | 13 unresolved | Not adjudicated |
| Remaining F40/packages/support/performance bindings | unresolved | Not adjudicated |
| Installed identity / host-smoke / Kira Windows-owner renewal | requires real AE/Windows | requires real AE/Windows |

Commands and measured results:

- Read `AGENT_GUIDE.md`, `tools/emulation/GOTCHAS.md`, the compatibility plan, Radial ledger excerpts, R05 report/results, C53b recipe/patch/documentation and existing capture harnesses.
- `bash scripts/setup_ae_sdk_links.sh`: exit0. An initial Zoom build lacked SDK links; it was rerun successfully after setup. Initial source lookup also found that PF16 records172/174/181 have no F39 packaged source. The driver now regenerates their original typed source using the retained generator, requiring its F39 input hash before running. These are harness setup corrections, not numerical differences.
- `R06-radial-trace.py --index N`, for **152,153,155,156,157,158,159,167,168,169,170,171,172,174,178,179,181**: final invocations exit0. Each executes original AEX twice with untraced F46 and twice with C53b, using native ARGB16 or ARGB32F raw input. All 68 sessions have intact output guards and clean sessions. All four final outputs agree for each record.
- Original AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- F46 worker SHA-256: `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
- C53b worker SHA-256: `df51edc461ee13ae826c94e62b29c17b813181ef1c2719388e4d9faf180099a2`.
- `R06-compare-rotation.py N`, same 17 indices: final invocations exit0. Fresh current UCRT-linked production captures match both original trace repeats, byte for byte. The comparator checks trace identity, no truncation, no dropped/unhookable watches, complete snapshot lengths and snapshot hashes before comparing the bytes. Output padding is unchanged in all 17 captures.
- **91 intermediate-plane comparisons + 17 final-output comparisons; 12,531,456 compared bytes; zero differing bytes; first mismatch null.** Final output accounts for 23,328 bytes per repeat. Current production source SHA-256 is `8ea892bcae5882b8d212c1d1494b68dbf8fe39dce212f133ad2491c200ea200e`.
- Rotation boundaries: polar/source-scalar before `0x2780`, prepass-alpha after `0x2780` where the existing production seam exposes it, accumulator/max-alpha after `0x24c0`, final float plane after `0x4640`. Zoom boundaries: pre-blur polar at `0xb150` entry and normalized polar at first `0x9d80` entry. Complete typed output is separately bound to F46. This does **not** verify all legacy coordinate, eligibility, negative, multi-case or full-size assertions.
- Example record152: fresh accumulator hash `b778e242f9a1bb63e85cf54dccf3fdd6fb5f56aebc2bac91bf291dbebe3d9342`, maximum-alpha hash `1dcb15ab797a3fa7d1a4a7b791bbdb55b0f2e564effe3123a8d6d0fd870ec889`, final float-plane hash `87cc31562a24086e546de772d83e6cffb94631e827cdf54ef0237fcc9b6167a8`. Both original repeats and current production agree. The old accumulator pin was `13b28b32ce8db24cde6bd5f93acab3113a192137b77be5f99da09555859d7135`.
- `R06-full-plane-capability.py`: exit0 means both expected configuration rejections were recorded, **not** successful rendering. A `size=31795200` watch is rejected with `watch bytes must be 1..16777216`. A two-window strategy's tail watch (`size=15017984`, `byte_offset=16777216`) is rejected with `unknown field byte_offset`. Both produce zero output bytes and no trace. These admission probes use the retained 9x7 typed input; they are not full-size165 executions.
- The existing C53b schema has pointer-slot dereferencing but no post-dereference byte displacement. Its recorded patch already establishes the size limit and closed schema. The two attempted full-coverage configurations were refuted without a new arithmetic boundary value; investigation stopped per hard rule8. No third workaround was attempted.
- No genuine Mac-versus-original numerical difference was observed in measured cells, so no fuzz witness was emitted. The comparator includes fuzz-format witness emission if a future replay finds a difference.

inference:

The measured small-frame stage differences in R05 are consistent with legacy reference arithmetic drift: C53b's fresh intermediate bytes agree with current Mac, and its final bytes agree with untraced F46. This supports refreshing those measured cells once their complete command contracts are migrated. It does not justify replacing entire multi-case commands or removing their negatives now.

Full-size165 is an instrumentation boundary of the two tested capture strategies, **not** a demonstrated Mac numerical mismatch or proof that every possible existing-watch strategy is impossible. A different naturally occurring interior pointer may permit bounded windows, but that needs a separately bounded investigation. Increasing the registered worker's snapshot capacity would require a newly authorized build; this ticket did not authorize rebuilding workers. Neither issue is a real-AE/Windows requirement, and neither is relabeled as one.

changed_files:

- `orchestra/reports/R06-radial-trace.py`: reproducible twice-F46/twice-C53b raw typed capture.
- `orchestra/reports/R06-compare-rotation.py`: current production stage/output comparison, complete-byte verification and mismatch witness emission (also handles the two Zoom witnesses).
- `orchestra/reports/R06-full-plane-capability.py`: the two rejected full-coverage configurations.
- `orchestra/reports/R06-package-evidence.py`: evidence validation and packaging.
- `orchestra/reports/R06-results.json`: per-case hashes/counts/results, capability failures and remaining work.
- `orchestra/reports/R06-evidence.tar.xz`, `orchestra/reports/R06-artifact-manifest.json`: original traces, compressed original/Mac planes, outputs, watch configurations and logs.
- This report.

verify:

From the worktree root, use the existing MAIN venv and cached workers. No build/install of a reference worker is needed:

```sh
bash scripts/setup_ae_sdk_links.sh
export OLM_TEST_JOBS=2 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/orchestra/state/R06-release-gate-closure"
export TMP="$TMPDIR" TEMP="$TMPDIR"
mkdir -p "$TMPDIR"
PY="/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3"
for index in 152 153 155 156 157 158 159 167 168 169 170 171 172 174 178 179 181; do
  "$PY" -B orchestra/reports/R06-radial-trace.py --index "$index" > "$TMPDIR/trace$index.log" 2>&1 || break
  "$PY" -B orchestra/reports/R06-compare-rotation.py "$index" > "$TMPDIR/compare$index.log" 2>&1 || break
done
"$PY" -B orchestra/reports/R06-full-plane-capability.py > "$TMPDIR/capability.log" 2>&1
python3 -B orchestra/reports/R06-package-evidence.py > "$TMPDIR/package.log" 2>&1
git diff --check
```

Expected: 17 records, 68 clean original sessions, 108 exact comparisons including 91 intermediate planes, all padding checks true, zero differences; capability records two rejections. No gate status is promoted. Packaging validates all records before writing results. Timing/process IDs in traces mean a fresh archive hash can differ.

Retained evidence can be checked without executing plugins:

```sh
python3 - <<'PY'
import hashlib,json,tarfile
from pathlib import Path
p=Path('orchestra/reports');m=json.loads((p/'R06-artifact-manifest.json').read_text())
with (p/m['archive']).open('rb') as f:
    assert hashlib.file_digest(f,'sha256').hexdigest()==m['sha256']
with tarfile.open(p/m['archive']) as t:
    assert len(t.getmembers())==len(m['files'])
    for r in m['files']:
        with t.extractfile(r['path']) as f:
            assert hashlib.file_digest(f,'sha256').hexdigest()==r['sha256']
r=json.loads((p/'R06-results.json').read_text())
assert r['status']=='blocked' and len(r['radial'])==17
assert sum(len(x['planes']) for x in r['radial'])==108
assert all(x['padding_exact'] and all(v['exact'] and v['different_bytes']==0 for v in x['planes'].values()) for x in r['radial'])
print('R06 evidence intact; release closure remains blocked')
PY
```

Retained archive: 378 members, 11,220,888 bytes, SHA-256 `bc38a820c4ee82b41be3c21ad66a0f06a476897b619d3414908e778e5a93d669`. The offline integrity check passed for every member. All four driver files passed Python AST parsing.

next:

1. Authorize a bounded full-size165 tracing follow-up: either demonstrate a naturally exposed interior pointer covering the remaining bytes or authorize a larger read-only snapshot worker, retain/register it durably, and bind its final output to F46 twice. Complete all remaining cases/planes/negative assertions before refreshing the 18 legacy commands. Preserve the R06 traces as evidence, not as a substitute for complete command coverage.
2. Continue the 13 R03 runtime/contract failures, then F40 stale bindings/missing historical packages, support documentation and performance-runner bindings. None was adjudicated after the group1 stop.
3. Renew installed identity, native host smoke and Windows-owner evidence through real AE/Windows. Then rerun both gates; the requested all-PASS-except-real-host outcome is still outstanding.
