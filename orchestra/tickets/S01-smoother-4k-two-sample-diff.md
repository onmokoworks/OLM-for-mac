# S01: OLMSmoother v1, Full 3840x2160 8 bpc: real AE output differs from the same bundle in our host in 2 samples

## Facts (A02g, `orchestra/reports/A02g-real-ae-retest-downsample.md`)
- In real AE 2026 (A02e project `defaults-3840x2160-8.aep`, OLMSmoother at Full, defaults), the output differs from the same installed bundle run in the F47d/F51 full-frame host in **2 samples**. The first is (1649,1235), channel B: AE=0xde, host=0xdf.
- At ≤1920x1080 the same plugin matched the original AEX on F53 exactly. 4K could not run on the oracle at the time; F54 may now allow it.

## Do
1. Reproduce it. Feed the exact input pixels (the A02e/A02f control frame at 4K) to:
   - the Mac bundle in our host, with and without `OLM_PARALLEL_MAX=1`, and the reference build (R10);
   - the original AEX on the oracle at 4K, if F54's arena allows it (`~/.cache/olm-emu/worker-F54/`).
   Decide which side matches the original.
2. If AE ≠ our host for the same bundle: find out what AE passes differently. Possible differences are rowbytes, world origin, extent_hint, Classic vs Smart, the thread/MFR context and the input values (check that the input sample is identical by rendering the control). Add a scratch-only trace build if needed. Never install it into the AE folders.
3. If the plugin output depends on something nondeterministic (uninitialized memory, data races, the P05c bounded stack clears), find it with ASan/MSan-style checks and TSan, and fix it. Verify with R10 `ref_vs_fast`, default fuzz, and all Smoother corpora replaying true.

## Rules
- Use 1-2 processes. Change only Smoother sources. Do not touch the release gate or ledger. Do not run AE GUI; aerender on existing projects is allowed if no other AE/aerender is running. The stop rule applies.
