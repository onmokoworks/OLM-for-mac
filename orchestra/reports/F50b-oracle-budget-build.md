status: partial

summary:
- Built and installed F50 in the authorized space-free cache build directory; INDEX registered and build directory deleted.
- Normal synthetic PE returned; two production-budget exhaustion runs stopped at the exact same 2,000,000,000-instruction boundary.
- Both named RadialBlur smoke cases exhausted F50's instruction budget rather than returning.
- Corpus comparisons are in progress; S01 and seed-1 campaigns remain pending. Defaults unchanged.

facts:

FACT — build:
- `python3 tools/emulation/aexcompat_patches/build_F50.py` exited 0. Cargo jobs=1, offline/locked release build took 2m48s; pre-build memory free was 57%.
- Installed `/Users/onmk/.cache/olm-emu/worker-F50-budget/aex-guest-worker`; SHA256 `92be4c0c8d873c6b9b20238b0389afadc64096e97193e2cac09be4441d7069d6`.
- INDEX has exactly one matching F50 entry. Source and build manifest retained in cache. `/Users/onmk/.cache/olm-emu/build-F50` removed.
- Build manifest binds all 546 source files, parent worker and unchanged F50 patch. Original AEXCompat trees and MAIN were not edited.

FACT — smoke:
- `python3 tools/emulation/aexcompat_patches/smoke_F50_budget.py` exited 0. Synthetic normal return: 0.320935 s.
- Exhaustion runs: 709.005955 s and 679.583908 s; both RAX=1,000,000,000 and RIP=0x180001005 (RVA 0x1005). The fixture executes one XOR then alternating INC/JMP; this is exactly the 2-billion instruction boundary.
- The assertions were added while the original smoke process was already running. Both saved snapshots were independently checked afterward with the identical assertions; the committed script includes those assertions for future runs.
- `python3 tools/emulation/aexcompat_patches/verify_F50.py smoke` exited 0. This mode records observations; exit 0 does not assert equality.
- C49_seed1_case000117: F46 reject at 20.013962 s; F50 instruction budget at 861.385241 s, RIP 0x1800029b9; no output pair.
- C46_seed1_case000280: F46 reject at 20.014 s; F50 instruction budget at 854.926 s, RIP 0x1800029f1; no output pair.
- A premature corpus invocation overlapped the last smoke case briefly, within the two-process limit. It recorded 97 complete pairs (91 identical, 6 uncompared) before being stopped. Its in-flight pair was not recorded. Corpus resumed after smoke completed, retaining completed rows. No paused process remains.

FACT — interim corpus:
- Full inventory is 769 cases in 9 plugins; ColorKeep has no retained corpus. The recipe adds six explicitly labeled generated depth/route anchors for ColorKeep.
- OLMBlur: 72 identical, 6 uncompared; both workers reject the same allocation request for each of those six Classic rows.
- ColorKey: 18 identical. DirectionalBlur: 166 identical.
- Remaining results are not yet measured. Machine-readable completed pairs are in `F50b-evidence/corpus.jsonl`; no equality is inferred from rejection.

inference:
- The loop proves deterministic exhaustion at the configured production instruction boundary for this fixture, despite differing elapsed times. It does not establish a fixed runtime bound for arbitrary guest/host callbacks or all 257 scheduler slices.
- The configured 2-billion-per-slice budget is insufficient for both named slow RadialBlur cases. F50 should not become the fuzz default on this evidence.
- The 3600-second external watchdog exceeded measured smoke times, but remains unqualified for all plugin calls.

changed_files:
- `tools/emulation/aexcompat_patches/build_F50.py`
- `tools/emulation/aexcompat_patches/verify_F50.py`
- `tools/emulation/aexcompat_patches/smoke_F50_budget.py`
- `tools/emulation/aexcompat_patches/summarize_F50.py`
- `orchestra/reports/F50b-evidence/`
- This report.

verify:
```sh
python3 tools/emulation/aexcompat_patches/smoke_F50_budget.py
python3 tools/emulation/aexcompat_patches/verify_F50.py smoke
python3 tools/emulation/aexcompat_patches/verify_F50.py corpus
python3 tools/emulation/aexcompat_patches/verify_F50.py slow
python3 tools/emulation/aexcompat_patches/verify_F50.py campaigns
python3 tools/emulation/aexcompat_patches/summarize_F50.py
git diff --check
```
Expected for measured smoke: synthetic assertions pass; two real-AEX pairs are uncompared with F50 instruction exhaustion. Other expected totals are pending. Corpus/slow reruns resume completed rows; archive the evidence directory before requesting an entirely fresh run. Build recipe intentionally refuses to overwrite retained workers.

next:
- Finish corpus, all 174 S01 Smart-failure transitions, and both workers' DG/Radial seed-1 n300 campaigns.
- Proposal only: retain current F46 default until budget sufficiency and runtime are qualified. Do not apply a fuzz default or timeout switch in this ticket.
