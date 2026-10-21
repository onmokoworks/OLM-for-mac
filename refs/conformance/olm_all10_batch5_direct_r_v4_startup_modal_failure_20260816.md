# Batch5 direct `-r` v4 startup boundary

Status: `fail_closed_no_retry`.

The versioned v4 runner bypassed AppleScript `DoScriptFile` and launched the
exact AE executable once with `-r <nonce-bound launch.jsx>`. No nonce-bound
return, PNG, or plug-in row was produced.

The preserved macOS incident report places AE's main thread in a modal message
box reached from `CEggApp::BirthPrefs`, before the payload could establish any
runtime attribution. The recorded `SIGABRT` occurred during exact-owned-process
cleanup after the bounded observation window; it is not classified as an OLM
plug-in crash. The accepted installed identity remains unchanged and all ten
installed entries revalidate after cleanup.

The unified macOS log records a `DVAMacDialog` at 01:18:45.934 JST, during
preference initialization. AE itself passes root and deep strict code-sign
verification and Gatekeeper assessment as a notarized Adobe Developer ID app;
the bundled Expressions/Scripting plug-in is also Universal and strict-valid.
This rules out damaged AE or OLM signatures as the explanation for the dialog.

There will be no automatic retry. The remaining step is host maintenance:
explicitly clear or answer AE's startup preference/recovery dialog, then use a
new versioned one-shot receipt for the next batched smoke.
