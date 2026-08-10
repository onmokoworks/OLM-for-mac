#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"

static int checkout_calls;
static PF_Err checkout_layer(PF_ProgPtr, A_long, PF_EffectWorld **) {
	++checkout_calls;
	return PF_Err_NONE;
}
static PF_Err checkout_output(PF_ProgPtr, PF_EffectWorld **) {
	++checkout_calls;
	return PF_Err_NONE;
}

int main()
{
	PF_InData in_data{};
	PF_OutData out_data{};
	PF_SmartRenderInput input{};
	PF_SmartRenderCallbacks callbacks{checkout_layer, checkout_output};
	PF_SmartRenderExtra extra{&input, &callbacks};
	input.bitdepth = 32;
	const PF_Err err = EffectMain(PF_Cmd_SMART_RENDER, &in_data, &out_data,
	                              nullptr, nullptr, &extra);
	if (err != PF_Err_BAD_CALLBACK_PARAM || checkout_calls != 0) return 1;
	std::puts("PASS PF32 Smart fail-closed before host checkout");
	return 0;
}
