#include <cstdio>
#include <cstring>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#include "../../mac/OLMColorKey/OLMColorKey.cpp"

enum Mode {
	MODE_OK,
	MODE_ACQUIRE_ERROR,
	MODE_SUCCESS_NULL,
	MODE_FUNCTION_NULL,
	MODE_CALLBACK_ERROR,
	MODE_RELEASE_ERROR,
};

static Mode g_mode = MODE_OK;
static int g_acquire = 0;
static int g_release = 0;
static int g_world_calls = 0;
static int g_color_calls = 0;
static PF_WorldSuite2 g_world_suite = {};
static PF_ColorParamSuite1 g_color_suite = {};
static int g_param_checkouts = 0;
static int g_param_checkins = 0;
static int g_fail_checkout = 0;
static int g_fail_checkin = 0;

static PF_Err GetFormat(const PF_EffectWorld *, PF_PixelFormat *format)
{
	++g_world_calls;
	if (g_mode == MODE_CALLBACK_ERROR) return 73;
	*format = PF_PixelFormat_ARGB32;
	return PF_Err_NONE;
}

static PF_Err GetParamColor(PF_ProgPtr, const PF_ParamDef *param, PF_PixelFloat *output)
{
	++g_color_calls;
	if (g_mode == MODE_CALLBACK_ERROR) return 74;
	output->alpha = param->u.cd.value.alpha / 255.0f;
	output->red = param->u.cd.value.red / 255.0f;
	output->green = param->u.cd.value.green / 255.0f;
	output->blue = param->u.cd.value.blue / 255.0f;
	return PF_Err_NONE;
}

static SPErr Acquire(const char *name, int32 version, const void **suite)
{
	++g_acquire;
	if (g_mode == MODE_ACQUIRE_ERROR) return 71;
	if (!suite) return kSPBadParameterError;
	if (g_mode == MODE_SUCCESS_NULL) {
		*suite = NULL;
		return kSPNoError;
	}
	if (!std::strcmp(name, kPFWorldSuite) && version == kPFWorldSuiteVersion2) {
		g_world_suite.PF_GetPixelFormat =
		    g_mode == MODE_FUNCTION_NULL ? NULL : GetFormat;
		*suite = &g_world_suite;
		return kSPNoError;
	}
	if (!std::strcmp(name, kPFColorParamSuite) &&
	    version == kPFColorParamSuiteVersion1) {
		g_color_suite.PF_GetFloatingPointColorFromColorDef =
		    g_mode == MODE_FUNCTION_NULL ? NULL : GetParamColor;
		*suite = &g_color_suite;
		return kSPNoError;
	}
	return kSPBadParameterError;
}

static SPErr Release(const char *, int32)
{
	++g_release;
	return g_mode == MODE_RELEASE_ERROR ? 72 : kSPNoError;
}

static void Reset(Mode mode)
{
	g_mode = mode;
	g_acquire = g_release = g_world_calls = g_color_calls = 0;
	g_param_checkouts = g_param_checkins = 0;
	g_fail_checkout = g_fail_checkin = 0;
}

static bool WorldCase(Mode mode, PF_Err expected, int releases, int calls)
{
	Reset(mode);
	SPBasicSuite basic = {};
	basic.AcquireSuite = Acquire;
	basic.ReleaseSuite = Release;
	PF_InData in_data = {};
	in_data.pica_basicP = &basic;
	PF_EffectWorld input = {};
	PF_EffectWorld output = {};
	short depth = 0;
	const PF_Err err = GetWorldDepths(&in_data, &input, &output, &depth);
	const bool pass = err == expected && g_acquire == 1 &&
	                  g_release == releases && g_world_calls == calls &&
	                  (mode != MODE_OK || depth == 8);
	std::printf("WORLD mode=%d pass=%d err=%d acquire=%d calls=%d release=%d\n",
	            mode, pass, (int)err, g_acquire, g_world_calls, g_release);
	return pass;
}

static void FillParams(PF_ParamDef defs[OLMCOLORKEY_NUM_PARAMS],
	                   PF_ParamDef *params[OLMCOLORKEY_NUM_PARAMS])
{
	for (int i = 0; i < OLMCOLORKEY_NUM_PARAMS; ++i) params[i] = &defs[i];
	defs[OLMCOLORKEY_COLOR_SPACE].u.pd.value = 1;
	defs[OLMCOLORKEY_FORCE_LOWER_PRECISION].u.pd.value = 1;
	defs[OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE].u.pd.value = 2;
	defs[OLMCOLORKEY_EDGE_BLUR_AMOUNT].u.fs_d.value = 1.0;
	defs[OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE].u.pd.value = 1;
	defs[OLMCOLORKEY_EDGE_BLUR_DIRECTION].u.pd.value = 1;
	defs[OLMCOLORKEY_NUMBER_OF_COLORS].u.sd.value = 2;
	defs[ColorParamIndex(0, COLOR_OFFSET_USE_COLOR)].u.bd.value = TRUE;
	defs[ColorParamIndex(1, COLOR_OFFSET_USE_COLOR)].u.bd.value = TRUE;
	defs[ColorParamIndex(0, COLOR_OFFSET_COLOR)].u.cd.value = {255, 0, 0, 0};
	defs[ColorParamIndex(1, COLOR_OFFSET_COLOR)].u.cd.value = {255, 0, 255, 0};
}

