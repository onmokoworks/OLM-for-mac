status: blocked
summary:
- Reproduced the retained Full 3840x2160 PF8 discrepancy in exactly two B samples.
- F54 original AEX, installed bundle on arm64/x86_64, serial/default dispatch, and R10 reference all agree exactly.
- The retained AE render differs; its no-effect control exactly matches the generated A02e source.
- Architecture and parallel-dispatch hypotheses are refuted without a differing AE input/host-boundary value; stop rule applied.
- No production changes, AE launch, sanitizer campaign, or regression campaign; AE-specific cause remains unresolved.

facts:
- Read AGENT_GUIDE.md, GOTCHAS.md, compatibility plan, A02g report, and Smoother v1's forbidden-action row. Branch: `orch/S01-smoother-4k-two-sample-diff`.
- Executed (exit 0):
  ```sh
  PYTHONDONTWRITEBYTECODE=1 ../A02f-real-ae-retest-downsample/orchestra/state/A02f-real-ae-retest-downsample/venv/bin/python orchestra/reports/S01-smoother-4k-evidence/reproduce.py > orchestra/state/S01-smoother-4k-two-sample-diff/reproduce.log 2>&1
  ```
  The first run loaded retained TIFFs. The committed version loads the identical hash-bound compressed ARGB bytes, removing dependency on those worktrees and TIFF decoding. It retains the same host/oracle calls. Each call runs sequentially, with a timeout; reference compilation uses `OLM_REFERENCE_BUILD=1` through the R10 adapter mechanism.
- Input: 33,177,600 ARGB8 bytes, SHA-256 `97c1b2330a146ec5c56e73779a169d50d1b8016fee28d47ba96315987caad03e`. Decoded A02f control equals A02e priority-e2 `input-3840x2160-8.argb` byte-for-byte. This is a retained control, not a fresh AE render or plugin checkout trace.
- AE: SHA-256 `c9742d1378262bab8d398f543687d1702a973a78381bd10a2bb870c960edd109`.
- All six outputs have SHA-256 `14c5a995110525b5c04c2c8a86c20ea8904a580bb92256bbb7fb0608fe7e7531`: installed bundle arm64 default, arm64 `OLM_PARALLEL_MAX=1`, x86_64 default, x86_64 `OLM_PARALLEL_MAX=1`, current-source R10 reference, original AEX through F54. Each differs from AE in exactly two samples: (1649,1235), B, AE=222/0xde versus host=223/0xdf; (1649,1238), B, same values. No other sample differs.
- Installed bundle hash remains the A02f recorded `47d02cbb8325bd7885e95e89201615436de05eacb3c34a62fdfcc2dfc2e17b41`. Universal F51/F47d host is invoked explicitly with `arch -arm64` and `arch -x86_64`; commands are retained in results.json. Classic route, tight rows, no input padding, defaults key=false, color=255/255/255/255, tolerance=6.
- F54 worker SHA-256 `dbf9766f23de8f247169f63cf8310a0c73e15f053765e2c9373106623c2e9af2`; original AEX SHA-256 `6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82`. Adapter reports `status=ok`, guards intact and clean session. No arena rejection or timeout. Framed session response is retained as oracle-stdout.bin; stderr is empty.
- Final verification: committed script parses successfully with `ast.parse`; `git diff --check` and `git diff --cached --check` pass. Removed generated reference build and frame outputs; scratch is 44 KB. The reproduction process exited 0; no owned background process remains.
- Evidence manifest binds TIFF provenance, raw bytes, host, source, worker and AEX hashes. Compressed raw inputs/AE output are committed (about 1.9 MB total). No reference worker rebuild, installed-bundle write, MAIN modification, release gate or ledger edit.
- Architecture hypothesis: both slices return identical output. Parallel-dispatch hypothesis: both caps return identical output. These do not establish any differing live AE world/parameter. No nondeterminism was observed in these runs; repeated-run, memory-sanitizer and race-sanitizer investigations were not performed.

inference:
- The host matches the original CPU AEX for this exact input and defaults. Changing numerical output to match the retained AE file would break that measured original-AEX match.
- A host-context or AE I/O cause is plausible but unproven. The retained no-effect control excludes a difference in that exported control; it does not prove the effect checkout world is identical.
- The two rejected explanations provide no live AE boundary divergence. The strict two-hypothesis stop rule prevents proceeding to speculative rowbytes/origin/extent/Smart/MFR experiments in this ticket. F54 success establishes the oracle side, not the missing AE boundary.
- PF8 does not use P05c's reduced PF16 stack storage, per the P05c source/report; no causal evidence warrants altering those clears.

changed_files:
- orchestra/reports/S01-smoother-4k-two-sample-diff.md
- orchestra/reports/S01-smoother-4k-evidence/reproduce.py
- orchestra/reports/S01-smoother-4k-evidence/manifest.json
- orchestra/reports/S01-smoother-4k-evidence/results.json
- orchestra/reports/S01-smoother-4k-evidence/input.argb.gz
- orchestra/reports/S01-smoother-4k-evidence/ae.argb.gz
- orchestra/reports/S01-smoother-4k-evidence/oracle-stdout.bin
- orchestra/reports/S01-smoother-4k-evidence/oracle-stderr.log

verify:
```sh
# Run from this worktree; sequential, no AE launch. Requires recorded installed bundle.
PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' orchestra/reports/S01-smoother-4k-evidence/reproduce.py > orchestra/state/S01-smoother-4k-two-sample-diff/recheck.log 2>&1
cat orchestra/state/S01-smoother-4k-two-sample-diff/results.json
git diff --check
```
Expected: exit 0; six rows with the identical host hash and exactly the two mismatches above; F54 guards intact/session clean. Bundle identity assertion must pass. Output scratch is approximately 163 MB before cleanup. Script checks compressed-input hashes. The installed bundle may later change; restore/use the recorded identity before treating a new run as reproduction. No fuzz or corpus result is claimed for this investigation because production source was unchanged and the stop rule was reached.

next:
- Follow-up: capture the actual AE input/output world and InData boundary (rowbytes, origin, extent, selector, floating-point state, thread/MFR context), and compare against these committed bytes. Do not install a trace bundle in AE folders.
- A fresh existing-project control/effect aerender, only when no AE/aerender is running, can establish whether the retained difference persists. No AE GUI is needed or authorized here.
- If that boundary shows nondeterminism, perform the requested sanitizers and causal fix, then R10 ref_vs_fast, default fuzz with --jobs 1, and all Smoother corpora. If it shows a deterministic context difference, isolate that first. This report does not close bit-exact native AE conformance.
