# OLMKiraKira ramp arbitrary registration ABI

Status: **registration arguments and callback ABI grounded**

The five actual-AEX rows use `PF_Param_ARBITRARY_DATA` at disk IDs
`19/21/23/36/25`. Their common registration arguments are UI size
`0x136 × 0xaa`, parameter flags OR `0x40`, UI flags OR `0x82`, and the
`RampDataHandler` at `effect+0x200`. The registered value handle starts null.

Before AddParam, virtual slot `+0x18` produces the recovered default. Exported
entrypoint probes cover selectors `0..10`, including ownership and canonical
flatten/unflatten behavior.

Mac registers all five arbitrary rows and exposes 41 parameters.
