# OLMKiraKira Mode 3 live Gaussian capture

Windows desktop-required, one fresh AE run. The selected manifest case is final_random10_olm_kira_kira_03 and its manifest Blur Mode is 3. The runner applies match-name overrides {"OLM OLM Kira Kira-0003": 5, "OLM OLM Kira Kira-0004": 0, "OLM OLM Kira Kira-0005": 0, "OLM OLM Kira Kira-0026": 0} so the first Gaussian setup is expected to be kernel size 21, sigma 2.5, type 5.

The runner relays through Windows PowerShell 5.1, requires an interactive desktop session, canonicalizes every work/marker path to an absolute path, and first runs a minimal AE JSX launch/ready preflight with no case, AEX, CDB, render, or algorithm claim. Only after that marker is observed and the preflight AE exits does it run the pause marker, fixed no-space JSX launch path, live hash-pinned module lookup, absolute base-plus-RVA breakpoints, and fail-closed marker policy from the 2026-07-13 retry harness. It captures the first getKernel output cv::Mat.data pointer after return and writes exactly 21 little-endian float32 words.

Any missing AE ready/module/hook/argument/word/same-run field returns exact_bind_failure.
