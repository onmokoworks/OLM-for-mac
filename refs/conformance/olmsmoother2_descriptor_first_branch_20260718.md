# OLMSmoother2 descriptor first-branch audit - 2026-07-18

## Conclusion

The first source-level branch explaining the current Mac descriptor is the `scan_d3b0` left-column R stop at `(x=92,y=840)`. This is a branch classification, not an AE-exactness claim and not a source fix.

## FACT

- Windows accepted descriptor: `[92, 841, 1, 92, 842, 2]`.
- Mac trace descriptor: `[92, 840, 1, 92, 843, 2]`.
- `cardinal6` constructs the descriptor from `scan_d3b0` followed by `scan_da50`.
- Mac trace at `(92,841)` has class bytes `[A,R,G,B]=[255,0,0,255]`; at `(92,840)` the left-column bytes are `[255,255,0,255]`.
- In `scan_d3b0`, the left-column R stop is at source line `1380`; the preceding vertical step is line `1381`.

## INFERENCE

- On the Mac trace, the scan passes the predicates at `y=841`, decrements to `y=840`, then stops because `R@(x=92,y=840) != 0`; that yields the second descriptor field `840`.
- The Windows descriptor's `841` implies that this stop condition is not reached in the same way, or that the Windows class-plane byte at that coordinate differs. The current evidence does not distinguish those two possibilities.
- The second differing field `843` vs `842` comes from the independent `scan_da50` result and must be audited separately; it is not evidence that the first `scan_d3b0` branch is wrong.

## Next evidence

A Windows same-run class-plane witness for `(92,840)`, `(92,841)`, and the corresponding `x+1` column is required before changing the scanner or class-plane generation. PNG tuning and Mac source changes are forbidden for this audit.
