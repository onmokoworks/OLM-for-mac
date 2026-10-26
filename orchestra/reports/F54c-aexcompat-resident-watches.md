status: blocked
summary:
- Ported C53b-compatible resident watches into stacked AEXCompat branch olm/F54c-resident-watches; reviewed source commit 3ab60261c59da842c3eea1b5762d9db3871d9018.
- Added pointer chains, bounded full-plane snapshots, first/all occurrence selection, JSON and raw dumps; preserved F54b tracing.
- All 17 retained R06 cases and 342 snapshots are byte-exact; cropped zoom/rotation captures and three 4K no-op renders pass.
- Registered worker-F54c; final 5,687-route inventory has zero byte differences but two RadialBlur wall-limit status differences, blocking F53 equivalence.
- No OLM plugin, MAIN, release gate, ledger, default oracle, claim, push or PR changes.

facts:
- AEXCompat base: e96d6ed9b0a8170e1d3d427ac6cf65e07dc3144e (olm/F54b-numeric).
- Source/worktree: /Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-olm-F54c, branch olm/F54c-resident-watches.
- Independent read-only source review completed at 3ab60261; accepted findings were resolved. The initial large-watch design lacked an aggregate memory bound; the final implementation reserves pending and completed captures before reads, bounds logical watched bytes to 256 MiB and witness count to 256, and reports dropped witnesses. Changed-range summaries are capped at 4096 with an explicit flag; captured bytes remain complete.
- Final worker: ~/.cache/olm-emu/worker-F54c/aex-guest-worker.
- Worker SHA256: 3d5eec0c6792f176a9cfbc38093c53b852f4ea1baae2cfd313345c02f55d6fba.
- INDEX registration used .index.lock; worker directory contains source.tar and build.json. Identical installer rerun returned reused:true. The build tree was deleted after verification.
- Initial memory_pressure: 53% free; observed checks during work: 46–53% free, above the required 30%. One build/emulator process normally, at most two concurrent; corpus driver uses --jobs 1.
- cargo build --manifest-path guest/Cargo.toml --release -p aex-guest-worker --bin aex-guest-worker -j 1: final reviewed build succeeded in 50.26 seconds.
- RUST_TEST_THREADS=1 cargo test --manifest-path guest/Cargo.toml --release -p aex-guest-worker -p olm-ucrtmath -j 1: 714 worker library + 10 CLI + 8 math tests passed; 3 ignored; zero failures. Full 3840x2160x16-byte synthetic snapshot test passes (132,710,400 bytes). This is synthetic capture evidence, not a real-AEX 4K intermediate-plane claim.
- Initial test development: a tuple-return API edit initially failed compilation; two new tests then failed UC_ERR_WRITE_UNMAPPED because the test helper mapped only a small scratch page. A text replacement missed unformatted included source, repeating the same two failures once. Dedicated page-rounded mappings fixed both; no emulator arithmetic or plugin changes were made.
- verify_F54c.py: all 17 archived R06 cases, 342 before/after snapshots, 48,693,888 captured bytes, and every final output matched C53b byte-for-byte. First mismatch: none. Raw dumps equal JSON hex. Input SHA256 bindings were checked against F39 evidence. Raw stage files were deleted after hash retention.
- verify_F54c.py --geometry-only: 20x15 checkout at [3,4,23,19] on a 40x30 canvas; zoom direct pointer and rotation rcx->[+0x38] pointer each capture before/after. Both match untraced output with guards/session clean and the expected output rectangle. Zoom output SHA256 972137a96d7b81f74d90197c1e59b6c43dc5aa0f92fc35c479f47a28df356546; rotation 6ee347dd6c402137074e098d3448e868dfb2e645c42b5c4bbe56faaeebe628f6.
- verify_F54c_4k.py: real original-AEX no-op renders at 3840x2160 in 8/16/32bpc match untraced F54b exactly; each captures 128-byte InData before/after at direct call RVA 0x10974. This call is grounded by the original dispatch table: PF_CMD_SMART_RENDER=24 -> RVA 0x1096c, then direct call at 0x10974 to 0x17d60 with InData in RDX. F53 cannot serve as this 4K baseline: the measured rejection is its 1920x1080 session dimension cap.
- Inherited limitation probe: function watch at the actual selector entry RVA 0x10540 produced zero witnesses, no unhookable flag, and exact 4K no-op output. probe_F54c_entry.py reproduces this with the unchanged SMART_TRACE interface on both F54b and F54c. This is a missing capture, not successful trace coverage.
- Corpus inventory: 2,995 saved inputs / 5,687 route comparisons, all ten plugins and every current saved route checked. Final inventory: 5,579 exact successful outputs, 106 matching non-success classifications, zero output-byte differences, TWO status differences. Full-corpus equivalence is NOT established. Comparison semantics are unchanged from F54b: raw bytes, status classification and output rectangle; diagnostic text is retained but not required identical.
- Initial full-corpus attempt completed 5,384 routes before its strict driver stopped on one status difference, before Smoother. C46_seed1_case000280/smart: F53 ok, 3,968 bytes, 8.992045 seconds; F54c reject, no output, 20.016279 seconds, RIP=0x180002860. Initial per-case JSONL/summary is retained separately.
- One isolated same-case recheck returned reject on BOTH workers at the existing execution limit. This does not establish byte equivalence; no frame was produced. Its result is retained separately rather than substituted into the corpus.
- One full RadialBlur replay plus the remaining Smoother corpus completed the inventory. The replay reproduced C46_seed1_case000280/smart: F53 ok in 8.927 seconds, F54c reject in 20.014 seconds at RVA 0x2860. It additionally observed C49_seed1_case000117/smart: F53 ok, 480 bytes, 13.447 seconds; F54c reject in 20.015 seconds at RVA 0x2cc3. On the first attempt, this second case rejected on both workers. No first byte mismatch exists because the differing F54c runs produced no output.
- No further emulation retries were run after that full replay. run_F54c_corpus.py --resume was then used only to validate/reaggregate existing ten-plugin records: worker/baseline identities, full route inventory and recomputed category counts. It exits 1 for the two differences. Resume is for the frozen current corpus, not proof that arbitrary modified corpus contents match old records.
- The registered worker has qualification.json marking this corpus gate blocked; it remains experimental, and the default oracle is unchanged.

