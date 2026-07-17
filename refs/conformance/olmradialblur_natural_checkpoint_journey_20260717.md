# OLMRadialBlur natural checkpoint journey

- Status: `pass_local_causal_natural_checkpoint_journey`
- Every child embeds and matches the complete SHA/RIP/instruction ancestry of the supplied parent sequence.
- No direct-core entry, Python/synthetic prefill, or worker detour was used.

| Label | RIP | cumulative instructions | checkpoint SHA-256 |
| --- | --- | ---: | --- |
| `staging` | `0x180007811` | `908` | `bcafa4313a809f8bd1ad7acc76b728f772bea93707a77bed8c39d5b64b1f7c91` |
| `core` | `0x1800056f0` | `340360724` | `4b5af5087e656441cfba2c81589a2e91c7ec3ecd640e889c4cb9079b7a796dec` |
| `prefill_start` | `0x180005a00` | `340385693` | `27b907b4e12ed463cfb71f4dabb3bdd2714da0d7934672f721ec2d3d2ec1f523` |
| `prefill_end` | `0x180005ba2` | `954651817` | `de1fac456754d1f3a6cbdd1abf2762cbcd936c45e63e59831e18d24d9b3e86bd` |

Boundary: fresh-process actual-AEX checkpoint ancestry and reached RIPs only; modeled loader state, no Windows or AE-exact claim.
