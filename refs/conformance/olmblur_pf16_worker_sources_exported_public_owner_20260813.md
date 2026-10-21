# OLMBlur PF16 retained worker sources: exported public owner

Status: **PASS_ACTUAL_EXPORTED_SMART_OWNER_PF16_WORKER_SOURCES_2_RAW_EXACT**

The exact 12x12/Amount3 and 18x18/Amount11 PF16 sources, both Repeat 1,
Bias 1 and NonLegacy, traverse the Windows exported SmartPreRender and
SmartRender entry points.  Both active outputs equal their fresh actual-worker
oracles and all 13 padding bytes per row remain untouched.

Actual Windows 2025 AEX exported SmartPreRender/SmartRender under the repository AexLoader/Unicorn. Each row uses the exact retained PF16 worker source and a fresh same-source internal-worker oracle. This is hostless public-owner evidence, not native AE or arbitrary-source evidence.
