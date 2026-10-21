## Goal
Make `tools/fuzz/run.py --replay` use the oracle worker recorded in each corpus file's
provenance (`worker_path` + `worker_sha256`) by default, so replays are comparable without
manual `--worker`. Same for `--case-timeout` if the corpus records one.

## Facts
- After F13, `tests/fuzz_corpus/radialblur` was rebaselined with
  `/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/...` (sha 93622cbc...). Replaying with
  the default worker (3cb4855b...) gives 6/35 matches; with the recorded worker 35/35.
- Other plugins' corpora use the default worker.

## Requirements
- If the recorded worker path exists and its sha matches: use it. If sha mismatches or missing:
  fail clearly (exit non-zero, message naming the file), unless `--worker` is given explicitly.
- A corpus may contain mixed workers: group replays per worker.
- Add a test in `tools/fuzz/test_framework.py`.
- Verify: replay every plugin corpus under `tests/fuzz_corpus/*` with no `--worker` flag;
  report matches per plugin (expect all True). Use --jobs 2.
