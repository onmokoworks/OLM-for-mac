# KiraKira Smart geometry (P02c)

Separate `realistic-v1` corpus: seeds 1 and 2, 100 cases each; 72 explicit
geometry probes with 8/16/32bpc, 1:1/1:3/2:3 downsample, approximation on/off,
full/subrect/expanded/empty requests, 4:3 aspect and seven-byte row padding.
Inputs are embedded losslessly; comparisons use F52c AEX Smart and negotiated
output bounds. Seed 2 index 48 is an unavailable original IPP exception, not
an exact or tolerated case. Historical corpora retain their saved expectations.

Replay serially with `python3 tools/fuzz/verify_kirakira_geometry_P02c.py
--label replay --replay --jobs 1`. See the ticket report for provenance and limits.
