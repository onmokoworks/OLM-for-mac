# ColorKeep Smart geometry / realistic-v1 / P02a

200 seed/index cases: seed 1 and 20261024, 100 each, plus 18 explicit expanded
request, empty result and ROI cases at PF8/PF16/PF32 with aspect 1:1 and 4:3.
All Smart results are raw exact against the registered F52c original-AEX worker.
Classic results are retained independently; they are not this ticket's contract.
Expanded requests are clipped by the original's pass-through PreRender; this
corpus does not claim that ColorKeep itself expands result_rect beyond input.

Replay with `tools/fuzz/run.py --plugin colorkeep --jobs 1 --replay
 tests/fuzz_corpus/colorkeep_realistic_P02a --scratch
 orchestra/state/P02a-colorkeep-geometry/replay` (on one command line).
See orchestra/reports/P02a-colorkeep-geometry.md for provenance and measurements.
