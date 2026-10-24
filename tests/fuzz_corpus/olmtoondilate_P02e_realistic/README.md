# P02e realistic Smart geometry witnesses

Separate from default-geometry historical corpora. Contains realistic-v1 seed 1
and seed 20261024, n100 each, plus 36 labelled boundary cases across PF8/PF16/PF32:
full/subrectangle/expanded/empty requests, unequal X/Y downsample, pixel aspect,
non-full extent, odd rowbytes, and radii immediately around float32 6.0.

All 236 Smart outputs were exact against the registered F52c AEX worker. Expanded
requests are clipped by the oracle's checkout result; this is not evidence of
expanded output allocation. Oversized storage is separately covered by the
ASan/UBSan ROI unit test. This set proves hostless CPU agreement, not native AE.

Regenerate: `OLM_TEST_JOBS=1 python3 mac/OLMToonDilate/tests/geometry_witnesses.py`.
Replay with `tools/fuzz/run.py --plugin olmtoondilate --jobs 1 --replay` this folder,
using ticket-local `--scratch` and `--report`. Compare Smart pixel status, not the
historical saved object equality (the generic replay also includes Classic).
