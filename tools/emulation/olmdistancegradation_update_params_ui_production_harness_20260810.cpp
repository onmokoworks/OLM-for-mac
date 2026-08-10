#include <cstdio>
#include <cstring>

#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"

static PF_ParamDef values[DG_NUM_PARAMS];
static int update_count;
static int update_indices[6];
static A_u_long update_flags[6];

static PF_Err checkout_param(PF_ProgPtr, PF_ParamIndex index, A_long, A_long,
                             A_u_long, PF_ParamDef *out)
{
	*out = values[index];
	return PF_Err_NONE;
}

static PF_Err checkin_param(PF_ProgPtr, PF_ParamDef *) { return PF_Err_NONE; }

static PF_Err update_param(PF_ProgPtr, PF_ParamIndex index, const PF_ParamDef *def)
{
	if (update_count >= 6) return PF_Err_BAD_CALLBACK_PARAM;
	update_indices[update_count] = index;
	update_flags[update_count] = def->ui_flags;
	++update_count;
	return PF_Err_NONE;
}

static PF_ParamUtilsSuite3 param_utils = { update_param };

static SPErr acquire_suite(const char *name, int32 version, const void **suite)
{
	if (std::strcmp(name, kPFParamUtilsSuite) || version != kPFParamUtilsSuiteVersion3) return 1;
	*suite = &param_utils;
	return 0;
}

static SPErr release_suite(const char *, int32) { return 0; }

int main(int argc, char **argv)
{
	if (argc != 6) return 2;
	std::memset(values, 0, sizeof(values));
	values[DG_INTERP_MODE].u.pd.value = std::atoi(argv[1]);
	values[DG_IN_OUT].u.pd.value = std::atoi(argv[2]);
	values[DG_RENDER_MODE].u.pd.value = std::atoi(argv[3]);
	values[DG_USE_BG_COLOR].u.bd.value = std::atoi(argv[4]) != 0;
	values[DG_BLUR_MODE].u.pd.value = std::atoi(argv[5]);
	for (int i = 0; i < DG_NUM_PARAMS; ++i) values[i].ui_flags = 0xa5;

	SPBasicSuite basic{};
	basic.AcquireSuite = acquire_suite;
	basic.ReleaseSuite = release_suite;
	PF_InData in_data{};
	PF_OutData out_data{};
	in_data.effect_ref = reinterpret_cast<PF_ProgPtr>(0x1234);
	in_data.pica_basicP = &basic;
	in_data.inter.checkout_param = checkout_param;
	in_data.inter.checkin_param = checkin_param;

	const PF_Err err = EffectMain(PF_Cmd_UPDATE_PARAMS_UI, &in_data, &out_data,
	                              nullptr, nullptr, nullptr);
	if (err || update_count != 6) return 3;
	for (int i = 0; i < update_count; ++i) {
		if (i) std::putchar(',');
		std::printf("%d:%u", update_indices[i], (unsigned)update_flags[i]);
	}
	std::putchar('\n');
	return 0;
}
