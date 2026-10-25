Draft only — not posted.

Title: Add optional guest session geometry and on-demand UHD frame storage

Guest sessions previously lacked OLM's downsample and cropped-checkout geometry, and their dimension/data limits prevented UHD rendering. Add opt-in downsample, padded rowbytes, extent/request rectangles, pixel aspect, negotiated output, and explicit/automatic cropped input checkouts. Existing OLM F52/F52c/F53 option names work directly. Raise render bounds to 3840x2160 and map only required overflow pages within a bounded 2 GiB frame range. Preserve existing small-allocation addresses, reuse negotiated output capacity, and release cropped descriptors after checkout scopes.

Validation: Release worker tests pass (702 library + 10 CLI; 3 ignored). Whole-tree rustfmt passes for 229 files. Nine UHD Smart cases and three PF32 full-HD cases succeed for OLMBlur, ColorKey, and DirectionalBlur; measured peak worker RSS is below 841 MB. Tests use constant finite input and declared default parameters.

Direct F53 comparison matches all 44 ColorKey and all 15 Smoother2 corpus cases, plus all eight fixed cropped-checkout witnesses. Blur matches 57/60 full-corpus cases; all cases execute successfully, but three have byte differences. The 1,000-case survey records 901 successful exact frames, 51 matching non-success statuses, 14 byte differences and 34 Smoother DEEP_PIXELS rejections where F53 succeeds. Full results and hashes are in the F54 report. Do not present this as a complete replacement for the OLM oracle. Separate math/NaN patches remain outside this geometry change.

Local review: fixed negotiated allocation growth, cropped-world descriptor ownership, and mixed input/output depth identity. Re-reviewed source, behavioral tests, the type annotation fix, and documentation; no accepted outstanding or rejected findings. Reviewed HEAD: `5a9bd8f7f7dd128f2d5c6c037ce3a71a14b7504c`.

No Closes clause: no upstream issue was created/claimed under the ticket's no-posting exception. No push, PR, or merge has been performed. CI and Windows-native tests have not been run.
