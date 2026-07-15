# OLMToonDilate PF16 Actual-AEX Stage Audit - 2026-07-16

## Result

- Status: **PASS_STAGE_BOUNDARY_CLASSIFIED**
- The worker calls the captured five-argument host PF_COPY callback at `0x1801a5b5e` and resumes at `0x1801a5b61`.
- At resume, output visible bytes equal raw input bytes and output padding remains owned by the output sentinel.
- This is bounded worker evidence only; the host PF_COPY behavior remains an inference, not an AE-exact contract.

## Evidence

- Gates: `{'worker_return_confirmed': True, 'one_helper_capture': True, 'pf_copy_callback_captured': True, 'pf_copy_resume_captured': True, 'callback_output_visible_equals_raw_input': True, 'helper_copies_exact_pf16_words': True, 'padding_sentinel_preserved': True, 'helper_source_and_destination_in_output_payload': True, 'alpha_matrix_only_32768_seed_or_propagate': True}`
- Raw host input: `[[16384, 24000, 8000, 4000], [32768, 1234, 2345, 3456]]`
- Helper source/destination: `[[32768, 1234, 2345, 3456]]` / `[[32768, 1234, 2345, 3456]]`
- Callback/resume evidence: `{'kind': 'pf_copy_callback', 'abi': '5 args', 'args': ['0x1234', '0x20000020', '0x200000a0', '0x0', '0x0'], 'return_address': '0x1801a5b61', 'source_world': '0x20000020', 'destination_world': '0x200000a0', 'source_payload': '0x20000000', 'destination_payload': '0x20000080', 'width': 2, 'height': 1, 'source_rowbytes': 20, 'destination_rowbytes': 20, 'visible_bytes_per_row': 16, 'copied_rows': [{'source': 536870912, 'destination': 536871040, 'bytes': 16}]}` / `{'address': '0x1801a5b61', 'input_visible_after_callback': [0, 64, 192, 93, 64, 31, 160, 15, 0, 128, 210, 4, 41, 9, 128, 13], 'output_visible_after_callback': [0, 64, 192, 93, 64, 31, 160, 15, 0, 128, 210, 4, 41, 9, 128, 13], 'output_padding_after_callback': [165, 165, 165, 165], 'output_visible_equals_input': True}`
- PF16 alpha matrix: `[{'alpha': 1, 'seed_or_propagate_observed': False, 'callback_resume_confirmed': True, 'callback_output_equals_raw_input': True}, {'alpha': 16384, 'seed_or_propagate_observed': False, 'callback_resume_confirmed': True, 'callback_output_equals_raw_input': True}, {'alpha': 32767, 'seed_or_propagate_observed': False, 'callback_resume_confirmed': True, 'callback_output_equals_raw_input': True}, {'alpha': 32768, 'seed_or_propagate_observed': True, 'callback_resume_confirmed': True, 'callback_output_equals_raw_input': True}, {'alpha': 32769, 'seed_or_propagate_observed': False, 'callback_resume_confirmed': True, 'callback_output_equals_raw_input': True}, {'alpha': 65535, 'seed_or_propagate_observed': False, 'callback_resume_confirmed': True, 'callback_output_equals_raw_input': True}]`

## Consequence

No internal-stage transformation claim is made. The binary worker classification is limited to callback copy bytes, padding ownership, helper placement, and the observed alpha boundary: only `32768` seeded or propagated.

## Reproduce

```sh
tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_pf16_actual_aex_cli_differential_20260716.py
```
