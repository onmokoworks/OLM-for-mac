# Windows SSH / AE interactive broker audit (2026-07-13)

## FACT

- Mac-to-Windows SSH, Windows Codex CLI, request transfer, hash checks, runner
  invocation, fail-closed classification, and return ZIP creation all work.
- Processes launched directly by Windows Codex over OpenSSH run in Windows
  session `0`; the logged-in desktop and Explorer run in session `1`.
- Direct SSH runs of After Effects/CDB therefore produced no JSX marker or
  plug-in load. The retained returns are `exact_bind_failure`, not evidence:
  - DirectionalBlur: `ae_pause`, ready marker absent.
  - Smoother2: `bind`, module/config/writer markers absent.
- A Task Scheduler probe using `LogonType Interactive` wrote session id `1`,
  proving that an interactive-token broker can reach the desktop session.
- A minimal After Effects JSX marker still did not execute through that broker.
  `AfterFX.com` reported `GPU3 failed (previous) sanity test`; the Windows
  Application log also recorded an Explorer/dcomp crash during the diagnostic.
  All diagnostic tasks and AfterFX/CDB processes were removed afterward.
- The retained retry return hashes are:
  - DirectionalBlur: `0f2799651d615e9b1795b93eab47dead802f0b66ff9903c2bff78405f5cf3c13`
  - Smoother2: `c6bd2e18157431312796cd9b67567bf20561daac62e745aa63beb94e1a012f77`

## Decision

- Use Windows Codex over SSH for binary inspection, package validation,
  non-GUI CDB work, file transfer, and fail-closed intake preparation.
- Do not treat SSH/session-0 After Effects execution as an AE validation path.
- Until a stable interactive broker is proven, launch AE-dependent runners from
  the already logged-in Windows desktop. The package itself remains the source
  of runner/contract truth; only the outer launch context changes.
- Do not repeat Task Scheduler GPU/desktop experiments unattended. The next
  automation attempt must first pass the one-line JSX marker without an
  Application-log crash, then the effect-load marker, before any trace request.

## INFERENCE

The current failures are launch-context failures, not evidence about either
image-processing algorithm. They do not reopen closed binary/CLI stages and do
not justify production tuning.
