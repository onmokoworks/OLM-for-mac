# OLMDistanceGradation actual-AEX powf XMM closure

Eight exported Smart PF32 Power cells execute 992 `powf` calls. Every actual XMM0/XMM1/result triple is an in-order production call; no extra pair exists. Production's seven additional unique pairs occur only in 63 transparent skipped pixels per cell. Replacing every production-only result with zero or one leaves all eight final RAW hashes exact. Native Windows UCRT return words and the eight final native-derived RAW comparisons remain required; no production admission or AE claim is made.
