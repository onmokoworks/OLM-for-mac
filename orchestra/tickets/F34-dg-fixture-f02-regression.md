# F34: DistanceGradation retained fixed-fixture regression (748 bytes) since F02

## Facts (I02, `orchestra/reports/I02-bisect-distance.py`, `reports/integration_I02_evidence.json`)
- The DG retained fixed-fixture regression passes two 2992-byte fixtures at a95eebfc, the first
  parent of F02.
- At the F02 merge f7ce7e67 and at HEAD, the first fixture differs by 748 bytes. The harness does
  not print the first mismatch.
- F02 = "dg default owner compose" (`orchestra/reports/F02-dg-default-owner-compose.md`).

## Goal
Decide which side is right and fix the wrong one in general code.
1. Find where the fixture's expected bytes came from: the original AEX (emulator/native capture)
   or an older Mac output. Use its provenance file or git history.
2. Rerun the original AEX on that fixture with the current default worker, and also with the F30
   worker (INDEX). Compare raw bits with the expected bytes and with HEAD's Mac output.
   Report the first mismatch (offset, channel, values).
3. Outcomes:
   - Mac is wrong: fix the general cause and keep all F02, C14, C19 and C27 gains. The DG corpus
     must still replay 145/145, and seed-1 n300 must not lose any exact case.
   - The expected bytes were not AEX truth: do not edit the expected file. Report it as such with
     evidence. The orchestrator decides.
- Do not touch the release gate or ledger. Use 1-2 processes.
