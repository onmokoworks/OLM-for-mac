depends: C28-kira-smart-r6

# F31: switch the Mac port to `ucrtmath` and make the F30 worker the default oracle

## Background (facts; read `orchestra/reports/F30-oracle-worker-ucrtmath.md`, especially `next`, and `F30-evidence/mac-call-sites.txt`)
- The F30 worker (`~/.cache/olm-emu/` INDEX entry from F30) is F29's SSE NaN fix plus UCRT-exact
  expf/atan2f/powf in FMA mode. Its import shim was validated with 12M calls and 0
  mismatches.
- Under F30, RadialBlur Smart goes 148 → 240 exact. Blur and DirectionalBlur get *worse*
  (281→277, 285→283), because the Mac port still calls Apple libm at those sites.
- F30 lists the call sites:
  - float exp:
    - `core/olmblur_worker_orchestration.cpp:92`
    - `core/olmblur_worker16_nonlegacy.cpp:113`
    - `core/olmblur_worker32_nonlegacy.cpp:88`
    - `core/olmblur_worker16_legacy.cpp:72`
    - `core/olmblur_worker8_legacy.cpp:54`
    - `core/dblur_gaussian.h:23,28`
    - `core/olmblur_worker32_legacy.cpp:51`
    - `mac/OLMBlur/OLMBlur.cpp:1317`
    - `mac/OLMRadialBlur/OLMRadialBlur.cpp:1546,2224`
  - float pow:
    - `mac/OLMBlur/OLMBlur.cpp:1336`
    - `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:1184,1187`
    - the Blur decay, KiraKira seed/fade, and ColorKey conversion float `std::pow` sites
  - atan2f:
    - `mac/OLMColorKey/OLMColorKey.cpp:927`
    - `mac/OLMRadialBlur/OLMRadialBlur.cpp:193`

## Goal
1. Link `ucrtmath/` into the Mac plugin builds: Xcode/CMake/whatever builds `mac/`, plus the
   fuzz/regression harness builds.
2. Replace the float-import call sites with `ucrt_expf`, `ucrt_powf`, `ucrt_atan2f` in FMA
   mode.
   - Match by the **original AEX import boundary**: at every site the original calls the
     float import, so the Mac code must call the float function. Where Mac code currently
     evaluates in double and casts, use the float import.
   - Leave genuine double math (double sin/cos/exp/pow/atan2) as it is. It is not covered yet.
3. Switch the fuzzer default worker to F30, in `tools/fuzz/` config or adapters. Keep the old
   default selectable.
4. Re-measure seed 1 n300 Smart for all plugins plus one fresh seed each, and replay every
   corpus under F30.
5. Rebaseline the corpora with `tools/fuzz/rebaseline_corpus.py`, but only for saved cases whose
   reference changed for a demonstrated NaN/UCRT reason. List each one.

## Acceptance (strict)
- Measured under F30, no case may go exact → non-exact, compared with the F30 report's numbers
  (before the port change).
- Admitted outputs must be exact. Mismatch → refusal is allowed.
- Report before/after E/M/R/U per plugin.
- Run the existing unit tests for the touched plugins. `OLM_TEST_JOBS=1` is preset.

## Rules
- Use 1-2 processes. Do not change the release gate/ledger.
- `ucrtmath/` stays independent: the plugins include its header, never the reverse.
- If a site turns out not to be a float import boundary, leave it and list it.
