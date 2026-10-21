# OLMBlur classic public-entry closure

The retained 2025 export routes selector `0x0b` to `FUN_18000a180`. On the registered default tuple (Amount 5, Smoothness 100, Repeat 2), PF8 and PF16 are copy-only exact at padded 24x24. Bias 2 and Legacy 1 are counterexamples to the former Mac contract: the owner never reads either slot, so all four Bias/Legacy combinations have identical output. Production now admits only this bounded PF8/PF16 tuple, copies the world, and leaves numerical rendering on Smart Render.

PF32 is fail-closed in classic Render. The actual owner tests only `PF_WorldFlag_DEEP`; AEXCompat sets that flag for both PF16 and PF32, so the classic export cannot identify a float owner and aliases its PF16 branch. Non-default Amount/Smoothness/Repeat values are also rejected rather than generalizing the malformed classic float-slider read. Input, parameter definitions, world headers, row padding, and guards are bound in the JSON.

Evidence boundary: the actual classic export uses the repository Unicorn loader. The pinned AEXCompat worker executes setup/default discovery; pixel.rs/classic.rs are identity-bound source context only because the worker automatically chooses Smart for pixels. Worker classic pixels and native AE classic routing are not executed here.
