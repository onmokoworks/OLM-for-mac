These are diagnostic pixel mismatches from T06's scratch-only gate-off build.
Do not replay them as production acceptance fixtures or promote the bypass.

One representative is retained for each of the 62 output signatures in the
seed-1, 300-case campaign. Selection minimizes pixel area, then compressed input
size, then original case index among that signature's saved reductions. The
bounded greedy shrinker used at most 24 attempts / 8 seconds per input; global
minimality and a distinct root cause per signature are not claimed.

Replay with `tools/fuzz/triage_kirakira.py --experiment all --plugin olmkirakira
--jobs 2 --replay tests/fuzz_corpus/olmkirakira_gate_off_T06 --scratch
orchestra/state/T06-triage-kirakira --report
orchestra/state/T06-triage-kirakira/cluster-replay.json --details
orchestra/state/T06-triage-kirakira/cluster-details.json` (join onto one line).

The switch bypasses outer tuple admission, the Smart request-admission return,
and typed row alignment in a generated scratch translation unit. It leaves
request normalization, geometry/span checks and helper algorithm fallbacks
unchanged. Smart tiny requests can therefore still fail. No production source
contains the gate-off switch. See `orchestra/reports/T06-triage-kirakira.md` for
limitations, provenance, byte statistics and follow-up tickets.

The other 41 saved reductions are retained under `other_reductions/` so the
minimum selection and signature membership can be audited. Directory replay
uses only the 62 top-level JSONs. All 103 reductions were observed in the full
campaign; the selected 62 were additionally replayed unchanged.
