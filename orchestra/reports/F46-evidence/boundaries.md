# F46 imported pow boundary audit

Facts:
- `static-pow.json` binds the original MAIN decomp files by SHA256 and records all named double pow calls and enclosing functions. `aex-double-imports.json` independently records the pinned PE import tables for all ten plugins.
- OLMBlur's six calls (decomp 1046/1094, 1635/1683, 2229/2278) promote the float repeat-decay and integer iteration, multiply the double result by blur amount, then narrow. The corresponding three core typed workers and Mac classic radius now use `ucrt_pow(..., UCRT_FMA)`, with those casts and subsequent operations preserved.
- Smoother2 calls double pow for sRGB decode (1163/1179/1194), encode (2238), LUT construction (6069/6129), and forward/inverse gamma (6500..6504, 7235..7248). Both maintained Mac sources' actual host pow calls are switched. Checked-in captured LUTs remain unchanged; their data are not calls and this ticket does not regenerate them.
- DistanceGradation has only three named double pow call sites outside the import thunk: 3540372/3540538/3540700, in typed Sphere interpolation. The Mac shared typed callback uses `ucrt_pow` after the existing float subtraction and double promotion. Power's separate powf path is unchanged.
- The remaining DistanceGradation Gaussian softdouble, embedded OpenCV/IPP helpers, and other plugin math remain unchanged. No named pow call was found in the embedded Gaussian kernel. The import table alone was not used as permission for blanket replacement.
- F45 already dispatches both CRT DLL names' pow to the same legacy binary hook and exposes native_pow. F46 replaces only that hook function and native callback arithmetic, adds the pow C object/FFI, and extends the diagnostic producer. FMA selection uses the unchanged F45 mode function (default 1).

Inference:
- These call-site correspondences justify an import-boundary change, not a replacement of embedded math or a general AE-exact claim. Finite replay results qualify only the measured cases.
