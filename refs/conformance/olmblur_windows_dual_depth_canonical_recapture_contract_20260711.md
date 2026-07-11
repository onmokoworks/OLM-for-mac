# OLMBlur Windows dual-depth canonical recapture contract

This package owns only the generated reference-request ZIP and its generator/smoke artifacts. It does not modify NAS content, an existing package, plugin source, or the conformance ledger.

Required installed plugin: `OLMBlur.aex` with SHA256 `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`. The Windows runner records its absolute path, byte size, UTC mtime, and SHA256 in `run/return_manifest.json` and exits `hash_mismatch` before After Effects starts on mismatch.

The seven canonical cases are rendered in two Software lanes: 8bpc PNG and 32bpc OpenEXR. Both lanes force linear blending off and record AE version, project renderer, bits per channel, working space, and linear blending. The 32bpc lane requires the exact output-module template `OLMBlur OpenEXR RGBA Float32 No Compression`, whose return contract is OpenEXR, four-channel RGBA, 32-bit float samples, and no compression.

Each lane also emits a case_0001 disabled-effect control. The return is not accepted as rendered unless all fourteen case outputs and both controls exist and every AE result reports `status=ok`.
