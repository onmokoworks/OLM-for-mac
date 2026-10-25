# C01 — PF32 NaN Lab component matching and positive Thin

Label: `C01-pf32-nan`. Original AEX CPU Smart versus production Mac Smart,
raw ARGB bytes, no tolerance. The reference/fast split is unchanged.

- `reduced-2081.json`: N01's committed 1x8 reduced witness.
- `2081.json`, `3790.json`, `5995.json`: unreduced N01 default sampler cases,
  seed `812324792801853187`; regenerated from the observed index range.

The original report retained only the first reduced signature. The C01 scan
replayed all 144 PF32 Lab76/Lab94 component-mode cases in its 18,377 observed
indices and recovered exactly these three unreduced mismatches. The additional
reduced replay made 145 checks. Before/after results and the original worker
and AEX hashes are retained in `orchestra/reports/C01-evidence`.

Lab per-component COMISS/JA accepts unordered differences. Positive PF32 Thin
UCOMISS/JNE treats NaN matte alpha as zero and copies source RGBA when its
distance is within the amount. These two instruction predicates explain the
finite replacement and the later restoration in the unreduced witness.

Recheck: `python3 orchestra/reports/C01-evidence/verify.py corpus`.
This preserves each corpus's original route set, including these Smart-only
N01 cases; it does not add a Classic observation to historical Smart results.
