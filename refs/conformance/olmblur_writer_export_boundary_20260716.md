# OLMBlur 16bpc writer/export boundary witness - 2026-07-16

Mac-only actual-AEX/Unicorn witness. No production source, PNG tuning, global rounding change, ledger update, or AE exact promotion.

## FACT

- AEX: `plugins_2025/OLMBlur.aex`, SHA-256 `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.
- case_0004 Non-Legacy retained portable pre-store values `22037.498046875` and `26373.498046875` execute through the actual standard writer and store `22037` and `26373`.
- The Legacy alternate direct-memory writer is a separate ASM/decomp writer family; the existing Legacy full-worker fixture supplies the executable AEX coverage.
- Existing Legacy and Non-Legacy complete-worker fixture commands pass.

## INFERENCE

- case_0004 is already one word below the retained expected internal words before any claimed export mapping; this witness does not support changing the writer.
- case_0003's 20-point sign-mixed PNG residual remains unbound before the final exported word. The local run proves writer ownership, not the live AE residual.

## Unproven

- Windows same-run pre-store/store values, AE host/export ownership, and AE exactness remain unproven.

## Commands

```text
python3 tools/emulation/test_olmblur_writer_export_boundary_20260716.py
```

## Changed files

- `tools/emulation/test_olmblur_writer_export_boundary_20260716.py` (new)
- `refs/conformance/olmblur_writer_export_boundary_20260716.json` (new)
- `refs/conformance/olmblur_writer_export_boundary_20260716.md` (new)
