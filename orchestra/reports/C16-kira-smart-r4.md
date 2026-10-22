status: blocked

summary:
- Stopped this worker after discovering a concurrent, independently launched C16 worker in the same worktree.
- Both workers launched seed-1 campaigns targeting the same report and log paths; those paths cannot establish independent evidence for this run.
- No production code, admission, corpus expectation, release gate or ledger change was made by this worker.
- No cluster was closed and no residual improvement is claimed.

facts:
- Starting HEAD: `e29f1a802457a613b3c595425e4037b32077a465`, branch `orch/C16-kira-smart-r4`; initial tracked status was clean.
- Read AGENT_GUIDE, emulator GOTCHAS, compatibility plan, relevant ledger entries, T06/F09/F12 and C13 reports, and the retained-worker INDEX.
- Started `python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch orchestra/state/C16-kira-smart-r4 --report orchestra/state/C16-kira-smart-r4/before-seed1.json --corpus orchestra/state/C16-kira-smart-r4/before-corpus`, redirecting to `before-seed1.log` in that scratch directory.
- `ps -axo pid,ppid,etime,command` showed two C16 orchestration launchers (PIDs 71781 and 72554), another Codex process (72564), and two simultaneous campaigns. The other campaign PID 73370/parent 72564 used absolute paths and `before-seed1-corpus`; this worker's campaign PID 73428/parent 72866 used relative paths and `before-corpus`. Both resolved to the same `before-seed1.json`; both had live AEX worker children.
- The two live build directories were `run_1dbqqlhl` (other campaign) and `run__d3f79e6` (this campaign), confirmed by their AEX child command lines. This is a same-ticket collision, not merely the expected second worker on another ticket.
- Sent SIGTERM only to this campaign PID 73428 and its observed descendants 77636/77644. Subsequent process inspection showed 73428 absent. Removed only this campaign's regenerable `run__d3f79e6` build tree. Other worker processes and files were left intact.
- Source SHA256 at stop: `643a6d545a22e3aabf0003ea0b0d661e942b502ff5a29c23b1cfb290e32c07f8`, matching the C13 reported source. Scratch measured 2,590,318 bytes at cleanup (shared scratch may subsequently change).
- No completed baseline, sanitizer result, first mismatch or acceptance counts are attributed to this interrupted run. Any shared campaign report needs ownership verification before use. C13's 222 exact / 0 mismatch / 78 refusal remains prior evidence, not a new measurement by this worker.

inference:
- Concurrent ownership can overwrite evidence and interleave edits/commits; proceeding would risk invalidating the ticket's provenance and two-process resource limit. This operational collision blocks this worker safely continuing.
- Static inspection suggests the Channel 6 four-plane constructor is still a useful next target, but this worker obtained no paired trace or new numerical boundary and makes no recovery claim.

changed_files:
- `orchestra/reports/C16-kira-smart-r4.md` (this report only).

verify:
```sh
git show --stat HEAD
git diff HEAD^ HEAD -- mac/OLMKiraKira/OLMKiraKira.cpp
ps -axo pid,ppid,comm
```
Expected for this report commit: one report added, no production diff. PID 73428 should be absent; process IDs are historical and may later be recycled. Inspect full command lines locally if determining current C16 ownership.

After assigning exactly one owner, remeasure using a fresh, uniquely named scratch subdirectory:
```sh
s="$PWD/orchestra/state/C16-kira-smart-r4/single-owner-recheck"
mkdir -p "$s"
python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/before-seed1.json" --corpus "$s/corpus" > "$s/before-seed1.log" 2>&1
```
Expected if production source remains at the hash above: C13's 222/0/78 Smart baseline; this worker did not complete an uncontaminated recheck.

next:
- Orchestrator: resolve duplicate C16 launches and allow the designated owner to continue. This report records only the interrupted worker's actions and must not overwrite or supersede subsequent validated results from the surviving owner.
- Complete the ticket's cluster selection, gate-off/paired traces, seed-1 plus fresh-seed proof, sanitizer and corpus checks under single ownership.
