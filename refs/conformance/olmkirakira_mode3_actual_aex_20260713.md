# OLMKiraKira Blur Mode 3 actual-AEX probe

Status: **captured**

## FACT

- The probe requests Blur Mode 3 at the FUN_181150790 helper boundary.
- The target hook is installed at FUN_181272ec0, the recovered GaussianBlur wrapper target.
- FUN_181163706 loads TLS index 0 from GS:[0x58], and FUN_1811637D1 reads the selected runtime object's generation at +0x8.
- The observed OpenCV error callback uses the Windows x64 RCX/RDX/R8/R9 register ABI; its error path returns to an intentional int3 and is not detoured.
- The actual AEX reached FUN_181272ec0; the four-argument Gaussian wrapper boundary is captured before executing its body.

## INFERENCE / LIMIT

- A Mat header is decoded from the wrapper argument only when its OpenCV magic/shape checks pass.
- A sidecar comparison is optional and is not evidence that the AEX used that exact OpenCV build unless the target hook is captured.
- The probe uses MSVC's uninitialized TLS epoch (-1) and leaves singleton construction, guard epochs, and per-thread vector creation to the AEX.
- R9 and the caller shadow words are retained as raw context, not promoted to Gaussian arguments; this callsite passes InputArray, OutputArray, Size, and sigmaX only.

## Execution

- AEX: `/Users/onmk/Documents/Projects/Personal/OLM as/aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex`
- SHA-256: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`
- Entry: `FUN_181150790 @ 0x181150790`
- Target: `FUN_181272ec0 @ 0x181272ec0`
- Input: `{"blur_mode": 3, "height": 7, "length": 5, "sigma": 0.0, "type": "CV_32FC1", "width": 9}`

- Fault boundary: `{"generation_check": {"generation_at_plus8": 0, "object": "0x181839f80", "qword_at_plus0": "0x181496408", "qword_at_plus8": "0x0", "rip": "0x1811637d1"}, "tls_container_accessor": {"global_container": "0x200005e0", "guard_218": 2147483651, "rip": "0x181163c80", "tls_epoch": 2147483661}, "tls_data_accessor": {"global_data": "0x20000670", "guard_1f8": 2147483649, "guard_208": 2147483650, "rax_return": null, "rip": "0x181163b40", "tls_epoch": 2147483661}, "tls_data_create": {"r8": "0x20000bf0", "rcx": "0x200005e0", "rdx": "0x0", "rip": "0x181165220"}, "tls_lookup": {"gs_0x58": "0x40000000", "rip": "0x181163706", "selected_generation_at_plus4": 2147483659, "selected_object": "0x40000100", "tls_index": 0}, "tls_selected": {"generation_at_plus4": 2147483659, "global_generation": 2147483656, "rip": "0x18116371e", "selected_object": "0x40000100"}, "vector_compare": {"requested_entry": "0x181839f80", "requested_generation": 0, "rip": "0x1811637e6", "vector_begin": "0x20000680", "vector_capacity": "0x20000780", "vector_end": "0x20000698", "vector_end_or_count": "0x3", "vector_field_plus50": 3, "vector_object": "0x200005e0"}}`

## Runtime singleton

- `{"generation": "0x0", "object": "0x181839f80", "per_thread_data": "0x20000960", "status": "initialized_before_downstream_fault", "tls_container": "0x200005e0", "tls_vector_begin": "0x20000680", "tls_vector_end": "0x20000698", "vtable": "0x181496408"}`

## Error callback ABI

- `{"abi": "windows-x64", "caller_return_site": "0x18115ea8b", "name": "FUN_181162610", "observed_error_code": "0xfffffffc", "post_call_trap": "int3", "registers": ["RCX", "RDX", "R8", "R9"]}`

## Captured boundary

- Hit count: `1`
- Size: `[0, 1]`
- sigmaX: `2.5`
- input wrapper: `{"flags": "0x1010000", "mat": {"channels": 1, "cols": 9, "data": "0x20000280", "depth_code": 5, "dims": 2, "flags": "0x42ff4005", "header": "0x20000380", "rows": 7, "sample_first_rows": [[0.01148897036910057, 0.05549173057079315, 0.10627298057079315, 0.17049632966518402, 0.2457490861415863, 0.34558823704719543, 0.4540441632270813, 0.48259422183036804], [0.34558823704719543, 0.45220592617988586, 0.5441176295280457, 0.6525735855102539, 0.7610294222831726, 0.8069853186607361, 0.8363969922065735, 0.6802045106887817]], "step_bytes": 36, "step_pointer": "0x200003e0", "values_f32": [[0.01148897036910057, 0.05549173057079315, 0.10627298057079315, 0.17049632966518402, 0.2457490861415863, 0.34558823704719543, 0.4540441632270813, 0.48259422183036804, 0.23253676295280457], [0.34558823704719543, 0.45220592617988586, 0.5441176295280457, 0.6525735855102539, 0.7610294222831726, 0.8069853186607361, 0.8363969922065735, 0.6802045106887817, 0.1292509287595749], [0.24448531866073608, 0.27389708161354065, 0.2867647111415863, 0.3014705777168274, 0.31617647409439087, 0.39338237047195435, 0.4696691334247589, 0.3750000298023224, 0.3345588445663452], [0.39338237047195435, 0.4852941334247589, 0.5937500596046448, 0.7022059559822083, 0.8088235855102539, 0.8694852590560913, 0.8568474650382996, 0.11764706671237946, 0.21725644171237946], [0.2991728186607361, 0.3216911852359772, 0.33639705181121826, 0.35110294818878174, 0.3658088445663452, 0.4264706075191498, 0.4159007668495178, 0.4227941334247589, 0.4375000596046448], [0.3779871165752411, 0.5330882668495178, 0.6415441036224365, 0.7500000596046448, 0.8419117331504822, 0.9191175699234009, 0.16819852590560913, 0.1672794222831726, 0.27389705181121826], [0.29871323704719543, 0.3694852888584137, 0.3841911852359772, 0.39889705181121826, 0.4283088445663452, 0.4434168040752411, 0.45197612047195435, 0.4495059847831726, 0.45582491159439087]]}, "object": "0x20000380", "wrapper": "0xf0fed90"}`
- output wrapper: `{"flags": "0x2010000", "mat": {"channels": 1, "cols": 9, "data": "0x20000400", "depth_code": 5, "dims": 2, "flags": "0x42ff4005", "header": "0x20000500", "rows": 7, "sample_first_rows": [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], "step_bytes": 36, "step_pointer": "0x20000560", "values_f32": [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]}, "object": "0x20000500", "wrapper": "0xf0feda8"}`
- raw R9 (not an argument): `0x9`

## Sidecar

- `{"status": "not_requested"}`
