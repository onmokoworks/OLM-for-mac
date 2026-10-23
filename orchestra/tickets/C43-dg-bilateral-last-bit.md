# C43: DistanceGradation Smart PF8 Bilateral — reproduce the original's last-bit float result

## Facts (C39, C40 reports)
- For seed45 case2 the original's post-filter words are FLOAT32 `01805443` (212.50001525878906).
  Mac computes `00805443` (212.5). The pre-filter half-tie levels are 42.5 / 127.5 / 212.5.
  A last-bit difference across a byte-quantization tie flips output bytes.
- C40 merged an **interim guard**: Smart PF8 Bilateral Size0 refuses fields with half-integer
  pre-filter ties. It costs 5 previously exact cases: seed1 indices 4/9/146, seed44 275, seed45 245.
- Separately, seed44 case70 (PF8 Bilateral Size7, 16x21) remains a Smart mismatch: 8 bytes;
  original `39`, Mac `38`.

## Goal
Make the Mac bilateral arithmetic bit-identical to the original. Then remove C40's guard,
recovering the 5 cases plus the witness, and fix case70.
- Using the decomp/disasm (the original IPP/OpenCV-style bilateral), compare against the Mac
  implementation: weight computation (exp table vs direct), the float accumulation order
  (SIMD lane order, horizontal adds), the normalisation divide vs reciprocal multiply,
  `FMA` vs separate ops, and the `ucrt` exp now available (`ucrtmath`).
- Use the paired plane tracers to find the first word that differs inside the filter loop for
  case2 and case70.

## Acceptance
- Seeds 1, 44, 45, 46 and one fresh seed, n300: 0 Smart mismatches.
- The 5 cases C40 lost are exact again, with the guard removed.
- Replay the corpus. Rebaseline only refusal/mismatch → exact.
- If not resolved after two refuted hypotheses, keep the guard and report what you learned.
- Use 1-2 processes. Do not touch the release gate/ledger.
