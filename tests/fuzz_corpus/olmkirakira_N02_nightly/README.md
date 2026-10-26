# N02: 2026-10-25 overnight scalar PF32 nonfinite refusals

Three reduced witnesses copied from `orchestra/reports/nightly-20261025/witnesses/`.
Input bytes, parameters, geometry and original-worker binding are unchanged.
Candidate provenance is refreshed from the final standard replay.
`N02_origin` identifies each source. The saved result now records **both routes**:
Smart is exact after scalar box source admission; Classic still refuses. A true
saved-result replay therefore does not imply Classic output equality.

Use `python3 orchestra/reports/N02-kirakira-evidence/verify.py replays` from the
repository root. It passes each witness's original sampler and size bounds to
standard `tools/fuzz/run.py --replay`, and also replays the historical corpora.
The odd-even witness requires `--geometry realistic --size-sampler odd-even-v1
--max-size 1080 --size-max-height 1080`; the other two use realistic and
realistic-v2 respectively, with max-size 256. No historical corpus is rebaselined.
