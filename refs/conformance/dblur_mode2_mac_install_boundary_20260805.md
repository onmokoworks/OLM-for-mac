# OLMDirectionalBlur mode-2 Mac install boundary

- The new arm64 bundle is installed and ad-hoc signature verification passes.
- Installed Mach-O SHA-256: `61dca846...5206d`.
- The previous installed bundle is recoverable under
  `handoff/mac_plugin_backups/mediacore_20260805_directionalblur_before_mode2/`;
  its Mach-O SHA-256 is `9fbe1461...7b0a58`.
- After Effects 26.3 PID `77384` was already running. `lsof` resolves its
  mapped Mach-O vnode to the renamed old bundle, proving that the current AE
  process still executes `9fbe1461...7b0a58` and not the new installation.
- No render from that live process may be attributed to the new implementation.
  Restart AE, bind the new process to the installed bundle/hash, then run the
  Software 8bpc cases.