static void FillOneParam(A_long index, PF_ParamDef *param)
{
	std::memset(param, 0, sizeof(*param));
	if (index == OLMCOLORKEY_COLOR_SPACE ||
	    index == OLMCOLORKEY_FORCE_LOWER_PRECISION)
		param->u.pd.value = 1;
	else if (index == OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE)
		param->u.pd.value = 2;
	else if (index == OLMCOLORKEY_EDGE_BLUR_AMOUNT)
		param->u.fs_d.value = 1.0;
	else if (index == OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE ||
	         index == OLMCOLORKEY_EDGE_BLUR_DIRECTION)
		param->u.pd.value = 1;
	else if (index == OLMCOLORKEY_NUMBER_OF_COLORS)
		param->u.sd.value = 2;
	else if (index == ColorParamIndex(0, COLOR_OFFSET_USE_COLOR) ||
	         index == ColorParamIndex(1, COLOR_OFFSET_USE_COLOR))
		param->u.bd.value = TRUE;
	else if (index == ColorParamIndex(0, COLOR_OFFSET_COLOR))
		param->u.cd.value = {255, 0, 0, 0};
	else if (index == ColorParamIndex(1, COLOR_OFFSET_COLOR))
		param->u.cd.value = {255, 0, 255, 0};
}

static PF_Err CheckoutParam(PF_ProgPtr, PF_ParamIndex index,
	                        A_long, A_long, A_u_long, PF_ParamDef *param)
{
	++g_param_checkouts;
	if (g_fail_checkout == g_param_checkouts) return 81;
	FillOneParam(index, param);
	return PF_Err_NONE;
}

static PF_Err CheckinParam(PF_ProgPtr, PF_ParamDef *)
{
	++g_param_checkins;
	return g_fail_checkin == g_param_checkins ? 82 : PF_Err_NONE;
}

static bool ParamCase(int fail_checkout, int fail_checkin,
	                  PF_Err expected, int expected_checkouts,
	                  int expected_checkins)
{
	Reset(MODE_OK);
	g_fail_checkout = fail_checkout;
	g_fail_checkin = fail_checkin;
	SPBasicSuite basic = {};
	basic.AcquireSuite = Acquire;
	basic.ReleaseSuite = Release;
	PF_InData in_data = {};
	in_data.pica_basicP = &basic;
	in_data.inter.checkout_param = CheckoutParam;
	in_data.inter.checkin_param = CheckinParam;
	OLMColorKeyInfo info = {};
	const PF_Err err = CheckoutSmartInfo(&in_data, &info);
	const bool pass = err == expected &&
	                  g_param_checkouts == expected_checkouts &&
	                  g_param_checkins == expected_checkins &&
	                  g_acquire == 1 && g_release == 1;
	std::printf("PARAM checkout_fail=%d checkin_fail=%d pass=%d err=%d checkouts=%d checkins=%d\n",
	            fail_checkout, fail_checkin, pass, (int)err,
	            g_param_checkouts, g_param_checkins);
	return pass;
}

static bool ColorCase(Mode mode, PF_Err expected, int releases, int calls)
{
	Reset(mode);
	SPBasicSuite basic = {};
	basic.AcquireSuite = Acquire;
	basic.ReleaseSuite = Release;
	PF_InData in_data = {};
	in_data.pica_basicP = &basic;
	PF_ParamDef defs[OLMCOLORKEY_NUM_PARAMS] = {};
	PF_ParamDef *params[OLMCOLORKEY_NUM_PARAMS] = {};
	FillParams(defs, params);
	OLMColorKeyInfo info = {};
	const PF_Err err = CheckoutInfo(&in_data, params, &info);
	const bool pass = err == expected && g_acquire == 1 &&
	                  g_release == releases && g_color_calls == calls;
	std::printf("COLOR mode=%d pass=%d err=%d acquire=%d calls=%d release=%d\n",
	            mode, pass, (int)err, g_acquire, g_color_calls, g_release);
	return pass;
}

int main()
{
	bool pass = true;
	pass &= WorldCase(MODE_OK, PF_Err_NONE, 1, 2);
	pass &= WorldCase(MODE_ACQUIRE_ERROR, 71, 0, 0);
	pass &= WorldCase(MODE_SUCCESS_NULL, PF_Err_BAD_CALLBACK_PARAM, 1, 0);
	pass &= WorldCase(MODE_FUNCTION_NULL, PF_Err_BAD_CALLBACK_PARAM, 1, 0);
	pass &= WorldCase(MODE_CALLBACK_ERROR, 73, 1, 1);
	pass &= WorldCase(MODE_RELEASE_ERROR, 72, 1, 2);
	pass &= ColorCase(MODE_OK, PF_Err_NONE, 1, 4);
	pass &= ColorCase(MODE_ACQUIRE_ERROR, 71, 0, 0);
	pass &= ColorCase(MODE_SUCCESS_NULL, PF_Err_BAD_CALLBACK_PARAM, 1, 0);
	pass &= ColorCase(MODE_FUNCTION_NULL, PF_Err_BAD_CALLBACK_PARAM, 1, 0);
	pass &= ColorCase(MODE_CALLBACK_ERROR, 74, 1, 1);
	pass &= ColorCase(MODE_RELEASE_ERROR, 72, 1, 4);
	pass &= ParamCase(0, 0, PF_Err_NONE, 33, 33);
	for (int ordinal = 1; ordinal <= 33; ++ordinal) {
		pass &= ParamCase(ordinal, 0, 81, ordinal, ordinal - 1);
		pass &= ParamCase(0, ordinal, 82, ordinal, ordinal);
	}
	std::printf("COLORKEY_REAL_SDK_SUITE_LIFECYCLE_EXACT=%d\n", pass);
	return pass ? 0 : 3;
}
