# OLMBlur PF16 retained worker sources: Mac public admission

Status: **PASS_PF16_8_WINDOWS_EXPORTED_TO_MAC_PUBLIC_RAW_EXACT_AND_494_FAIL_CLOSED**

- Positive controls: 16
- Fail-closed controls: 494
- 12x12 Repeat1 output: `f4a8b917c50936578f0573b943e5d9baad29af87b8f17f2efec4765c74771922`
- 12x12 Repeat2 output: `28d648118306c3ed9bedbcd7e99c7af8f8bc26813b701b366c56b966f3a3e846`
- 18x18 Repeat1 output: `fbf43a4c4832c1c2a8e30187361ddaec6bf95c36a793f71573d8b1db4652a46e`
- 18x18 Repeat3 output: `64355b2ce493e3d318de8fa09f45234b98236029347b62e9d09e4ef8cb98a4bc`
- 12x12 Legacy Repeat2 output: `6119d2c5760e5f5234b9c53c990dad3a529777124bdbab794dc46bd562c1e9c0`
- 18x18 Legacy Repeat3 output: `b47c25529ac36c0c7af7fb43659d67a5e7d3a4d77172706813dad47e1a700d26`
- 18x12 Legacy mixed-alpha output: `28b16efe8ef4535661f1f514ff69195e944d1c071d78df1e8f5a8034cbcdc346`
- 20x16 Legacy Smoothness62.5 public output: `2e97a898b15328c6fb11876f88951c9b1a593a66eb23bcbe89b94784c477ca1b`

For exactly eight source-bound PF16 cells, current Mac public SmartRender is raw exact to the same-source Windows exported owner. The Smoothness62.5 cell reproduces the owner's signed integer-part materialization while retaining the full fixed value in its exact predicate. Sixteen optional-checkin success controls and 494 bounded one-away/lifecycle controls preserve complete input and commit no failure output.