inference:
- The two persistent full-replay status differences block this ticket despite successful tracing tests. Baseline status itself varied between runs, so a timing-dependent boundary is supported; the cause of F54c reaching the limit is unproven. No numeric/arithmetic cause is claimed, and no execution budget was changed to force equality.
- R06 stage equivalence and traced/untraced comparisons support read-only capture behavior for the measured paths. They do not establish universal AE equivalence or close any RadialBlur algorithm mismatch.
- The selector-entry missing capture predates F54c. Cached translated-block/hook lifecycle is a possible cause, not proven here. Direct-call watches and the tested function watches do capture.
- A 256 MiB logical capture reservation permits one complete 4K float RGBA plane with before/after hex while bounding retained hex payloads to 1 GiB. Existing tiny absolute output-pixel watches are outside resident JSON and are not part of this reservation.

changed_files:
- AEXCompat commit 3ab60261: docs/RESIDENT_WATCHES.md; guest/crates/aex-guest-worker/src/{classic.rs,main.rs,x64.rs,x64/engine.rs,x64/types.rs,x64/trace.rs,x64/tests_cases.rs}.
- OLM tools/emulation/aexcompat_patches/F54c-resident-watches.patch and .md: durable source patch and instructions.
- OLM tools/emulation/aexcompat_patches/{install_F54c.py,verify_F54c.py,verify_F54c_4k.py,probe_F54c_entry.py,run_F54c_corpus.py,retain_F54c.py}.
- OLM tools/emulation/aexcompat_patches/verify_F54b.py: optional --scratch-root only; comparison logic unchanged.
- OLM orchestra/reports/F54c-evidence/* and this report.

verify:
Run from this OLM worktree (MAIN assets must remain available); each command uses only the original AEX and reference workers:

```sh
WORKER="$HOME/.cache/olm-emu/worker-F54c/aex-guest-worker"
PYTHONDONTWRITEBYTECODE=1 python3 tools/emulation/aexcompat_patches/verify_F54c.py --worker "$WORKER"
PYTHONDONTWRITEBYTECODE=1 python3 tools/emulation/aexcompat_patches/verify_F54c_4k.py --worker "$WORKER"
PYTHONDONTWRITEBYTECODE=1 python3 tools/emulation/aexcompat_patches/probe_F54c_entry.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/emulation/aexcompat_patches/run_F54c_corpus.py --worker "$WORKER"
python3 tools/emulation/aexcompat_patches/retain_F54c.py
```

Expected: 17 R06 cases/342 snapshots exact, two cropped captures exact, three 4K no-op/context captures exact. Entry-boundary probe records zero witnesses on both workers (known limitation, not a PASS). The full corpus command exits nonzero for the observed status differences; the saved final inventory has 5,579 exact successes, 106 matching non-successes, zero byte differences and two status differences. Wall-limit results can vary: preserve each observation instead of treating a passing retry as proof. The retention command records the failure as manifest status `differences`.

For rebuilding, apply the adjacent patch on e96d6ed9 in a space-free AEXCompat worktree or use the stacked branch. Set CARGO_TARGET_DIR=~/.cache/olm-emu/build-F54c/target and TMPDIR=~/.cache/olm-emu/build-F54c/tmp; run the build/test commands above from that source worktree. Redirect logs into ticket scratch; use one job. Installed source.tar preserves the full exact source independently of worktree lifetime. Existing installation is immutable; a relocated/revised binary is not expected to reproduce its binary hash.

next:
- Blocker follow-up: compare F54b/F54c/F53 execution timing and stop behavior on both retained RadialBlur cases, preserving default limits and failed outputs. Localize the cause before claiming the required F53 equivalence. Do not merge this as an all-corpus-qualified worker on the present evidence.
- Follow-up: investigate selector-entry watches after prior selector execution, including warm translated blocks and multiple resident frames; preserve the zero-capture baseline witness.
- N03 has an experimental registered pointer/geometry tracing worker with the measured R06 bindings, but the full-corpus gate remains blocked. No RadialBlur numerical fix is claimed.
