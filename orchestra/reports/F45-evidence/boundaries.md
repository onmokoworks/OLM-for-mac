# F45 double-import boundaries

Facts:
- F43c's report is `status: blocked` (a closeout tool rejection, not a numerical failure). F45 obeys the ticket fallback: double pow stays host in worker and Mac.
- MAIN read-only decomp `OLMColorKey.aex.c.txt` lines 1464/1588, 1647/1771, 1830/1954 call double sin after float product promotion. Four shared typed Mac `phase` call sites now call `ucrt_sin(..., UCRT_FMA)`, preserving promotion and the cast after +1. Remaining `std::sin` expressions use float arguments; they are outside this double ticket.
- `OLMKiraKira.aex.c.txt` FUN_1812943d0, lines 3773479/3773481 calls double cos/sin to construct the rotation matrix. `core/kirakira_warp.h` now uses double UCRT at this boundary. Embedded float extent_sincos remains unchanged.
- `OLMRadialBlur.aex.c.txt` lines 1987/1989 and 2416/2418 call double cos/sin before float narrowing. Mac coordinate paths now use UCRT double, preserving their existing casts and angle arithmetic. The Mac FFT implementation's twiddle math is an implementation-specific helper, not this original import boundary, and remains host.
- DistanceGradation's Mac Gaussian `std::exp` was inspected but not switched. The Smart kernel identifies FUN_181285230; decomp lines 3758387 onward call internal FUN_1813a0870 on softdouble storage, not imported exp. The legacy kernel also has no demonstrated imported-exp boundary in this audit; its host exp remains unchanged pending separate evidence. Imported exp in decomp appears in separate bilateral code (e.g. lines 3825300/3825330/3825578/3825604/3826405); the current port's corresponding IPP helpers already implement separate embedded arithmetic. No blanket replacement is justified.
- DistanceGradation's decomp double sin/cos pair at 3789032/3789033 is in linked OpenCV code; no matching host trig call exists in its current Mac/core implementation. KiraKira Gaussian exp helpers likewise are not exp imports (KiraKira's import set has no exp).
- OLMBlur/Smoother2 double pow calls remain host. DirectionalBlur double trig used for host ROI/scale calculations is outside the declared double-import users; no change.
- F44 legacy import dispatch contains double sin/cos but no double exp variant. F45 adds exp and routes all three names for api-ms-win-crt-math-l1-1-0.dll and ucrtbase.dll, plus native Win64 export dispatch. ANSI suite callbacks are separate host APIs and remain unchanged.

Inference:
- Restricting changes to imported math avoids substituting UCRT into embedded OpenCV/IPP algorithms. This is boundary integration, not a claim that those remaining algorithms are universally exact.
