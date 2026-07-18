# OLMBlur case_0004 checkpoint/resume boundary audit (2026-07-18)

## Result

- Classification: `helper_entry_observed_helper_output_incomplete`.
- This is Mac-only actual-AEX Unicorn evidence; it is not AE exact or Windows conformance evidence.

## FACT

- Pinned AEX SHA-256: `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.
- Natural checkpoint reached `0x180001000` after `15958497` instructions.
- Resume cap: `100000000` instructions; observed helper calls: `1`; writer pre-store hits: `0`.
- Completed helper calls retain source/destination float32 words before and after the actual helper body: `0/1`.
- Each recorded writer retains pre-store RGB float32 words and destination ARGB16 words before/after the actual writer body.

## INFERENCE

- The bounded classification is `helper_entry_observed_helper_output_incomplete`.
- Helper entry/output and writer boundaries are separated by same-run observations; this does not identify the first Mac-vs-Windows divergence.
- No production source edit is justified by this audit alone.

## Reproduction

```text
python3 tools/emulation/audit_olmblur_case0004_checkpoint_resume_20260718.py
python3 tools/emulation/test_olmblur_case0004_checkpoint_resume_boundary_audit_20260718.py
```

## Changed files

- `tools/emulation/audit_olmblur_case0004_checkpoint_resume_20260718.py`
- `tools/emulation/test_olmblur_case0004_checkpoint_resume_boundary_audit_20260718.py`
- `refs/conformance/olmblur_case0004_checkpoint_resume_boundary_audit_20260718.json`
- `refs/conformance/olmblur_case0004_checkpoint_resume_boundary_audit_20260718.md`
