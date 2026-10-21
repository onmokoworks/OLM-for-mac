# DirectionalBlur remaining-six UCRT powf call census

Status: `PASS_ACTUAL_EXPORTED_SMART_SIX_POWF_KEYS_CENSUSED_AE_FREE`.

The six pinned exported-Smart cells make 47,514 `powf` calls spanning 787 exact float32 input/exponent keys in addition to their Gaussian `expf` calls. All six host-substituted control outputs retain their pinned raw hashes, but those result words are not native Windows UCRT evidence. Only the call keys are promoted into the AE-free native request. Therefore the earlier 557-row batch is incomplete and must not be sent. AE and network state were unchanged.
