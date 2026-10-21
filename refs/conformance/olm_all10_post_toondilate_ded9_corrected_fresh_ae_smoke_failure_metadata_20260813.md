# OLM all10 post-ToonDilate corrected smoke failure metadata

Status: `FAILURE_PRESERVED_NO_RETRY_FORMAL_GATE_BLOCKED`.

The single corrected AE invocation did not create `ae_return.json` or any PNG. After Effects accepted the early `get version` probe approximately 0.34 seconds after launch, then `DoScriptFile` entered an AE error dialog with:

> スクリプトファイルを実行できません。スクリプト機能のプラグインがインストールされていません。

The Sentry breadcrumb attributes that dialog to `AEDoScriptFileCommand performDefaultImplementation`. The later minidump records `OnForceQuit`, `sendingProcess=Python`, and `SIGTERM`; therefore it was caused by the runner's exact owned-PID cleanup after the hang. It is not evidence that OLMToonDilate crashed After Effects.

The raw report, summary, one-shot receipt, launch wrapper, minidump, Sentry event, breadcrumb, and session record are preserved and SHA-256-bound by the adjacent JSON. Exact TERM/KILL was initially limited to owned PID 36723; it remained in `UE` state while AdobeCrashReport was still attached. After the dump hash was verified, the root coordinator stopped exact AdobeCrashReport PID 38140, exact Adobe crashpad PID 36747, exact owned AE PID 36723, and the two resulting exact orphan helpers (dynamiclink PID 37527 and TeamHub PID 37528). A final exact-process audit found no After Effects, AfterFX, aerender, or attempt-owned Adobe crash helper. No broad kill or retry was used.

The installed ToonDilate binary remains `5bbe693106072ceff14a1c1ae5a0d64815cddde58356c57575d29e516479036e`, and the accepted identity manifest remains `ef7bf31f4f8907af8d047276296b16c4d918433a94173938ca98b2874c61c368`.

This failure record makes no host-frame or numerical claim, authorizes no retry, and keeps the formal release gate blocked.
