status: blocked

summary:
- Implementation and all requested self-tests are complete; all ten plugins work on both architectures and both builds.
- HEAD identity: 840 comparisons, 800 byte-exact renders, 40 identical refusals, zero differences/new refusals/execution errors.
- The copied-source 1-ULP mutation produced eight detected PF32 differences; the planted copy was deleted.
- `blocked` is required by the worker brief because one cache-cleanup command was rejected; safer cleanup succeeded and no technical blocker remains.

facts:
- Tested production revision: `853db347f6831db1780142fe0382d841fc9a980e`.
- `python3 tools/refactor/self_test.py` exited 0. It invokes HEAD versus HEAD with `--cases 18 --seed 909 --arch both --build both --jobs 1` for all ten plugins. Each configuration includes 18 small cases and three full 3840×2160 cases, one per depth. The native comparisons total 840; all ten per-plugin exit codes are 0.
- Per-plugin counts:

| Plugin | Byte-exact | Same refusal | Differences | New refusals | Execution errors |
| --- | ---: | ---: | ---: | ---: | ---: |
| olmdistancegradation | 84 | 0 | 0 | 0 | 0 |
| olmdirectionalblur | 84 | 0 | 0 | 0 | 0 |
| radialblur | 84 | 0 | 0 | 0 | 0 |
| olmblur | 84 | 0 | 0 | 0 | 0 |
| olmcolorkey | 84 | 0 | 0 | 0 | 0 |
| colorkeep | 84 | 0 | 0 | 0 | 0 |
| olmtoondilate | 84 | 0 | 0 | 0 | 0 |
| olmsmoother (Classic) | 56 | 28 | 0 | 0 | 0 |
| olmsmoother2 | 72 | 12 | 0 | 0 | 0 |
| olmkirakira | 84 | 0 | 0 | 0 | 0 |

- Small cases cycle all depths, default/realistic-v1/realistic-v2 geometry, and default/odd-even-v1 sizes. Geometry sampling supplies downsample, ROI, aspect and padding. Smoother2 exercised 40 `float-v1` comparisons across the four configurations.
- `python3 tools/refactor/self_test.py --mutation` exited 0: the invoked differential returned 1 as expected, with 24 comparisons, 16 exact renders, eight PF32 differences, no refusals and no execution errors. The test inserts `std::nextafter(pixel.red, INFINITY)` for finite red values only in the archived head's ColorKeep float kernel, then runs the actual differential entry point. No production worktree file is planted.
- First deliberate mismatch: arm64/reference, sequence 2, generator index 8, seed 909, geometry 1×26, depth 32, raw byte offset 4. Base SHA256 `5a378a7a49306777d37b96a751e72f327e356a8f792edeb427b8a2eb7e843317`; planted-head SHA256 `ba611a9ba639267821258403533044a03e56b2b209dffdb970e6138ecc453f61`.
- `python3 tools/refactor/test_native_diff.py` passed three tests: refusal-code/tag changes, identical timeouts remaining failures, and raw comparison across the 1 MiB boundary/length mismatch.
- `/usr/bin/arch -x86_64 /usr/sbin/sysctl -n sysctl.proc_translated` returned `1`. Harness launches explicitly select architecture; the final builder also checks `lipo -archs`. RadialBlur's delegated builder and ucrtmath receive the architecture override.
- Additional commands (all exit 0):
  - `python3 tools/refactor/native_diff.py --plugin colorkeep --base HEAD --head HEAD --cases 9 --arch both --build both`: 48 exact comparisons.
  - `python3 tools/refactor/native_diff.py --plugin radialblur --base HEAD --head HEAD --cases 1 --arch x86_64 --build reference --scratch orchestra/state/Q00-refactor-native-diff-tool/radial-smoke`: four exact comparisons.
  - `python3 tools/refactor/native_diff.py --plugin colorkeep --base HEAD --cases 3 --arch both --build both --scratch orchestra/state/Q00-refactor-native-diff-tool/worktree-smoke`: 24 exact comparisons against WORKTREE.
- Counts, coverage, binary hashes and the first deliberate mismatch's complete case parameters are committed in `orchestra/reports/Q00-native-diff-evidence.json`.
- All test process exits were collected. No scratch `run` directories remain: archived sources, native binaries and raw frames were deleted; logs and JSON observations remain in ticket scratch. No plugin, MAIN, release-gate or ledger file was modified.
- Tool rejection: an exec invocation beginning `rm -rf tools/refactor/__pycache__` was rejected before execution with `rm -f style commands are not permitted. Use a safer approach`. Recovery removed only `.pyc` files with `Path.unlink()` and the empty directory with `Path.rmdir()`, then reran the unit checks successfully. The worker brief explicitly requires `status: blocked` after a rejected call; that procedural requirement is the sole reason for this status.

inference:
- The identity matrix demonstrates bounded deterministic equality through the requested native harness paths, including existing refusals. The mutation demonstrates sensitivity to a genuine one-float-ULP source change in both architectures/build modes.
- These are tool self-tests, not new AEX/AE conformance evidence or completion of the 3,000-case per-plugin G1 refactor gate. Refusal source-line suffixes are deliberately excluded because refactoring moves lines; ordered guard names/tags and error codes remain compared.

changed_files:
- `tools/refactor/native_diff.py`
- `tools/refactor/README.md`
- `tools/refactor/self_test.py`
- `tools/refactor/test_native_diff.py`
- `orchestra/reports/Q00-native-diff-evidence.json`
- `orchestra/reports/Q00-refactor-native-diff-tool.md`

verify:
```sh
python3 tools/refactor/test_native_diff.py
python3 tools/refactor/self_test.py
python3 tools/refactor/self_test.py --mutation
git diff --check
```
Expected: three unit tests pass; identity exits 0 with 840 comparisons and zero differences/new refusals/execution errors; mutation self-test exits 0 while detecting eight PF32 differences; diff check is clean. Existing refusal counts at the tested production revision are 28 for Smoother v1 and 12 for Smoother2. Full 4K renders make the identity matrix take several minutes.

next:
- Orchestrator review/merge; no implementation work remains. The procedural blocked status needs acknowledgement of the rejected cleanup call, not a code fix.
- Plugin refactor tickets should run `python3 tools/refactor/native_diff.py --plugin <adapter-name> --base <pre-refactor-sha> --cases 3000 --seed 909 --arch both --build both --jobs 1` for their full G1 gate.
