# OLMRadialBlur tiny Rotation Patch Audit

Date: 2026-06-30

Witness:

- reference / candidate comparison around tiny Rotation `case_0010`
  max witness `(1614,6)`

Observed 9x5 patch summary:

- The local candidate does **not** merely miss a single isolated bright pixel.
- A small bright cluster in the Windows reference is absent in the candidate:
  - `(1612,4) ref=251 cand=0`
  - `(1613,4) ref=247 cand=0`
  - `(1614,4) ref=253 cand=0`
  - `(1613,5) ref=253 cand=0`
  - `(1614,5) ref=251 cand=0`
  - `(1614,6) ref=255 cand=0`
- Nearby dark and low-gray support pixels still match:
  - `(1610,4) ref=10 cand=10`
  - `(1611,5) ref=7 cand=7`
  - `(1612,6) ref=5 cand=5`
  - `(1613,6) ref=1 cand=1`
  - `(1613,7) ref=2 cand=2`

Interpretation:

- This looks less like a simple one-pixel output shift and more like a missing
  bright local lobe / contribution family.
- Combined with the local witness dump, where all four contributing polar cells
  at `(1614,6)` are already `valid=1` but have `[negative, zero, negative,
  zero]` RGB, the current best local reading is:
  - the candidate is not choosing a nearly-correct bright neighborhood and then
    misplacing it by one pixel
  - instead, the relevant bright polar contribution is already absent or
    numerically suppressed upstream of the final inverse-sampling step
