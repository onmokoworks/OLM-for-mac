# OLMBlur classic current install / AE smoke

The frozen source `21f3c96a…8c89` built as an ad-hoc-signed Universal
x86_64+arm64 plugin and was installed as the only `OLMBlur.plugin`. The binary
SHA-256 is `b1461f8e…943f`; the previous `272b764a…5d22` bundle is recoverable
at `handoffs/olmblur_classic_current_install_20260812/previous_build.plugin`.
The current bundle and build transcript are durable siblings under the
hash-bound manifest `48907c06…666`. Source and binary are recorded together;
this is not a reproducible-build claim.

A fresh AE 26.3x87 process (PID 8082) had no OLMBlur mapping before effect add.
After adding `OLM OLM Blur`, the process mapped exactly the installed path and
completed control/effect-on PF32, SOFTWARE, 64×36 renders with all five default
parameters unchanged. AE was then stopped.

This promotes install identity and load/add/default-render only. It does not
prove live classic PF8/PF16 pixels or that AE routed PF32 through classic
`PF_Cmd_RENDER`. The bounded pixel claim remains in the separate classic public
entry closure. The persisted raw retains all observations; only inherited
ColorKey-template claim labels were sanitized by the checked-in deterministic
sanitizer. The original raw and exact observation runner are also preserved and
bound. The dedicated runner is a replay runner, not the observation producer.
