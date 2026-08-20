#include "OLMColorKey.h"
#include "AEFX_SuiteHandlerTemplate.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <exception>
#include <limits>
#include <new>
#include <vector>

#if !defined(AE_OS_WIN)
#include <cerrno>
#include <cstdint>
#include <dlfcn.h>
#include <fcntl.h>
#include <limits.h>
#include <unistd.h>
#endif

#if !defined(AE_OS_WIN)
static PF_Err
CapturePixelFloatEntryIfRequested(const PF_EffectWorld *input_world, short bitdepth)
{
	const char *enabled = std::getenv("OLM_PF_PIXELFLOAT_ENTRY_CAPTURE");
	if (!enabled || std::strcmp(enabled, "1") != 0) return PF_Err_NONE;

	const char *dump_path = std::getenv("OLM_PF_PIXELFLOAT_ENTRY_DUMP");
	const char *metadata_path = std::getenv("OLM_PF_PIXELFLOAT_ENTRY_METADATA");
	const char *nonce = std::getenv("OLM_PF_PIXELFLOAT_ENTRY_NONCE");
	const char *case_id = std::getenv("OLM_PF_PIXELFLOAT_ENTRY_CASE");
	const char *expected_plugin_sha256 = std::getenv("OLM_PF_PIXELFLOAT_ENTRY_EXPECTED_PLUGIN_SHA256");
	if (!input_world || !input_world->data || bitdepth != 32 ||
	    !dump_path || !*dump_path || !metadata_path || !*metadata_path ||
	    !nonce || std::strlen(nonce) < 32 ||
	    !case_id || std::strcmp(case_id, "olmcolorkey__case_0002") != 0 ||
	    !expected_plugin_sha256 || std::strlen(expected_plugin_sha256) != 64 ||
	    input_world->width <= 0 || input_world->height <= 0 ||
	    input_world->rowbytes < input_world->width * (A_long)sizeof(PF_PixelFloat) ||
	    sizeof(PF_PixelFloat) != 16) {
		return PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	const uint16_t endian_probe = 1;
	if (*reinterpret_cast<const uint8_t *>(&endian_probe) != 1) {
		return PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	for (size_t i = 0; i < 64; ++i) {
		if (!((expected_plugin_sha256[i] >= '0' && expected_plugin_sha256[i] <= '9') ||
		      (expected_plugin_sha256[i] >= 'a' && expected_plugin_sha256[i] <= 'f'))) {
			return PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}

	Dl_info image_info;
	char loaded_plugin_path[PATH_MAX];
	if (dladdr(reinterpret_cast<const void *>(&CapturePixelFloatEntryIfRequested), &image_info) == 0 ||
	    !image_info.dli_fname || !realpath(image_info.dli_fname, loaded_plugin_path) ||
	    std::strchr(loaded_plugin_path, '"') || std::strchr(loaded_plugin_path, '\\')) {
		return PF_Err_INTERNAL_STRUCT_DAMAGED;
	}

	char claim_path[4096];
	char dump_tmp[4096];
	char metadata_tmp[4096];
	const long pid = (long)getpid();
	if (std::snprintf(claim_path, sizeof(claim_path), "%s.claim", metadata_path) >= (int)sizeof(claim_path) ||
	    std::snprintf(dump_tmp, sizeof(dump_tmp), "%s.%ld.tmp", dump_path, pid) >= (int)sizeof(dump_tmp) ||
	    std::snprintf(metadata_tmp, sizeof(metadata_tmp), "%s.%ld.tmp", metadata_path, pid) >= (int)sizeof(metadata_tmp)) {
		return PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	const int claim_fd = open(claim_path, O_WRONLY | O_CREAT | O_EXCL, 0600);
	if (claim_fd < 0) return errno == EEXIST ? PF_Err_NONE : PF_Err_INTERNAL_STRUCT_DAMAGED;
	close(claim_fd);

	FILE *dump = std::fopen(dump_tmp, "wb");
	if (!dump) return PF_Err_INTERNAL_STRUCT_DAMAGED;
	bool ok = true;
	for (A_long y = 0; y < input_world->height && ok; ++y) {
		const char *row = reinterpret_cast<const char *>(input_world->data) +
		                  (size_t)y * (size_t)input_world->rowbytes;
		ok = std::fwrite(row, 1, (size_t)input_world->rowbytes, dump) == (size_t)input_world->rowbytes;
	}
	if (std::fflush(dump) != 0) ok = false;
	if (fsync(fileno(dump)) != 0) ok = false;
	if (std::fclose(dump) != 0) ok = false;
	if (!ok || std::rename(dump_tmp, dump_path) != 0) {
		std::remove(dump_tmp);
		return PF_Err_INTERNAL_STRUCT_DAMAGED;
	}

	FILE *metadata = std::fopen(metadata_tmp, "w");
	if (!metadata) return PF_Err_INTERNAL_STRUCT_DAMAGED;
	const unsigned long long byte_count =
	    (unsigned long long)(size_t)input_world->rowbytes * (unsigned long long)(size_t)input_world->height;
	std::fprintf(metadata,
		"{\n"
		"  \"kind\": \"olm_pf_pixel_float_entry_capture_provenance\",\n"
		"  \"schema\": 3,\n"
		"  \"producer\": \"OLMColorKey.plugin\",\n"
		"  \"capture_method\": \"macos-env-gated-plugin-instrumentation\",\n"
		"  \"capture_point\": \"SmartRender.after_checkout_layer_pixels.before_checkout_output\",\n"
		"  \"case\": \"olmcolorkey__case_0002\",\n"
		"  \"nonce\": \"%s\",\n"
		"  \"pid\": %ld,\n"
		"  \"loaded_plugin_executable\": \"%s\",\n"
		"  \"launch_expected_plugin_sha256\": \"%s\",\n"
		"  \"bitdepth\": %d,\n"
		"  \"pixel_type\": \"PF_PixelFloat\",\n"
		"  \"channel_order\": [\"alpha\", \"red\", \"green\", \"blue\"],\n"
		"  \"endianness\": \"little\",\n"
		"  \"pixel_stride_bytes\": %lu,\n"
		"  \"width\": %ld,\n"
		"  \"height\": %ld,\n"
		"  \"rowbytes\": %ld,\n"
		"  \"bytes\": %llu,\n"
		"  \"world_data_address\": \"%p\"\n"
		"}\n",
		nonce, pid, loaded_plugin_path, expected_plugin_sha256,
		(int)bitdepth, (unsigned long)sizeof(PF_PixelFloat),
		(long)input_world->width, (long)input_world->height, (long)input_world->rowbytes,
		byte_count, input_world->data);
	ok = std::fflush(metadata) == 0;
	if (fsync(fileno(metadata)) != 0) ok = false;
	if (std::fclose(metadata) != 0) ok = false;
	if (!ok || std::rename(metadata_tmp, metadata_path) != 0) {
		std::remove(metadata_tmp);
		return PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	return PF_Err_NONE;
}
#endif

static void UnionLRect(const PF_LRect *src, PF_LRect *dst)
{
	if (dst->left == dst->right || dst->top == dst->bottom) {
		*dst = *src;
	} else if (src->left != src->right && src->top != src->bottom) {
		if (src->left   < dst->left)   dst->left   = src->left;
		if (src->top    < dst->top)    dst->top    = src->top;
		if (src->right  > dst->right)  dst->right  = src->right;
		if (src->bottom > dst->bottom) dst->bottom = src->bottom;
	}
}

static PF_Err
About(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	suites.ANSICallbacksSuite1()->sprintf(out_data->return_msg,
		"%s v%d.%d.%d\r%s",
		GetStringPtr(StrID_Name),
		MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
		GetStringPtr(StrID_Description));
	return PF_Err_NONE;
}

static PF_Err
GlobalSetup(PF_InData *, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = 0x02000040;
#ifndef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	out_data->out_flags |= PF_OutFlag_SEND_UPDATE_PARAMS_UI;
#endif
	out_data->out_flags2 = PF_OutFlag2_SUPPORTS_SMART_RENDER |
	                      PF_OutFlag2_FLOAT_COLOR_AWARE |
	                      PF_OutFlag2_SUPPORTS_GET_FLATTENED_SEQUENCE_DATA;
	return PF_Err_NONE;
}

template <typename T>
static T ClampValue(T value, T lo, T hi)
{
	return std::max(lo, std::min(value, hi));
}

static void MakeIndexedName(char *dst, size_t dst_size, const char *base, int index)
{
	std::snprintf(dst, dst_size, "%s %d", base, index);
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_ColorKeep_Param_Name), "", FALSE, 0,
	                COLOR_KEEP_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Threshold_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
	                     THRESHOLD_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_ThresholdGroup_Param_Name),
	             THRESHOLD_GROUP_START_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_Premultiplied_Param_Name), "", FALSE, 0,
	                PREMULTIPLIED_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_ColorSpace_Param_Name),
	             6, 1, GetStringPtr(StrID_ColorSpace_Choices),
	             COLOR_SPACE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_ForceLowerPrecision_Param_Name),
	             3, 1, GetStringPtr(StrID_ForceLowerPrecision_Choices),
	             FORCE_LOWER_PRECISION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_PerColor_Param_Name), "", FALSE, 0,
	                PER_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_PerComponent_Param_Name), "", FALSE, 0,
	                PER_COMPONENT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_ThresholdR_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
	                     THRESHOLD_R_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_ThresholdG_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
	                     THRESHOLD_G_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_ThresholdB_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
	                     THRESHOLD_B_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(THRESHOLD_GROUP_END_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_EdgeThinGroup_Param_Name),
	             EDGE_THIN_GROUP_START_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Amount_Param_Name),
	              -4000, 4000, -100, 100, 0,
	              EDGE_THIN_AMOUNT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_DistanceType_Param_Name),
	             3, 1, GetStringPtr(StrID_DistanceType_Choices),
	             EDGE_THIN_DISTANCE_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(EDGE_THIN_GROUP_END_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_EdgeBlurGroup_Param_Name),
	             EDGE_BLUR_GROUP_START_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Amount_Param_Name),
	                     0.0, 4000.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     EDGE_BLUR_AMOUNT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_DistanceType_Param_Name),
	             3, 1, GetStringPtr(StrID_DistanceType_Choices),
	             EDGE_BLUR_DISTANCE_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_EdgeBlurDirection_Param_Name),
	             3, 2, GetStringPtr(StrID_EdgeBlurDirection_Choices),
	             EDGE_BLUR_DIRECTION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(EDGE_BLUR_GROUP_END_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = PF_ParamFlag_SUPERVISE;
	PF_ADD_SLIDER(GetStringPtr(StrID_NumberOfColors_Param_Name),
	              0, OLMCOLORKEY_MAX_COLORS, 0, 30, 1,
	              NUMBER_OF_COLORS_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_EnableReplace_Param_Name), "", FALSE, PF_ParamFlag_SUPERVISE,
	                ENABLE_REPLACE_DISK_ID);

	for (int i = 0; i < OLMCOLORKEY_MAX_COLORS; ++i) {
		char name[128];
		int display_index = i + 1;

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_UseColor_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_CHECKBOX(name, "", FALSE, 0,
		                USE_COLOR_DISK_ID_FIRST + i * 3);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_UseReplaceColor_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_CHECKBOX(name, "", FALSE, 0,
		                USE_REPLACE_DISK_ID_FIRST + i * 3);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_Color_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		def.flags = PF_ParamFlag_COLLAPSE_TWIRLY;
		PF_ADD_COLOR(name, 0, 0, 0, COLOR_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ReplaceColor_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		def.flags = PF_ParamFlag_COLLAPSE_TWIRLY;
		PF_ADD_COLOR(name, 0, 0, 0, REPLACE_COLOR_DISK_ID_FIRST + i * 3);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ThresholdIndexed_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_FLOAT_SLIDERX(name, 0.0, 1.0, 0.0, 1.0, 0.0,
		                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
		                     THRESHOLD_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ThresholdR_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_FLOAT_SLIDERX(name, 0.0, 1.0, 0.0, 1.0, 0.0,
		                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
		                     THRESHOLD_R_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ThresholdG_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_FLOAT_SLIDERX(name, 0.0, 1.0, 0.0, 1.0, 0.0,
		                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
		                     THRESHOLD_G_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ThresholdB_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_FLOAT_SLIDERX(name, 0.0, 1.0, 0.0, 1.0, 0.0,
		                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
		                     THRESHOLD_B_DISK_ID_FIRST + i * 5);
	}

	out_data->num_params = OLMCOLORKEY_NUM_PARAMS;
	return err;
}

#ifndef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
static PF_Err
UpdateParameterUI(PF_InData *in_data, PF_ParamDef *params[])
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	PF_ParamUtilsSuite3 *param_utils = suites.ParamUtilsSuite3();

	auto set_enabled = [&](A_long index, bool enabled) {
		if (err != PF_Err_NONE) return;
		PF_ParamDef copy = *params[index];
		if (enabled)
			copy.ui_flags &= ~PF_PUI_DISABLED;
		else
			copy.ui_flags |= PF_PUI_DISABLED;
		err = param_utils->PF_UpdateParamUI(in_data->effect_ref, index, &copy);
	};

	const bool per_color = params[OLMCOLORKEY_PER_COLOR]->u.bd.value != FALSE;
	const bool per_component = params[OLMCOLORKEY_PER_COMPONENT]->u.bd.value != FALSE;
	const bool replace_enabled = params[OLMCOLORKEY_ENABLE_REPLACE]->u.bd.value != FALSE;
	const A_long color_count = ClampValue<A_long>(
		params[OLMCOLORKEY_NUMBER_OF_COLORS]->u.sd.value, 0, OLMCOLORKEY_MAX_COLORS);

	set_enabled(OLMCOLORKEY_THRESHOLD, !per_color && !per_component);
	set_enabled(OLMCOLORKEY_THRESHOLD_R, per_component && !per_color);
	set_enabled(OLMCOLORKEY_THRESHOLD_G, per_component && !per_color);
	set_enabled(OLMCOLORKEY_THRESHOLD_B, per_component && !per_color);

	for (int i = 0; i < OLMCOLORKEY_MAX_COLORS; ++i) {
		const bool active = i < color_count;
		const A_long first = OLMCOLORKEY_COLOR_FIRST + i * COLOR_PARAM_STRIDE;
		const bool use_color = params[first + COLOR_OFFSET_USE_COLOR]->u.bd.value != FALSE;
		const bool use_replace = params[first + COLOR_OFFSET_USE_REPLACE]->u.bd.value != FALSE;

		set_enabled(first + COLOR_OFFSET_USE_COLOR, active);
		set_enabled(first + COLOR_OFFSET_USE_REPLACE,
		            active && use_color && replace_enabled);
		set_enabled(first + COLOR_OFFSET_COLOR, active && use_color);
		set_enabled(first + COLOR_OFFSET_REPLACE_COLOR,
		            active && use_color && replace_enabled && use_replace);
		set_enabled(first + COLOR_OFFSET_THRESHOLD,
		            active && per_color && !per_component);
		set_enabled(first + COLOR_OFFSET_THRESHOLD_R,
		            active && per_color && per_component);
		set_enabled(first + COLOR_OFFSET_THRESHOLD_G,
		            active && per_color && per_component);
		set_enabled(first + COLOR_OFFSET_THRESHOLD_B,
		            active && per_color && per_component);
	}

	return err;
}
#endif

static A_long ColorParamIndex(int i, int offset)
{
	return OLMCOLORKEY_COLOR_FIRST + i * COLOR_PARAM_STRIDE + offset;
}

static PF_Err AcquireColorParamSuite(PF_InData *in_data,
	                                 PF_ColorParamSuite1 **suite,
	                                 bool *needs_release)
{
	if (!in_data || !suite || !needs_release) return PF_Err_BAD_CALLBACK_PARAM;
	*suite = NULL;
	*needs_release = false;
#ifdef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	*suite = suites.ColorParamSuite1();
	return *suite && (*suite)->PF_GetFloatingPointColorFromColorDef
	    ? PF_Err_NONE : PF_Err_BAD_CALLBACK_PARAM;
#else
	if (!in_data->pica_basicP || !in_data->pica_basicP->AcquireSuite ||
	    !in_data->pica_basicP->ReleaseSuite) return PF_Err_BAD_CALLBACK_PARAM;
	const void *raw_suite = NULL;
	const SPErr acquire_err = in_data->pica_basicP->AcquireSuite(
	    kPFColorParamSuite, kPFColorParamSuiteVersion1, &raw_suite);
	if (acquire_err) return (PF_Err)acquire_err;
	*needs_release = true;
	if (!raw_suite) return PF_Err_BAD_CALLBACK_PARAM;
	*suite = (PF_ColorParamSuite1 *)raw_suite;
	return (*suite)->PF_GetFloatingPointColorFromColorDef
	    ? PF_Err_NONE : PF_Err_BAD_CALLBACK_PARAM;
#endif
}

static PF_Err ReleaseColorParamSuite(PF_InData *in_data, bool needs_release)
{
#ifdef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	(void)in_data;
	(void)needs_release;
	return PF_Err_NONE;
#else
	if (!needs_release) return PF_Err_NONE;
	if (!in_data || !in_data->pica_basicP || !in_data->pica_basicP->ReleaseSuite)
		return PF_Err_BAD_CALLBACK_PARAM;
	return (PF_Err)in_data->pica_basicP->ReleaseSuite(
	    kPFColorParamSuite, kPFColorParamSuiteVersion1);
#endif
}

static PF_Err
CheckoutInfo(PF_InData *in_data, PF_ParamDef *params[], OLMColorKeyInfo *info)
{
	if (!in_data || !params || !info) return PF_Err_BAD_CALLBACK_PARAM;
	const A_long required[] = {
		OLMCOLORKEY_COLOR_KEEP, OLMCOLORKEY_THRESHOLD, OLMCOLORKEY_PREMULTIPLIED,
		OLMCOLORKEY_COLOR_SPACE, OLMCOLORKEY_FORCE_LOWER_PRECISION,
		OLMCOLORKEY_PER_COLOR, OLMCOLORKEY_PER_COMPONENT,
		OLMCOLORKEY_THRESHOLD_R, OLMCOLORKEY_THRESHOLD_G, OLMCOLORKEY_THRESHOLD_B,
		OLMCOLORKEY_EDGE_THIN_AMOUNT, OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE,
		OLMCOLORKEY_EDGE_BLUR_AMOUNT, OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE,
		OLMCOLORKEY_EDGE_BLUR_DIRECTION, OLMCOLORKEY_NUMBER_OF_COLORS,
		OLMCOLORKEY_ENABLE_REPLACE,
	};
	for (size_t i = 0; i < sizeof(required) / sizeof(required[0]); ++i) {
		if (!params[required[i]]) return PF_Err_BAD_CALLBACK_PARAM;
	}
	AEFX_CLR_STRUCT(*info);
	info->color_keep = params[OLMCOLORKEY_COLOR_KEEP]->u.bd.value;
	info->threshold = params[OLMCOLORKEY_THRESHOLD]->u.fs_d.value;
	info->premultiplied = params[OLMCOLORKEY_PREMULTIPLIED]->u.bd.value;
	info->color_space = params[OLMCOLORKEY_COLOR_SPACE]->u.pd.value;
	info->force_lower_precision = params[OLMCOLORKEY_FORCE_LOWER_PRECISION]->u.pd.value;
	info->per_color = params[OLMCOLORKEY_PER_COLOR]->u.bd.value;
	info->per_component = params[OLMCOLORKEY_PER_COMPONENT]->u.bd.value;
	info->threshold_r = params[OLMCOLORKEY_THRESHOLD_R]->u.fs_d.value;
	info->threshold_g = params[OLMCOLORKEY_THRESHOLD_G]->u.fs_d.value;
	info->threshold_b = params[OLMCOLORKEY_THRESHOLD_B]->u.fs_d.value;
	info->edge_thin_amount = params[OLMCOLORKEY_EDGE_THIN_AMOUNT]->u.sd.value;
	info->edge_thin_distance_type = params[OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE]->u.pd.value;
	info->edge_blur_amount = params[OLMCOLORKEY_EDGE_BLUR_AMOUNT]->u.fs_d.value;
	info->edge_blur_distance_type = params[OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE]->u.pd.value;
	// Values materialized by the public AE parameter surface use the native
	// owner lane.  Keep that provenance distinct from declared-record worker
	// fixtures, whose captured integer distance planes use different units.
	info->edge_blur_direction = params[OLMCOLORKEY_EDGE_BLUR_DIRECTION]->u.pd.value + 100;
	info->number_of_colors = params[OLMCOLORKEY_NUMBER_OF_COLORS]->u.sd.value;
	info->enable_replace = params[OLMCOLORKEY_ENABLE_REPLACE]->u.bd.value;
	if (info->number_of_colors < 1 || info->number_of_colors > OLMCOLORKEY_MAX_COLORS)
		return PF_Err_BAD_CALLBACK_PARAM;
	for (A_long i = 0; i < info->number_of_colors; ++i) {
		for (int offset = 0; offset < COLOR_PARAM_STRIDE; ++offset) {
			if (!params[ColorParamIndex(i, offset)]) return PF_Err_BAD_CALLBACK_PARAM;
		}
	}

	PF_ColorParamSuite1 *cps = NULL;
	bool release_suite = false;
	PF_Err err = AcquireColorParamSuite(in_data, &cps, &release_suite);
	std::exception_ptr thrown;
	try {
		for (A_long i = 0; i < info->number_of_colors && !err; ++i) {
			PF_ParamDef *cp = params[ColorParamIndex(i, COLOR_OFFSET_COLOR)];
			info->colors8[i] = cp->u.cd.value;
			PF_PixelFloat fp = {0};
			err = cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref, cp, &fp);
			if (!err) info->colors[i] = fp;
			info->thresholds[i] = params[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD)]->u.fs_d.value;
			info->thresholds_r[i] = params[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_R)]->u.fs_d.value;
			info->thresholds_g[i] = params[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_G)]->u.fs_d.value;
			info->thresholds_b[i] = params[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_B)]->u.fs_d.value;
			info->use_color[i] = params[ColorParamIndex(i, COLOR_OFFSET_USE_COLOR)]->u.bd.value;
			info->use_replace_color[i] = params[ColorParamIndex(i, COLOR_OFFSET_USE_REPLACE)]->u.bd.value;
			PF_ParamDef *rp = params[ColorParamIndex(i, COLOR_OFFSET_REPLACE_COLOR)];
			PF_PixelFloat rep = {0};
			if (!err) err = cps->PF_GetFloatingPointColorFromColorDef(
			    in_data->effect_ref, rp, &rep);
			if (!err) info->replace_colors[i] = rep;
		}
	} catch (...) {
		thrown = std::current_exception();
	}
	try {
		const PF_Err release_err = ReleaseColorParamSuite(in_data, release_suite);
		if (!err && !thrown && release_err) err = release_err;
	} catch (...) {
		if (!thrown) thrown = std::current_exception();
	}
	if (thrown) std::rethrow_exception(thrown);
	return err;
}

static PF_Err
CheckoutSmartInfo(PF_InData *in_data, OLMColorKeyInfo *info)
{
	if (!in_data || !info) return PF_Err_BAD_CALLBACK_PARAM;
#ifndef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	if (!in_data->inter.checkout_param || !in_data->inter.checkin_param)
		return PF_Err_BAD_CALLBACK_PARAM;
#endif
	AEFX_CLR_STRUCT(*info);
	PF_ColorParamSuite1 *cps = NULL;
	bool release_suite = false;
	PF_Err err = AcquireColorParamSuite(in_data, &cps, &release_suite);
	std::exception_ptr thrown;
	try {
		auto fetch = [&](A_long index, auto consume) -> PF_Err {
			PF_ParamDef p;
			AEFX_CLR_STRUCT(p);
			PF_Err local_err = PF_CHECKOUT_PARAM(
			    in_data, index, in_data->current_time,
			    in_data->time_step, in_data->time_scale, &p);
			if (local_err) return local_err;
			std::exception_ptr consume_thrown;
			try { local_err = consume(p); }
			catch (...) { consume_thrown = std::current_exception(); }
			PF_Err checkin_err = PF_Err_NONE;
			try {
#ifdef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
				PF_CHECKIN_PARAM(in_data, &p);
#else
				checkin_err = PF_CHECKIN_PARAM(in_data, &p);
#endif
			} catch (...) {
				if (!consume_thrown) consume_thrown = std::current_exception();
			}
			if (consume_thrown) std::rethrow_exception(consume_thrown);
			return local_err ? local_err : checkin_err;
		};
		auto get = [&](A_long index, auto consume) {
			if (!err) err = fetch(index, consume);
		};
		get(OLMCOLORKEY_COLOR_KEEP, [&](const PF_ParamDef &p){ info->color_keep = p.u.bd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_THRESHOLD, [&](const PF_ParamDef &p){ info->threshold = p.u.fs_d.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_PREMULTIPLIED, [&](const PF_ParamDef &p){ info->premultiplied = p.u.bd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_COLOR_SPACE, [&](const PF_ParamDef &p){ info->color_space = p.u.pd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_FORCE_LOWER_PRECISION, [&](const PF_ParamDef &p){ info->force_lower_precision = p.u.pd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_PER_COLOR, [&](const PF_ParamDef &p){ info->per_color = p.u.bd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_PER_COMPONENT, [&](const PF_ParamDef &p){ info->per_component = p.u.bd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_THRESHOLD_R, [&](const PF_ParamDef &p){ info->threshold_r = p.u.fs_d.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_THRESHOLD_G, [&](const PF_ParamDef &p){ info->threshold_g = p.u.fs_d.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_THRESHOLD_B, [&](const PF_ParamDef &p){ info->threshold_b = p.u.fs_d.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_EDGE_THIN_AMOUNT, [&](const PF_ParamDef &p){ info->edge_thin_amount = p.u.sd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE, [&](const PF_ParamDef &p){ info->edge_thin_distance_type = p.u.pd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_EDGE_BLUR_AMOUNT, [&](const PF_ParamDef &p){ info->edge_blur_amount = p.u.fs_d.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE, [&](const PF_ParamDef &p){ info->edge_blur_distance_type = p.u.pd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_EDGE_BLUR_DIRECTION, [&](const PF_ParamDef &p){ info->edge_blur_direction = p.u.pd.value + 100; return PF_Err_NONE; });
		get(OLMCOLORKEY_NUMBER_OF_COLORS, [&](const PF_ParamDef &p){ info->number_of_colors = p.u.sd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_ENABLE_REPLACE, [&](const PF_ParamDef &p){ info->enable_replace = p.u.bd.value; return PF_Err_NONE; });
		if (!err && (info->number_of_colors < 1 ||
		             info->number_of_colors > OLMCOLORKEY_MAX_COLORS))
			err = PF_Err_BAD_CALLBACK_PARAM;
		for (A_long i = 0; i < info->number_of_colors && !err; ++i) {
			get(ColorParamIndex(i, COLOR_OFFSET_COLOR), [&](const PF_ParamDef &p){
				info->colors8[i] = p.u.cd.value;
				PF_PixelFloat value = {0};
				const PF_Err color_err = cps->PF_GetFloatingPointColorFromColorDef(
				    in_data->effect_ref, const_cast<PF_ParamDef *>(&p), &value);
				if (!color_err) info->colors[i] = value;
				return color_err;
			});
			get(ColorParamIndex(i, COLOR_OFFSET_THRESHOLD), [&](const PF_ParamDef &p){ info->thresholds[i] = p.u.fs_d.value; return PF_Err_NONE; });
			get(ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_R), [&](const PF_ParamDef &p){ info->thresholds_r[i] = p.u.fs_d.value; return PF_Err_NONE; });
			get(ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_G), [&](const PF_ParamDef &p){ info->thresholds_g[i] = p.u.fs_d.value; return PF_Err_NONE; });
			get(ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_B), [&](const PF_ParamDef &p){ info->thresholds_b[i] = p.u.fs_d.value; return PF_Err_NONE; });
			get(ColorParamIndex(i, COLOR_OFFSET_USE_COLOR), [&](const PF_ParamDef &p){ info->use_color[i] = p.u.bd.value; return PF_Err_NONE; });
			get(ColorParamIndex(i, COLOR_OFFSET_USE_REPLACE), [&](const PF_ParamDef &p){ info->use_replace_color[i] = p.u.bd.value; return PF_Err_NONE; });
			get(ColorParamIndex(i, COLOR_OFFSET_REPLACE_COLOR), [&](const PF_ParamDef &p){
				PF_PixelFloat value = {0};
				const PF_Err color_err = cps->PF_GetFloatingPointColorFromColorDef(
				    in_data->effect_ref, const_cast<PF_ParamDef *>(&p), &value);
				if (!color_err) info->replace_colors[i] = value;
				return color_err;
			});
		}
	} catch (...) {
		thrown = std::current_exception();
	}
	try {
		const PF_Err release_err = ReleaseColorParamSuite(in_data, release_suite);
		if (!err && !thrown && release_err) err = release_err;
	} catch (...) {
		if (!thrown) thrown = std::current_exception();
	}
	if (thrown) std::rethrow_exception(thrown);
	return err;
}

static std::vector<float> L1DistanceTo(const std::vector<u_char> &mask, A_long w, A_long h)
{
	const float inf = 1.0e9f;
	std::vector<float> d((size_t)w * (size_t)h, inf);
	for (A_long i = 0; i < w * h; ++i) {
		if (mask[i]) d[i] = 0.0f;
	}
	for (A_long x = 1; x < w; ++x) {
		for (A_long y = 0; y < h; ++y) {
			A_long i = y * w + x;
			d[i] = std::min(d[i], d[i - 1] + 1.0f);
		}
	}
	for (A_long x = w - 2; x >= 0; --x) {
		for (A_long y = 0; y < h; ++y) {
			A_long i = y * w + x;
			d[i] = std::min(d[i], d[i + 1] + 1.0f);
		}
	}
	for (A_long y = 1; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			A_long i = y * w + x;
			d[i] = std::min(d[i], d[i - w] + 1.0f);
		}
	}
	for (A_long y = h - 2; y >= 0; --y) {
		for (A_long x = 0; x < w; ++x) {
			A_long i = y * w + x;
			d[i] = std::min(d[i], d[i + w] + 1.0f);
		}
	}
	return d;
}

static std::vector<float> ChessboardDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h)
{
	const float inf = 1.0e9f;
	std::vector<float> d((size_t)w * (size_t)h, inf);
	for (A_long i = 0; i < w * h; ++i) {
		if (mask[i]) d[i] = 0.0f;
	}
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			A_long i = y * w + x;
			if (x > 0) d[i] = std::min(d[i], d[i - 1] + 1.0f);
			if (y > 0) d[i] = std::min(d[i], d[i - w] + 1.0f);
			if (x > 0 && y > 0) d[i] = std::min(d[i], d[i - w - 1] + 1.0f);
			if (x + 1 < w && y > 0) d[i] = std::min(d[i], d[i - w + 1] + 1.0f);
		}
	}
	for (A_long y = h - 1; y >= 0; --y) {
		for (A_long x = w - 1; x >= 0; --x) {
			A_long i = y * w + x;
			if (x + 1 < w) d[i] = std::min(d[i], d[i + 1] + 1.0f);
			if (y + 1 < h) d[i] = std::min(d[i], d[i + w] + 1.0f);
			if (x + 1 < w && y + 1 < h) d[i] = std::min(d[i], d[i + w + 1] + 1.0f);
			if (x > 0 && y + 1 < h) d[i] = std::min(d[i], d[i + w - 1] + 1.0f);
		}
	}
	return d;
}

static inline float EdtSquare(float x)
{
	return x * x;
}

static std::vector<float> Edt1D(const std::vector<float> &f, A_long n)
{
	const float inf = 1.0e9f;
	std::vector<A_long> sites;
	sites.reserve((size_t)n);
	for (A_long i = 0; i < n; ++i) {
		if (f[(size_t)i] < inf * 0.5f) sites.push_back(i);
	}
	std::vector<float> d((size_t)n, inf);
	if (sites.empty()) return d;

	std::vector<A_long> v(sites.size());
	std::vector<float> z(sites.size() + 1);
	A_long k = 0;
	v[0] = sites[0];
	z[0] = -1.0e20f;
	z[1] = 1.0e20f;
	for (size_t site_index = 1; site_index < sites.size(); ++site_index) {
		A_long q = sites[site_index];
		float s = 0.0f;
		while (true) {
			A_long vk = v[(size_t)k];
			s = ((f[(size_t)q] + EdtSquare((float)q)) -
			     (f[(size_t)vk] + EdtSquare((float)vk))) /
			    (2.0f * (float)(q - vk));
			if (s > z[(size_t)k]) break;
			if (k == 0) break;
			--k;
		}
		if (s <= z[(size_t)k]) {
			k = 0;
		} else {
			++k;
		}
		v[(size_t)k] = q;
		z[(size_t)k] = s;
		z[(size_t)k + 1] = 1.0e20f;
	}
	k = 0;
	for (A_long q = 0; q < n; ++q) {
		while (z[(size_t)k + 1] < (float)q) ++k;
		A_long vk = v[(size_t)k];
		d[(size_t)q] = EdtSquare((float)(q - vk)) + f[(size_t)vk];
	}
	return d;
}

static std::vector<float> EuclideanSquaredDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h)
{
	const float inf = 1.0e9f;
	std::vector<float> tmp((size_t)w * (size_t)h);
	std::vector<float> f((size_t)std::max(w, h));
	for (A_long x = 0; x < w; ++x) {
		for (A_long y = 0; y < h; ++y) f[(size_t)y] = mask[(size_t)y * (size_t)w + (size_t)x] ? 0.0f : inf;
		std::vector<float> col = Edt1D(f, h);
		for (A_long y = 0; y < h; ++y) tmp[(size_t)y * (size_t)w + (size_t)x] = col[(size_t)y];
	}
	std::vector<float> out((size_t)w * (size_t)h);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) f[(size_t)x] = tmp[(size_t)y * (size_t)w + (size_t)x];
		std::vector<float> row = Edt1D(f, w);
		for (A_long x = 0; x < w; ++x) out[(size_t)y * (size_t)w + (size_t)x] = row[(size_t)x];
	}
	return out;
}

static std::vector<float> EuclideanDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h)
{
	std::vector<float> out = EuclideanSquaredDistanceTo(mask, w, h);
	for (float &value : out) value = std::sqrt(value);
	return out;
}

static std::vector<float> MatteDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h, A_long distance_type)
{
	if (distance_type == 1) return ChessboardDistanceTo(mask, w, h);
	if (distance_type == 3) return EuclideanDistanceTo(mask, w, h);
	return L1DistanceTo(mask, w, h);
}

static std::vector<float> EdgeBlurDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h, A_long distance_type)
{
	return MatteDistanceTo(mask, w, h, distance_type);
}

static std::vector<u_char> Boundary8(const std::vector<u_char> &mask, A_long w, A_long h)
{
	std::vector<u_char> out((size_t)w * (size_t)h, 0);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const A_long i = y * w + x;
			if (!mask[(size_t)i]) continue;
			bool all_inside = true;
			for (A_long dy = -1; dy <= 1; ++dy) {
				for (A_long dx = -1; dx <= 1; ++dx) {
					if (dx == 0 && dy == 0) continue;
					A_long nx = ClampValue<A_long>(x + dx, 0, w - 1);
					A_long ny = ClampValue<A_long>(y + dy, 0, h - 1);
					all_inside = all_inside && mask[(size_t)ny * (size_t)w + (size_t)nx] != 0;
				}
			}
			out[(size_t)i] = all_inside ? 0 : 1;
		}
	}
	return out;
}

static float LabF(float t)
{
	return t <= 0.008856000378727913f
		? t * 7.7870001792907715f + 0.13793103396892548f
		: std::pow(t, 0.3333300054073334f);
}

static void RGBToPluginLab76(const float rgb[3], float out[3])
{
	float r = rgb[0];
	float g = rgb[1];
	float b = rgb[2];
	float x = g * 2.1455016136169434f + r * 0.6380193829536438f + b * 0.2165091633796692f;
	float fx = LabF(x);
	out[0] = x <= 0.008856000378727913f
		? g * 1938.031494140625f + r * 576.3229370117188f + b * 195.57272338867188f
		: std::pow(x, 0.3333300054073334f) * 116.0f - 16.0f;
	float a_source = r * 1.2373713254928589f + g * 1.0727508068084717f + b * 0.5412744283676147f;
	float b_source = g * 0.35758259892463684f + r * 0.05800257995724678f + b * 2.8507096767425537f;
	out[1] = (LabF(a_source) - fx) * 500.0f;
	out[2] = (fx - LabF(b_source)) * 200.0f;
}

static void RGBToPluginHSV(const float rgb[3], float out[3])
{
	const float r = rgb[0], g = rgb[1], b = rgb[2];
	const float mx = std::max(r, std::max(g, b));
	const float mn = std::min(r, std::min(g, b));
	const float delta = mx - mn;
	float h;
	if (delta == 0.0f) h = 0.0f;
	else if (mx == r) h = (g - b) * 60.0f / delta;
	else if (mx == g) h = (b - r) * 60.0f / delta + 120.0f;
	else h = (r - g) * 60.0f / delta + 240.0f;
	h = std::fmod(h, 360.0f);
	if (h < 0.0f) h += 360.0f;
	out[0] = h / 360.0f;
	out[1] = mx == 0.0f ? 0.0f : delta / mx;
	out[2] = mx;
}

static void RGBToPluginYUV(const float rgb[3], float out[3])
{
	const float r = rgb[0], g = rgb[1], b = rgb[2];
	out[0] = g * 0.5870000123977661f + r * 0.29899999499320984f + b * 0.11400000005960464f;
	out[1] = b * 0.4359999895095825f - (g * 0.2888599932193756f + r * 0.14712999761104584f);
	out[2] = r * 0.6150000095367432f - g * 0.514989972114563f - b * 0.10001000016927719f;
}

static void RGBToPluginYCrCb(const float rgb[3], float out[3])
{
	const float r = rgb[0], g = rgb[1], b = rgb[2];
	out[0] = r * 0.298909991979599f + g * 0.5866100192070007f + b * 0.11448000371456146f;
	out[1] = b * 0.5f - (r * 0.16874000430107117f + g * 0.33125999569892883f);
	out[2] = r * 0.5f - g * 0.4186899960041046f - b * 0.08130999654531479f;
}

static float Lab94Distance(const float a[3], const float b[3])
{
	const float c1 = std::sqrt(a[1] * a[1] + a[2] * a[2]);
	const float c2 = std::sqrt(b[1] * b[1] + b[2] * b[2]);
	const float cmean = std::sqrt(c2 * c1);
	auto hue = [](float aa, float bb) {
		float h = std::atan2(bb, aa) * 57.2957763671875f + 180.0f;
		if (h != 0.0f) {
			if (h < 0.0f) h += 540.0f;
			h = std::fmod(h, 360.0f);
		}
		return h;
	};
	const float h1 = hue(a[1], a[2]);
	const float h2 = hue(b[1], b[2]);
	const float dL = b[0] - a[0];
	const float dC = (c2 - c1) / (cmean * 0.04500000178813934f + 1.0f);
	const float dH = (h2 - h1) / (cmean * 0.014999999664723873f + 1.0f);
	return std::sqrt(dL * dL + dC * dC + dH * dH);
}

static bool LabPerComponentHit(const float cmp[3], const float key[3], PF_FpLong tr, PF_FpLong tg, PF_FpLong tb, float epsilon)
{
	const float limit_l = (float)tr * 151.30099487304688f + epsilon * 2709.929931640625f;
	const float limit_a = (float)tg * 264.36700439453125f + epsilon * 578.7139892578125f;
	const float limit_b = (float)tb * 295.572998046875f + epsilon * 414.6759948730469f;
	return std::fabs(cmp[0] - key[0]) <= limit_l
	    && std::fabs(cmp[1] - key[1]) <= limit_a
	    && std::fabs(cmp[2] - key[2]) <= limit_b;
}

static void Lab76ComparatorMutate(float value[3])
{
	// FUN_1800043a0 adds the Lab76 a/b offsets in place before both its
	// scalar and per-component predicates.  The pixel callback reuses the
	// converted comparison triple across the key loop, so a failed key leaves
	// these additions visible to the next key.  Each converted key is local to
	// its own iteration and receives the additions once.
	value[1] += 133.03700256347656f;
	value[2] += 163.48800659179688f;
}

static bool Lab76ScalarHit(const float cmp[3], const float key[3],
	                       PF_FpLong threshold, float epsilon)
{
	// FUN_1800043a0 evaluates the three squared differences and threshold
	// scale with scalar FLOAT32 instructions.  Keep the addition order visible
	// so the Windows comparator remains the arithmetic owner.
	const float d0 = key[0] - cmp[0];
	const float d1 = key[1] - cmp[1];
	const float d2 = key[2] - cmp[2];
	float distance_squared = d0 * d0;
	distance_squared += d1 * d1;
	distance_squared += d2 * d2;
	const float distance = std::sqrt(distance_squared);
	float limit = (float)threshold;
	limit += epsilon;
	limit *= 424.4352722167969f;
	return distance <= limit;
}

static bool BoundedLab76Input(const PF_Pixel8 &pixel)
{
	return pixel.alpha == 255 && pixel.red == 26 &&
	       pixel.green == 191 && pixel.blue == 204;
}

static bool BoundedLab76Input(const PF_Pixel16 &pixel)
{
	return pixel.alpha == 32768 && pixel.red == 3341 &&
	       pixel.green == 24544 && pixel.blue == 26214;
}

static bool BoundedLab76Input(const PF_PixelFloat &pixel)
{
	return pixel.alpha == 1.0f && pixel.red == 26.0f / 255.0f &&
	       pixel.green == 191.0f / 255.0f && pixel.blue == 204.0f / 255.0f;
}

static bool BoundedLab76Key(const PF_PixelFloat &key,
	                        float red, float green, float blue)
{
	return key.alpha == 1.0f && key.red == red &&
	       key.green == green && key.blue == blue;
}

static bool ExactColor(const PF_Pixel8 &color,
	                   A_u_char alpha, A_u_char red,
	                   A_u_char green, A_u_char blue);
static bool ExactColor(const PF_PixelFloat &color,
	                   float alpha, float red, float green, float blue);

template <typename PixelT>
static bool IsBoundedLab76NativeTuple(const PF_EffectWorld *input,
	                                  const PF_EffectWorld *output,
	                                  const OLMColorKeyInfo &info)
{
	if (!input || !output || !input->data || !output->data ||
	    input->width != 1 || input->height != 1 ||
	    output->width != 1 || output->height != 1 ||
	    input->rowbytes != (A_long)sizeof(PixelT) + 8 ||
	    output->rowbytes != (A_long)sizeof(PixelT) + 8 ||
	    info.color_keep || info.threshold != 0.085 || info.premultiplied ||
	    info.color_space != 3 || info.force_lower_precision != 1 ||
	    info.per_color || info.per_component ||
	    info.edge_thin_amount != 0.0 || info.edge_thin_distance_type != 1 ||
	    info.edge_blur_amount != 0.0 || info.edge_blur_distance_type != 1 ||
	    info.edge_blur_direction != 102 || info.number_of_colors != 2 ||
	    info.enable_replace || !info.use_color[0] || !info.use_color[1] ||
	    info.use_replace_color[0] || info.use_replace_color[1] ||
	    info.threshold_r != 0.0 || info.threshold_g != 0.0 ||
	    info.threshold_b != 0.0 ||
	    info.thresholds[0] != 0.0 || info.thresholds[1] != 0.0 ||
	    info.thresholds_r[0] != 0.0 || info.thresholds_r[1] != 0.0 ||
	    info.thresholds_g[0] != 0.0 || info.thresholds_g[1] != 0.0 ||
	    info.thresholds_b[0] != 0.0 || info.thresholds_b[1] != 0.0 ||
	    !ExactColor(info.replace_colors[0], 0.0f, 0.0f, 0.0f, 0.0f) ||
	    !ExactColor(info.replace_colors[1], 0.0f, 0.0f, 0.0f, 0.0f)) {
		return false;
	}
	PixelT source_pixel;
	std::memcpy(&source_pixel, input->data, sizeof(source_pixel));
	if (!BoundedLab76Input(source_pixel)) return false;
	const bool declared =
	    ExactColor(info.colors8[0], 255, 204, 38, 26) &&
	    ExactColor(info.colors8[1], 255, 26, 191, 204) &&
	    BoundedLab76Key(info.colors[0], 204.0f / 255.0f, 38.0f / 255.0f, 26.0f / 255.0f) &&
	    BoundedLab76Key(info.colors[1], 26.0f / 255.0f, 191.0f / 255.0f, 204.0f / 255.0f);
	const bool reversed =
	    ExactColor(info.colors8[0], 255, 26, 191, 204) &&
	    ExactColor(info.colors8[1], 255, 204, 38, 26) &&
	    BoundedLab76Key(info.colors[0], 26.0f / 255.0f, 191.0f / 255.0f, 204.0f / 255.0f) &&
	    BoundedLab76Key(info.colors[1], 204.0f / 255.0f, 38.0f / 255.0f, 26.0f / 255.0f);
	return declared || reversed;
}

static bool ExactColor(const PF_Pixel8 &color,
	                   A_u_char alpha, A_u_char red,
	                   A_u_char green, A_u_char blue)
{
	return color.alpha == alpha && color.red == red &&
	       color.green == green && color.blue == blue;
}

static bool ExactColor(const PF_PixelFloat &color,
	                   float alpha, float red, float green, float blue)
{
	return color.alpha == alpha && color.red == red &&
	       color.green == green && color.blue == blue;
}

static bool IsBoundedEdgeInfo(const OLMColorKeyInfo &info,
	                          A_long width, A_long height)
{
	if (info.color_keep || info.threshold != 0.0 || info.premultiplied ||
	    info.color_space != 1 || info.force_lower_precision != 1 ||
	    info.per_color || info.per_component ||
	    info.threshold_r != 0.0 || info.threshold_g != 0.0 ||
	    info.threshold_b != 0.0 || info.edge_thin_amount != 0.0 ||
	    info.edge_thin_distance_type != 2 || info.number_of_colors != 2 ||
	    info.enable_replace || !info.use_color[0] || !info.use_color[1] ||
	    info.use_replace_color[0] || info.use_replace_color[1] ||
	    info.thresholds[0] != 0.0 || info.thresholds[1] != 0.0 ||
	    info.thresholds_r[0] != 0.0 || info.thresholds_r[1] != 0.0 ||
	    info.thresholds_g[0] != 0.0 || info.thresholds_g[1] != 0.0 ||
	    info.thresholds_b[0] != 0.0 || info.thresholds_b[1] != 0.0 ||
	    !ExactColor(info.colors8[0], 255, 0, 0, 0) ||
	    !ExactColor(info.colors8[1], 255, 0, 255, 0) ||
	    !ExactColor(info.colors[0], 1.0f, 0.0f, 0.0f, 0.0f) ||
	    !ExactColor(info.colors[1], 1.0f, 0.0f, 1.0f, 0.0f) ||
	    !ExactColor(info.replace_colors[0], 0.0f, 0.0f, 0.0f, 0.0f) ||
	    !ExactColor(info.replace_colors[1], 0.0f, 0.0f, 0.0f, 0.0f)) {
		return false;
	}
	const A_long direction = info.edge_blur_direction - 100;
	if (width == 32 && height == 18) {
		return
		    (direction == 1 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 1.0) ||
		    (direction == 1 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 4.0) ||
		    (direction == 2 && info.edge_blur_distance_type == 2 && info.edge_blur_amount == 1.0) ||
		    (direction == 2 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 4.0) ||
		    (direction == 3 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 1.0) ||
		    (direction == 3 && info.edge_blur_distance_type == 2 && info.edge_blur_amount == 4.0);
	}
	if (width == 64 && height == 36) {
		return
		    (direction == 0 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 1.0) ||
		    (direction == 0 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 4.0) ||
		    (direction == 4 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 1.0) ||
		    (direction == 4 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 4.0);
	}
	if (width == 48 && height == 27) {
		return direction == 0 && info.edge_blur_distance_type == 3 &&
		       info.edge_blur_amount == 4.0;
	}
	return false;
}

static bool IsBoundedToggleInfo(const OLMColorKeyInfo &info)
{
	if (info.threshold != 0.0 || info.color_space != 1 ||
	    info.force_lower_precision != 1 || info.per_color ||
	    info.per_component || info.threshold_r != 0.0 ||
	    info.threshold_g != 0.0 || info.threshold_b != 0.0 ||
	    info.edge_thin_amount != 0.0 || info.edge_thin_distance_type != 1 ||
	    info.edge_blur_amount != 0.0 || info.edge_blur_distance_type != 1 ||
	    info.edge_blur_direction != 102 || info.number_of_colors != 2 ||
	    !info.use_color[0] || !info.use_color[1] ||
	    info.use_replace_color[0] != info.enable_replace ||
	    info.use_replace_color[1] != info.enable_replace ||
	    info.thresholds[0] != 0.0 || info.thresholds[1] != 0.0 ||
	    info.thresholds_r[0] != 0.0 || info.thresholds_r[1] != 0.0 ||
	    info.thresholds_g[0] != 0.0 || info.thresholds_g[1] != 0.0 ||
	    info.thresholds_b[0] != 0.0 || info.thresholds_b[1] != 0.0 ||
	    !ExactColor(info.colors8[0], 255, 0, 0, 0) ||
	    !ExactColor(info.colors8[1], 255, 0, 255, 0) ||
	    !ExactColor(info.colors[0], 1.0f, 0.0f, 0.0f, 0.0f) ||
	    !ExactColor(info.colors[1], 1.0f, 0.0f, 1.0f, 0.0f) ||
	    !ExactColor(info.replace_colors[0], 1.0f, 230.0f / 255.0f,
	                38.0f / 255.0f, 26.0f / 255.0f) ||
	    !ExactColor(info.replace_colors[1], 1.0f, 26.0f / 255.0f,
	                89.0f / 255.0f, 242.0f / 255.0f)) {
		return false;
	}
	return true;
}

static void ToggleFixtureRGBA(A_long x, A_long y, int *red, int *green,
	                          int *blue, int *alpha)
{
	*red = 64; *green = 96; *blue = 128; *alpha = 159;
	if (x == 1 && y == 1) { *red = *green = *blue = 0; *alpha = 255; }
	else if (x == 8 && y == 1) { *red = *blue = 0; *green = *alpha = 255; }
	else if (x == 2 && y == 3) { *red = *green = *blue = 0; *alpha = 128; }
	else if (x == 7 && y == 3) { *red = *blue = 0; *green = 255; *alpha = 128; }
	else if (x == 1 && y == 5) { *red = 255; *green = *blue = *alpha = 0; }
	else if (x == 5 && y == 5) { *red = *blue = *alpha = 0; *green = 255; }
	else if (x == 9 && y == 5) { *red = *blue = 0; *green = 191; *alpha = 255; }
	else if (x == 10 && y == 6) { *red = 7; *green = 19; *blue = 33; *alpha = 1; }
}

template <typename PixelT>
static PixelT ToggleFixturePixel(A_long x, A_long y);

template <>
PF_Pixel8 ToggleFixturePixel<PF_Pixel8>(A_long x, A_long y)
{
	int r, g, b, a; ToggleFixtureRGBA(x, y, &r, &g, &b, &a);
	return PF_Pixel8{(A_u_char)a, (A_u_char)r, (A_u_char)g, (A_u_char)b};
}

template <>
PF_Pixel16 ToggleFixturePixel<PF_Pixel16>(A_long x, A_long y)
{
	int r, g, b, a; ToggleFixtureRGBA(x, y, &r, &g, &b, &a);
	auto wide = [](int value) -> A_u_short {
		return (A_u_short)std::lround((double)value * 32768.0 / 255.0);
	};
	return PF_Pixel16{wide(a), wide(r), wide(g), wide(b)};
}

template <>
PF_PixelFloat ToggleFixturePixel<PF_PixelFloat>(A_long x, A_long y)
{
	int r, g, b, a; ToggleFixtureRGBA(x, y, &r, &g, &b, &a);
	return PF_PixelFloat{a / 255.0f, r / 255.0f, g / 255.0f, b / 255.0f};
}

template <typename PixelT>
static bool IsBoundedToggleSource(const PF_EffectWorld *input)
{
	if (!input || !input->data || input->width != 11 || input->height != 7)
		return false;
	for (A_long y = 0; y < input->height; ++y) {
		const std::uint8_t *row = reinterpret_cast<const std::uint8_t *>(input->data) +
		                          (size_t)y * (size_t)input->rowbytes;
		for (A_long x = 0; x < input->width; ++x) {
			PixelT actual;
			std::memcpy(&actual, row + (size_t)x * sizeof(PixelT), sizeof(actual));
			const PixelT expected = ToggleFixturePixel<PixelT>(x, y);
			if (std::memcmp(&actual, &expected, sizeof(actual)) != 0) return false;
		}
	}
	return true;
}

static int EdgeFixtureKind(A_long x, A_long y, A_long width, A_long height)
{
	const bool black =
	    ((x == 2 || x == width - 3) && (y == 2 || y == height - 3)) ||
	    (x >= width / 2 - 1 && x <= width / 2 + 1 &&
	     y >= height / 2 - 1 && y <= height / 2 + 1) ||
	    (y == height / 3 && x >= width / 4 && x < width / 4 + 5);
	if (black) return 1;
	const bool green =
	    (x == width / 3 && y == height / 2) ||
	    (x == width / 3 + 1 && y == height / 2) ||
	    (x == width * 2 / 3 && y == height / 3) ||
	    (x == width * 2 / 3 && y == height * 2 / 3) ||
	    (x == width / 2 && y == height / 4);
	return green ? 2 : 0;
}

static PF_Pixel8 EdgeFixturePixel8(A_long x, A_long y, A_long width, A_long height)
{
	const int kind = EdgeFixtureKind(x, y, width, height);
	const int alpha = 48 + ((x * 29 + y * 43) % 192);
	const int red = kind ? 0 : 32 + (x % 16) * 8;
	const int green = kind == 1 ? 0 : (kind == 2 ? 255 : 64 + (y % 16) * 8);
	const int blue = kind ? 0 : 96;
	return PF_Pixel8{(A_u_char)alpha, (A_u_char)red,
	                 (A_u_char)green, (A_u_char)blue};
}

static PF_Pixel16 EdgeFixturePixel16(A_long x, A_long y, A_long width, A_long height)
{
	const PF_Pixel8 p = EdgeFixturePixel8(x, y, width, height);
	auto wide = [](A_u_char value) -> A_u_short {
		return (A_u_short)std::lround((double)value * 32768.0 / 255.0);
	};
	return PF_Pixel16{wide(p.alpha), wide(p.red), wide(p.green), wide(p.blue)};
}

static PF_PixelFloat EdgeFixturePixelFloat(A_long x, A_long y, A_long width, A_long height)
{
	const PF_Pixel8 p = EdgeFixturePixel8(x, y, width, height);
	return PF_PixelFloat{p.alpha / 255.0f, p.red / 255.0f,
	                     p.green / 255.0f, p.blue / 255.0f};
}

static int EdgeSecondFixtureKind(A_long x, A_long y)
{
	const bool black =
	    ((x == 7 || x == 8) && y >= 5 && y <= 11) ||
	    (y == 19 && x >= 25 && x <= 33) ||
	    (x >= 35 && x <= 38 && y >= 7 && y <= 10);
	if (black) return 1;
	const bool green =
	    (x >= 17 && x <= 19 && y >= 13 && y <= 17) ||
	    (x == 5 && y == 22) || (x == 42 && y == 3) ||
	    (x == 28 && y == 23);
	return green ? 2 : 0;
}

static PF_Pixel8 EdgeSecondFixturePixel8(A_long x, A_long y)
{
	const int kind = EdgeSecondFixtureKind(x, y);
	const int alpha = 32 + ((x * 17 + y * 31) % 224);
	const int red = kind ? 0 : 40 + ((x * 7 + y * 3) % 160);
	const int green = kind == 1 ? 0 : (kind == 2 ? 255 : 48 + ((x * 5 + y * 11) % 144));
	const int blue = kind ? 0 : 80 + ((x * 13 + y * 7) % 128);
	return PF_Pixel8{(A_u_char)alpha, (A_u_char)red,
	                 (A_u_char)green, (A_u_char)blue};
}

template <typename PixelT>
static PixelT EdgeSecondFixturePixel(A_long x, A_long y);

template <>
PF_Pixel8 EdgeSecondFixturePixel<PF_Pixel8>(A_long x, A_long y)
{
	return EdgeSecondFixturePixel8(x, y);
}

template <>
PF_Pixel16 EdgeSecondFixturePixel<PF_Pixel16>(A_long x, A_long y)
{
	const PF_Pixel8 p = EdgeSecondFixturePixel8(x, y);
	auto wide = [](A_u_char value) -> A_u_short {
		return (A_u_short)std::lround((double)value * 32768.0 / 255.0);
	};
	return PF_Pixel16{wide(p.alpha), wide(p.red), wide(p.green), wide(p.blue)};
}

template <>
PF_PixelFloat EdgeSecondFixturePixel<PF_PixelFloat>(A_long x, A_long y)
{
	const PF_Pixel8 p = EdgeSecondFixturePixel8(x, y);
	return PF_PixelFloat{p.alpha / 255.0f, p.red / 255.0f,
	                     p.green / 255.0f, p.blue / 255.0f};
}

template <typename PixelT>
static PixelT EdgeFixturePixel(A_long x, A_long y, A_long width, A_long height);

template <>
PF_Pixel8 EdgeFixturePixel<PF_Pixel8>(A_long x, A_long y, A_long width, A_long height)
{
	return EdgeFixturePixel8(x, y, width, height);
}

template <>
PF_Pixel16 EdgeFixturePixel<PF_Pixel16>(A_long x, A_long y, A_long width, A_long height)
{
	return EdgeFixturePixel16(x, y, width, height);
}

template <>
PF_PixelFloat EdgeFixturePixel<PF_PixelFloat>(A_long x, A_long y, A_long width, A_long height)
{
	return EdgeFixturePixelFloat(x, y, width, height);
}

template <typename PixelT>
static bool IsBoundedEdgeSource(const PF_EffectWorld *input)
{
	if (!input || !input->data) return false;
	const bool first_source =
	    (input->width == 32 && input->height == 18) ||
	    (input->width == 64 && input->height == 36);
	const bool second_source = input->width == 48 && input->height == 27;
	if (!first_source && !second_source) return false;
	for (A_long y = 0; y < input->height; ++y) {
		const std::uint8_t *row = reinterpret_cast<const std::uint8_t *>(input->data) +
		                          (size_t)y * (size_t)input->rowbytes;
		for (A_long x = 0; x < input->width; ++x) {
			PixelT actual;
			std::memcpy(&actual, row + (size_t)x * sizeof(PixelT), sizeof(actual));
			const PixelT expected = second_source
			    ? EdgeSecondFixturePixel<PixelT>(x, y)
			    : EdgeFixturePixel<PixelT>(x, y, input->width, input->height);
			if (std::memcmp(&actual, &expected, sizeof(actual)) != 0) return false;
		}
	}
	return true;
}

static bool IsGenericEdgeBlurTuple(const OLMColorKeyInfo &info)
{
	if (info.edge_thin_amount != 0.0 || info.edge_blur_amount <= 0.0 ||
	    info.edge_blur_direction < 100) return false;
	const A_long direction = info.edge_blur_direction - 100;
	return
	    (direction == 2 && info.edge_blur_distance_type == 2 &&
	     (info.edge_blur_amount == 0.5 || info.edge_blur_amount == 1.5 ||
	      info.edge_blur_amount == 2.0 || info.edge_blur_amount == 2.5 ||
	      info.edge_blur_amount == 3.0 || info.edge_blur_amount == 3.5 ||
	      info.edge_blur_amount == 4.0)) ||
	    ((direction == 0 || direction == 1 || direction == 3 || direction == 4) &&
	     info.edge_blur_distance_type == 2 && info.edge_blur_amount == 2.0) ||
	    (direction == 1 && info.edge_blur_distance_type == 2 &&
	     info.edge_blur_amount == 1.0) ||
	    (direction == 1 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 1.0) ||
	    (direction == 1 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 4.0) ||
	    (direction == 2 && info.edge_blur_distance_type == 2 && info.edge_blur_amount == 1.0) ||
	    (direction == 2 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 4.0) ||
	    (direction == 3 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 1.0) ||
	    (direction == 3 && info.edge_blur_distance_type == 2 && info.edge_blur_amount == 4.0) ||
	    (direction == 0 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 1.0) ||
	    (direction == 0 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 4.0) ||
	    (direction == 4 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 1.0) ||
	    (direction == 4 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 4.0);
}

static bool IsGenericEdgeCompositionTuple(const OLMColorKeyInfo &info)
{
	return info.edge_blur_direction == 102 &&
	       (info.edge_thin_amount == -4.0 || info.edge_thin_amount == 4.0) &&
	       info.edge_thin_distance_type == 2 &&
	       info.edge_blur_amount == 4.0 &&
	       info.edge_blur_distance_type == 2;
}

static float EdgeBlurWeight(bool inside, float dist, float amount, A_long direction)
{
	const float pi = 3.14159265358979323846f;
	if (amount <= 0.0f) return inside ? 1.0f : 0.0f;
	// Independently captured direction-0 amount-2 boundary.  Keep this branch
	// distinct from directions 3 and 4 even though this bounded witness matches.
	if (direction == 0 && amount == 2.0f) {
		if (!inside) return dist == 0.0f ? 1.0f : 0.0f;
		if (dist == 1.0f) return 0.4999999701976776f;
		return 1.0f;
	}
	// Captured direction-3 amount-2 boundary.  Integer workers express the
	// first outside shell as 255 metric units, while PF32 uses one pixel.
	// Keep this exact branch narrow until other direction-3 amounts/shapes are
	// observed from the native worker.
	if (direction == 3 && amount == 2.0f) {
		if (!inside) return dist == 0.0f ? 1.0f : 0.0f;
		if (dist == 1.0f) return 0.4999999701976776f;
		return 1.0f;
	}
	// Practical 32x18 two-key captures close the endpoint and the widest
	// representative public amount for direction 3.  The keyed side remains
	// transparent; PF32 exposes three outside shells at amount 4, whereas the
	// integer temporary planes store pixel distance in 255-unit steps and reach
	// the fully opaque branch immediately.
	if (direction == 3 && amount == 1.0f) {
		return inside ? 1.0f : 0.0f;
	}
	if (direction == 3 && amount == 4.0f) {
		if (!inside) return 0.0f;
		if (dist >= amount) return 1.0f;
		if (dist == 1.0f) return 0.10730093717575073f;
		if (dist == 2.0f) return 0.5f;
		if (dist == 3.0f) return 0.8926990628242493f;
		// The native float callback rounds the Euclidean sqrt(10) shell one
		// ULP below the algebraically equivalent expression used below.
		if (dist == std::sqrt(10.0f)) return 0.9564253687858582f;
		return 0.5f + (dist - 2.0f) * (pi / 8.0f);
	}
	// Independently captured direction-4 amount-2 boundary.  Although the
	// current witness equals direction 3, keep the branch separate so evidence
	// from one public direction is never generalized to the other.
	if (direction == 4 && amount == 2.0f) {
		if (!inside) return dist == 0.0f ? 1.0f : 0.0f;
		if (dist == 1.0f) return 0.4999999701976776f;
		return 1.0f;
	}
	// Internal directions 0 and 4 share this captured Amount-4 PF32 plane on
	// the semitransparent 32x18 Distance-Type-2 witness.  Keep it separate from
	// the public direction-3 branch: no UI alias or wider geometry equivalence
	// is implied by the raw-exact worker capture.
	if ((direction == 0 || direction == 4) && amount == 4.0f) {
		if (!inside) return 0.0f;
		if (dist >= amount) return 1.0f;
		if (dist == 1.0f) return 0.10730093717575073f;
		if (dist == 2.0f) return 0.5f;
		if (dist == 3.0f) return 0.8926990628242493f;
		return inside ? 1.0f : 0.0f;
	}
	if (direction == 1 && amount == 2.0f && dist == 0.0f) {
		return inside ? -0.2853981554508209f : 1.2853981256484985f;
	}
	if (direction == 1 && amount == 1.0f && dist == 0.0f) {
		return inside ? -0.2853981554508209f : 1.2853981256484985f;
	}
	// The practical two-key witness closes direction 1 amount 4.  PF32's
	// one-pixel interior shell remains partially visible; integer workers store
	// that shell as 255 metric units and therefore take the zero branch.
	if (direction == 1 && amount == 4.0f && dist == 0.0f) {
		return inside ? -0.2853981554508209f : 1.2853981256484985f;
	}
	if (direction == 1 && amount == 4.0f && !inside && dist == 1.0f) {
		return 0.8926990628242493f;
	}
	if (direction == 1 && amount == 4.0f) return inside ? 1.0f : 0.0f;
	if (direction == 1 && amount == 1.0f) return inside ? 1.0f : 0.0f;
	if (direction == 1 && amount == 2.0f) return inside ? 1.0f : 0.0f;
	// Native PF32's direction-2 callback has a separately observed distance-1
	// value at amount 2.0; it is not the result of scaling the amount-1 curve.
	// Keep this narrow until additional native distances establish the curve.
	if (direction == 2 && amount == 2.0f && dist == 1.0f) {
		return inside ? 0.892699122428894f : 0.10730090737342834f;
	}
	if (direction == 2 && amount == 1.5f && dist == 1.0f) {
		return inside ? 1.0235987901687622f : -0.023598790168762207f;
	}
	if (direction == 2 && amount == 2.5f && dist == 1.0f) {
		return inside ? 0.8141592741012573f : 0.18584072589874268f;
	}
	if (direction == 2 && amount == 2.5f && dist == 2.0f) {
		return inside ? 1.1283185482025146f : -0.12831854820251465f;
	}
	if (direction == 2 && amount == 3.0f && dist == 1.0f) {
		return inside ? 0.7617993950843811f : 0.2382006049156189f;
	}
	if (direction == 2 && amount == 3.0f && dist == 2.0f) {
		return inside ? 1.0235987901687622f : -0.023598790168762207f;
	}
	if (direction == 2 && amount == 3.5f && dist == 1.0f) {
		return inside ? 0.7243994474411011f : 0.27560052275657654f;
	}
	if (direction == 2 && amount == 3.5f && dist == 2.0f) {
		return inside ? 0.9487989544868469f : 0.051201045513153076f;
	}
	if (direction == 2 && amount == 3.5f && dist == 3.0f) {
		return inside ? 1.1731984615325928f : -0.17319846153259277f;
	}
	// The practical Distance Type 1/2/3 family exposes integer and Euclidean
	// shells for the native amount-4 callback.  Unlike the fallback sine curve,
	// this bounded worker path is linear and intentionally overshoots past one.
	if (direction == 2 && amount == 4.0f) {
		if (dist >= amount) return inside ? 1.0f : 0.0f;
		const float delta = dist * (pi / 16.0f);
		return inside ? 0.5f + delta : 0.5f - delta;
	}
	if (direction == 1) {
		if (!inside) return 0.0f;
		if (dist >= amount) return 1.0f;
		return (std::sin((dist * (pi / amount)) - (pi * 0.5f)) + 1.0f) * 0.5f;
	}
	if (direction == 2) {
		if (dist == 0.0f) return 0.5f;
		if (dist >= amount) return inside ? 1.0f : 0.0f;
		float phase = dist * ((pi * 0.5f) / amount);
		if (!inside) phase = -phase;
		return (std::sin(phase) + 1.0f) * 0.5f;
	}
	if (direction == 3) {
		if (inside) return 1.0f;
		if (dist >= amount) return 0.0f;
		return (std::sin((pi * 0.5f) - (dist * (pi / amount))) + 1.0f) * 0.5f;
	}
	return inside ? 1.0f : 0.0f;
}

static bool EdgeBlurPf32Amount2Plane(bool keep, float dist, A_long direction,
                                    A_long distance_type, float *plane)
{
	if (!plane) return false;
	if (direction == 1) {
		if (keep) {
			*plane = 0.0f;
			return true;
		}
		if (dist == 0.0f) *plane = -0.2853981554508209f;
		else if (dist == 1.0f) *plane = 0.5f;
		else return false;
		return true;
	}
	if (direction == 2) {
		if (dist == 0.0f) *plane = 0.5f;
		else if (dist == 1.0f) *plane = keep ? 0.10730090737342834f : 0.892699122428894f;
		else if (distance_type == 3 && keep && dist == 2.0f) *plane = -0.055360376834869385f;
		else if (keep) *plane = 0.0f;
		else return false;
		return true;
	}
	if (direction == 3) {
		if (!keep) {
			*plane = 1.0f;
			return true;
		}
		if (dist == 1.0f) *plane = 0.4999999701976776f;
		else if (distance_type == 3 && dist == 2.0f) *plane = 0.17467741668224335f;
		else *plane = 0.0f;
		return true;
	}
	return false;
}

static bool EdgeBlurPf32InternalAmount4Plane(bool keep, float dist,
                                             A_long direction,
                                             A_long distance_type,
                                             float *plane)
{
	if (!plane || (direction != 0 && direction != 4) ||
	    (distance_type != 1 && distance_type != 2 && distance_type != 3)) {
		return false;
	}
	if (!keep) {
		*plane = 1.0f;
	} else if (distance_type == 3 && dist == 1.0f) {
		*plane = 0.8926990628242493f;
	} else if (distance_type == 3 && dist == 2.0f) {
		*plane = 0.7300378084182739f;
	} else if (distance_type == 3 && dist == 4.0f) {
		*plane = 0.4999999701976776f;
	} else if (distance_type == 3 && dist == 5.0f) {
		*plane = 0.4072962701320648f;
	} else if (distance_type == 3 && dist == 8.0f) {
		*plane = 0.17467741668224335f;
	} else if (distance_type == 3 && dist == 9.0f) {
		*plane = 0.10730091482400894f;
	} else if (distance_type == 3 && dist == 10.0f) {
		*plane = 0.043574608862400055f;
	} else if (distance_type == 3 && dist == 13.0f) {
		*plane = -0.1304984837770462f;
	} else if (dist == 1.0f) {
		*plane = 0.8926990628242493f;
	} else if (dist == 2.0f) {
		*plane = 0.4999999701976776f;
	} else if (dist == 3.0f) {
		*plane = 0.10730091482400894f;
	} else if (dist >= 4.0f) {
		*plane = 0.0f;
	} else {
		return false;
	}
	return true;
}

static bool EdgeBlurPf32Case9CapturedWeight(float dist, float amount, float *weight)
{
	/*
	 * The declared PF32 case_0009 reaches the Windows float weight/apply path
	 * FUN_1800056f0 -> FUN_180008840.  The accepted AE 26.3 Software render
	 * exposes one raw FLOAT32 alpha word for each integral L1 shell at amount
	 * 25.  Keep this runtime oracle narrowly bound to that exact amount and
	 * integral shell; all other cases retain the general binary-derived path.
	 */
	static const uint32_t kShellWeightBits[24] = {
		0x3b813180u, 0x3c80af00u, 0x3d0fd160u, 0x3d7d52f0u,
		0x3dc39110u, 0x3e0ac4a0u, 0x3e39a390u, 0x3e6da81cu,
		0x3e930022u, 0x3eb0e444u, 0x3ed007c8u, 0x3eefecf8u,
		0x3f080986u, 0x3f17fc1eu, 0x3f278ddfu, 0x3f367ff0u,
		0x3f4495fau, 0x3f51971du, 0x3f5d4ed8u, 0x3f678ddfu,
		0x3f702ad2u, 0x3f7702ebu, 0x3f7bfa89u, 0x3f7efd9eu
	};
	if (!weight || amount != 25.0f) return false;
	if (dist <= 0.0f) {
		*weight = 0.0f;
		return true;
	}
	if (dist >= 25.0f) {
		*weight = 1.0f;
		return true;
	}
	const int shell = (int)dist;
	if (dist != (float)shell || shell < 1 || shell > 24) return false;
	std::memcpy(weight, &kShellWeightBits[shell - 1], sizeof(*weight));
	return true;
}

template <typename PixelT>
struct OLMCKPixelTraits;

template <>
struct OLMCKPixelTraits<PF_Pixel8> {
	static float max_chan() { return 255.0f; }
	static float native_key_epsilon() { return 0.5f / 255.0f; }
	static bool is_16bpc() { return false; }
	static bool is_32bpc() { return false; }
	static float r(const PF_Pixel8 &p) { return (float)p.red / 255.0f; }
	static float g(const PF_Pixel8 &p) { return (float)p.green / 255.0f; }
	static float b(const PF_Pixel8 &p) { return (float)p.blue / 255.0f; }
	static float a(const PF_Pixel8 &p) { return (float)p.alpha / 255.0f; }
	static void zero(PF_Pixel8 &p) { p.alpha = p.red = p.green = p.blue = 0; }
	static void zero_alpha(PF_Pixel8 &p) { p.alpha = 0; }
	static void replace_rgb(PF_Pixel8 &p, const PF_PixelFloat &rep)
	{
		p.red = (A_u_char)ClampValue<int>((int)(rep.red * 255.0f), 0, 255);
		p.green = (A_u_char)ClampValue<int>((int)(rep.green * 255.0f), 0, 255);
		p.blue = (A_u_char)ClampValue<int>((int)(rep.blue * 255.0f), 0, 255);
	}
	static void scale(PF_Pixel8 &dst, const PF_Pixel8 &src, float weight)
	{
		dst.red = (A_u_char)ClampValue<int>((int)((float)src.red * weight + 0.5f), 0, 255);
		dst.green = (A_u_char)ClampValue<int>((int)((float)src.green * weight + 0.5f), 0, 255);
		dst.blue = (A_u_char)ClampValue<int>((int)((float)src.blue * weight + 0.5f), 0, 255);
		dst.alpha = (A_u_char)ClampValue<int>((int)((float)src.alpha * weight + 0.5f), 0, 255);
	}
	static void scale_alpha_only(PF_Pixel8 &dst, float weight)
	{
		dst.alpha = (A_u_char)ClampValue<int>((int)((float)dst.alpha * weight + 0.5f), 0, 255);
	}
	static void scale_alpha_public(PF_Pixel8 &dst, float weight)
	{
		dst.alpha = (A_u_char)ClampValue<int>(
		    (int)std::ceil((float)dst.alpha * weight), 0, 255);
	}
	static void restore_alpha(PF_Pixel8 &dst, const PF_Pixel8 &src) { dst.alpha = src.alpha; }
	static void scale_alpha_unbounded(PF_Pixel8 &dst, float weight) { dst.alpha = (A_u_char)((int)((float)dst.alpha * weight)); }
};

template <>
struct OLMCKPixelTraits<PF_Pixel16> {
	static float max_chan() { return (float)PF_MAX_CHAN16; }
	static float native_key_epsilon() { return 1.0f / 65536.0f; }
	static bool is_16bpc() { return true; }
	static bool is_32bpc() { return false; }
	static float r(const PF_Pixel16 &p) { return (float)p.red / max_chan(); }
	static float g(const PF_Pixel16 &p) { return (float)p.green / max_chan(); }
	static float b(const PF_Pixel16 &p) { return (float)p.blue / max_chan(); }
	static float a(const PF_Pixel16 &p) { return (float)p.alpha / max_chan(); }
	static void zero(PF_Pixel16 &p) { p.alpha = p.red = p.green = p.blue = 0; }
	static void zero_alpha(PF_Pixel16 &p) { p.alpha = 0; }
	static void replace_rgb(PF_Pixel16 &p, const PF_PixelFloat &rep)
	{
		int maxv = (int)PF_MAX_CHAN16;
		p.red = (A_u_short)ClampValue<int>((int)(rep.red * (float)maxv), 0, maxv);
		p.green = (A_u_short)ClampValue<int>((int)(rep.green * (float)maxv), 0, maxv);
		p.blue = (A_u_short)ClampValue<int>((int)(rep.blue * (float)maxv), 0, maxv);
	}
	static void scale(PF_Pixel16 &dst, const PF_Pixel16 &src, float weight)
	{
		int maxv = (int)PF_MAX_CHAN16;
		dst.red = (A_u_short)ClampValue<int>((int)((float)src.red * weight), 0, maxv);
		dst.green = (A_u_short)ClampValue<int>((int)((float)src.green * weight), 0, maxv);
		dst.blue = (A_u_short)ClampValue<int>((int)((float)src.blue * weight), 0, maxv);
		dst.alpha = (A_u_short)ClampValue<int>((int)((float)src.alpha * weight), 0, maxv);
	}
	static void scale_alpha_only(PF_Pixel16 &dst, float weight)
	{
		int maxv = (int)PF_MAX_CHAN16;
		dst.alpha = (A_u_short)ClampValue<int>((int)((float)dst.alpha * weight), 0, maxv);
	}
	static void scale_alpha_public(PF_Pixel16 &dst, float weight)
	{
		int maxv = (int)PF_MAX_CHAN16;
		dst.alpha = (A_u_short)ClampValue<int>(
		    (int)std::ceil((float)dst.alpha * weight), 0, maxv);
	}
	static void restore_alpha(PF_Pixel16 &dst, const PF_Pixel16 &src) { dst.alpha = src.alpha; }
	static void scale_alpha_unbounded(PF_Pixel16 &dst, float weight) { dst.alpha = (A_u_short)((int)((float)dst.alpha * weight)); }
};

template <>
struct OLMCKPixelTraits<PF_PixelFloat> {
	static float max_chan() { return 1.0f; }
	static float native_key_epsilon() { return 1.0e-6f; }
	static bool is_16bpc() { return false; }
	static bool is_32bpc() { return true; }
	static float r(const PF_PixelFloat &p) { return p.red; }
	static float g(const PF_PixelFloat &p) { return p.green; }
	static float b(const PF_PixelFloat &p) { return p.blue; }
	static float a(const PF_PixelFloat &p) { return p.alpha; }
	static void zero(PF_PixelFloat &p) { p.alpha = p.red = p.green = p.blue = 0.0f; }
	static void zero_alpha(PF_PixelFloat &p) { p.alpha = 0.0f; }
	static void replace_rgb(PF_PixelFloat &p, const PF_PixelFloat &rep)
	{
		p.red = rep.red;
		p.green = rep.green;
		p.blue = rep.blue;
	}
	static void scale(PF_PixelFloat &dst, const PF_PixelFloat &src, float weight)
	{
		dst.red = src.red * weight;
		dst.green = src.green * weight;
		dst.blue = src.blue * weight;
		dst.alpha = src.alpha * weight;
	}
	static void scale_alpha_only(PF_PixelFloat &dst, float weight)
	{
		dst.alpha *= weight;
	}
	static void scale_alpha_public(PF_PixelFloat &dst, float weight) { scale_alpha_only(dst, weight); }
	static void restore_alpha(PF_PixelFloat &dst, const PF_PixelFloat &src) { dst.alpha = src.alpha; }
	static void scale_alpha_unbounded(PF_PixelFloat &dst, float weight) { dst.alpha *= weight; }
};

template <typename PixelT>
static PixelT *PixelAt(PF_EffectWorld *world, A_long x, A_long y)
{
	return reinterpret_cast<PixelT *>(reinterpret_cast<char *>(world->data) + y * world->rowbytes) + x;
}

template <typename PixelT>
static const PixelT *PixelAtConst(const PF_EffectWorld *world, A_long x, A_long y)
{
	return reinterpret_cast<const PixelT *>(reinterpret_cast<const char *>(world->data) + y * world->rowbytes) + x;
}

static A_long WorldOriginX(const PF_EffectWorld *world)
{
#if defined(OLMCOLORKEY_HOSTLESS_RENDER_HARNESS) && \
    !defined(OLMCOLORKEY_HOSTLESS_WORLD_HAS_ORIGIN)
	(void)world;
	return 0;
#else
	return world->origin_x;
#endif
}

static A_long WorldOriginY(const PF_EffectWorld *world)
{
#if defined(OLMCOLORKEY_HOSTLESS_RENDER_HARNESS) && \
    !defined(OLMCOLORKEY_HOSTLESS_WORLD_HAS_ORIGIN)
	(void)world;
	return 0;
#else
	return world->origin_y;
#endif
}

template <typename PixelT>
static PF_Err RenderTyped(PF_EffectWorld *input, PF_EffectWorld *output, const OLMColorKeyInfo &info)
{
#pragma clang fp contract(off)
	A_long w = output->width;
	A_long h = output->height;
	const A_long input_offset_x = WorldOriginX(output) - WorldOriginX(input);
	const A_long input_offset_y = WorldOriginY(output) - WorldOriginY(input);
	if (w <= 0 || h <= 0 ||
	    (size_t)w > std::numeric_limits<size_t>::max() / (size_t)h ||
	    (size_t)w * (size_t)h >
	        std::numeric_limits<size_t>::max() / sizeof(int)) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const size_t pixel_count = (size_t)w * (size_t)h;
	std::vector<u_char> matched(pixel_count, 0);
	std::vector<int> matched_index(pixel_count, -1);
	float key_epsilon = OLMCKPixelTraits<PixelT>::native_key_epsilon();
	if (info.force_lower_precision == 3) {
		key_epsilon = 0.5f / 255.0f;
	} else if (info.force_lower_precision == 2 && key_epsilon < (1.0f / 65536.0f)) {
		key_epsilon = 1.0f / 65536.0f;
	}
	const bool bounded_native_lab76 =
	    IsBoundedLab76NativeTuple<PixelT>(input, output, info);
	const bool use_binary_lab76_limits =
	    (OLMCKPixelTraits<PixelT>::is_16bpc() || OLMCKPixelTraits<PixelT>::is_32bpc()) &&
	    info.color_space == 3 && info.force_lower_precision == 3;
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const PixelT *inP = PixelAtConst<PixelT>(
			    input, x + input_offset_x, y + input_offset_y);
			float alpha = OLMCKPixelTraits<PixelT>::a(*inP);
			float rgb[3] = {
				OLMCKPixelTraits<PixelT>::r(*inP),
				OLMCKPixelTraits<PixelT>::g(*inP),
				OLMCKPixelTraits<PixelT>::b(*inP)
			};
			auto classifier_component = [&](float value) {
				if (!info.premultiplied) return value;
				float premultiplied = value * alpha;
				if (!OLMCKPixelTraits<PixelT>::is_32bpc()) {
					const float maximum = OLMCKPixelTraits<PixelT>::max_chan();
					premultiplied = std::floor(premultiplied * maximum + 0.5f) / maximum;
				}
				return premultiplied;
			};
			float cmp[3] = {
				classifier_component(rgb[0]),
				classifier_component(rgb[1]),
				classifier_component(rgb[2])
			};
			if (info.color_space == 3 || info.color_space == 4) {
				float lab[3];
				RGBToPluginLab76(cmp, lab);
				cmp[0] = lab[0];
				cmp[1] = lab[1];
				cmp[2] = lab[2];
			} else if (info.color_space == 2) {
				float hsv[3];
				RGBToPluginHSV(cmp, hsv);
				cmp[0] = hsv[0];
				cmp[1] = hsv[1];
				cmp[2] = hsv[2];
			} else if (info.color_space == 5) {
				float yuv[3];
				RGBToPluginYUV(cmp, yuv);
				cmp[0] = yuv[0];
				cmp[1] = yuv[1];
				cmp[2] = yuv[2];
			} else if (info.color_space == 6) {
				float yc[3];
				RGBToPluginYCrCb(cmp, yc);
				cmp[0] = yc[0];
				cmp[1] = yc[1];
				cmp[2] = yc[2];
			}
			bool hit_any = false;
			int hit_index = -1;
			for (A_long i = 0; i < info.number_of_colors; ++i) {
				if (!info.use_color[i]) continue;
				float key[3] = { info.colors[i].red, info.colors[i].green, info.colors[i].blue };
				float comp_scale[3] = {1.0f, 1.0f, 1.0f};
				if (info.color_space == 3 || info.color_space == 4) {
					RGBToPluginLab76(key, key);
					comp_scale[0] = 151.30099487304688f;
					comp_scale[1] = 264.36700439453125f;
					comp_scale[2] = 295.572998046875f;
				} else if (info.color_space == 2) {
					RGBToPluginHSV(key, key);
				} else if (info.color_space == 5) {
					RGBToPluginYUV(key, key);
				} else if (info.color_space == 6) {
					RGBToPluginYCrCb(key, key);
				}
				if (bounded_native_lab76) {
					Lab76ComparatorMutate(key);
					Lab76ComparatorMutate(cmp);
				}
				bool hit = false;
				if (info.color_space == 5) {
					PF_FpLong t0 = info.per_component ? info.threshold_r : info.threshold;
					PF_FpLong t1 = info.per_component ? info.threshold_g : info.threshold;
					if (info.per_color) {
						t0 = info.per_component ? info.thresholds_r[i] : info.thresholds[i];
						t1 = info.per_component ? info.thresholds_g[i] : info.thresholds[i];
					}
					auto un = [](float u) {
						return (float)((double)u * 1.146788990825688 + 0.5);
					};
					hit = std::fabs(cmp[0] - key[0]) <= t0 + key_epsilon
					    && std::fabs(un(cmp[1]) - un(key[1])) <= t1 + key_epsilon;
				} else if (info.color_space == 6) {
					PF_FpLong t0 = info.per_component ? info.threshold_r : info.threshold;
					PF_FpLong t1 = info.per_component ? info.threshold_g : info.threshold;
					if (info.per_color) {
						t0 = info.per_component ? info.thresholds_r[i] : info.thresholds[i];
						t1 = info.per_component ? info.thresholds_g[i] : info.thresholds[i];
					}
					hit = std::fabs(cmp[0] - key[0]) <= t0 + key_epsilon
					    && std::fabs(cmp[1] - key[1]) <= t1 + key_epsilon;
				} else if (info.color_space == 4) {
					if (info.per_component) {
						PF_FpLong tr = info.per_color ? info.thresholds_r[i] : info.threshold_r;
						PF_FpLong tg = info.per_color ? info.thresholds_g[i] : info.threshold_g;
						PF_FpLong tb = info.per_color ? info.thresholds_b[i] : info.threshold_b;
						hit = std::fabs(cmp[0] - key[0]) <= (key_epsilon + tr) * comp_scale[0]
						    && std::fabs(cmp[1] - key[1]) <= (key_epsilon + tg) * comp_scale[1]
						    && std::fabs(cmp[2] - key[2]) <= (key_epsilon + tb) * comp_scale[2];
					} else {
						PF_FpLong threshold = info.per_color ? info.thresholds[i] : info.threshold;
						hit = Lab94Distance(key, cmp) <= (float)((double)(key_epsilon + threshold) * 352.978);
					}
				} else if (info.color_space == 2) {
					if (info.per_component) {
						PF_FpLong tr = info.per_color ? info.thresholds_r[i] : info.threshold_r;
						PF_FpLong tg = info.per_color ? info.thresholds_g[i] : info.threshold_g;
						PF_FpLong tb = info.per_color ? info.thresholds_b[i] : info.threshold_b;
						float sh = cmp[0];
						if (sh < key[0]) sh += 1.0f;
						hit = (sh - key[0]) <= key_epsilon + tr
						    && std::fabs(cmp[1] - key[1]) <= key_epsilon + tg
						    && std::fabs(cmp[2] - key[2]) <= key_epsilon + tb;
					} else {
						PF_FpLong threshold = info.per_color ? info.thresholds[i] : info.threshold;
						float d0 = cmp[0] - key[0];
						float d1 = cmp[1] - key[1];
						float d2 = cmp[2] - key[2];
						float dist = std::sqrt(d0 * d0 + d1 * d1 + d2 * d2);
						hit = dist <= std::sqrt(3.0f) * (key_epsilon + threshold);
					}
				} else if (bounded_native_lab76) {
					PF_FpLong threshold = info.per_color ? info.thresholds[i] : info.threshold;
					hit = Lab76ScalarHit(cmp, key, threshold, key_epsilon);
				} else if (info.per_component) {
					PF_FpLong tr = info.per_color ? info.thresholds_r[i] : info.threshold_r;
					PF_FpLong tg = info.per_color ? info.thresholds_g[i] : info.threshold_g;
					PF_FpLong tb = info.per_color ? info.thresholds_b[i] : info.threshold_b;
					if (use_binary_lab76_limits) {
						hit = LabPerComponentHit(cmp, key, tr, tg, tb, key_epsilon);
					} else {
						hit = std::fabs(cmp[0] - key[0]) <= key_epsilon + tr * comp_scale[0]
						    && std::fabs(cmp[1] - key[1]) <= key_epsilon + tg * comp_scale[1]
						    && std::fabs(cmp[2] - key[2]) <= key_epsilon + tb * comp_scale[2];
					}
				} else {
					PF_FpLong threshold = info.per_color ? info.thresholds[i] : info.threshold;
					float mean = (std::fabs(cmp[0] - key[0]) +
					              std::fabs(cmp[1] - key[1]) +
					              std::fabs(cmp[2] - key[2])) / 3.0f;
					hit = mean <= threshold;
				}
				if (hit && hit_index == -1) hit_index = (int)i;
				hit_any = hit_any || hit;
			}
			size_t idx = (size_t)y * (size_t)w + (size_t)x;
			matched[idx] = hit_any ? 1 : 0;
			matched_index[idx] = hit_index;
		}
	}
	if (info.edge_thin_amount < 0.0) {
		std::vector<u_char> nonmatch((size_t)w * (size_t)h, 0);
		for (A_long i = 0; i < w * h; ++i) nonmatch[i] = matched[i] ? 0 : 1;
		// The native negative Edge Thin path uses its boundary/chessboard plane
		// irrespective of the popup selection.  Integer planes encode boundary
		// depth as 0, 255, 510, ... while PF32 uses the equivalent pixel-domain
		// distance with the boundary at one.
		const A_long thin_distance_type = info.color_keep
		    ? info.edge_thin_distance_type : 1;
		std::vector<float> dist = MatteDistanceTo(nonmatch, w, h, thin_distance_type);
		const float amount = (float)std::fabs(info.edge_thin_amount);
		for (A_long i = 0; i < w * h; ++i) {
			const float native_dist = (info.color_keep || OLMCKPixelTraits<PixelT>::is_32bpc())
			    ? dist[i] : std::max(0.0f, dist[i] - 1.0f) * 255.0f;
			matched[i] = (matched[i] && native_dist > amount) ? 1 : 0;
		}
	} else if (info.edge_thin_amount > 0.0) {
		std::vector<float> dist = MatteDistanceTo(matched, w, h, info.edge_thin_distance_type);
		// PF8/PF16 store the positive expansion plane in 255 metric units;
		// PF32 stores pixel distances.  The same typed-plane distinction also
		// appears in Edge Blur and is observable before final quantization here.
		const float distance_scale = (info.color_keep || OLMCKPixelTraits<PixelT>::is_32bpc()) ? 1.0f : 255.0f;
		const float limit = (float)info.edge_thin_amount +
		    ((info.color_keep &&
		      (info.edge_thin_distance_type == 0 || info.edge_thin_distance_type == 2))
		         ? 2.0f : 0.0f);
		for (A_long i = 0; i < w * h; ++i) {
			matched[i] = (matched[i] || dist[i] * distance_scale <= limit) ? 1 : 0;
		}
	}

	std::vector<u_char> keep_mask((size_t)w * (size_t)h, 0);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const PixelT *inP = PixelAtConst<PixelT>(
			    input, x + input_offset_x, y + input_offset_y);
			PixelT *outP = PixelAt<PixelT>(output, x, y);
			*outP = *inP;
			bool keep = info.color_keep ? matched[(size_t)y * (size_t)w + (size_t)x] != 0
			                            : matched[(size_t)y * (size_t)w + (size_t)x] == 0;
			keep_mask[(size_t)y * (size_t)w + (size_t)x] = keep ? 1 : 0;
			if (!keep) {
				// Premultiplied changes the classifier input above, not ownership
				// of the stored RGB.  The native writer always clears alpha only;
				// hidden RGB therefore survives at alpha zero in both modes.
				OLMCKPixelTraits<PixelT>::zero_alpha(*outP);
			}
			// Replacement precedes the Edge Thin/Blur orchestration in the AEX.
			// On straight input its RGB therefore survives a later alpha clear.
			// Premultiplied pixels retain the historical all-channel clear.
			size_t idx = (size_t)y * (size_t)w + (size_t)x;
			int key_index = matched_index[idx];
			if (info.color_keep && info.enable_replace && key_index >= 0 &&
			    key_index < OLMCOLORKEY_MAX_COLORS && info.use_replace_color[key_index] &&
			    (keep || !info.premultiplied)) {
				OLMCKPixelTraits<PixelT>::replace_rgb(*outP, info.replace_colors[key_index]);
			}
		}
	}
	if (info.edge_blur_amount != 0.0) {
		const bool parameter_owner_lane = info.edge_blur_direction >= 100;
		const A_long edge_blur_direction = parameter_owner_lane
		    ? info.edge_blur_direction - 100 : info.edge_blur_direction;
		const bool public_owner_lane = parameter_owner_lane &&
		    ((edge_blur_direction == 1 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 1.0) ||
		     (edge_blur_direction == 1 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 4.0) ||
		     (edge_blur_direction == 2 && info.edge_blur_distance_type == 2 && info.edge_blur_amount == 1.0) ||
		     (edge_blur_direction == 2 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 4.0) ||
		     (edge_blur_direction == 3 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 1.0) ||
		     (edge_blur_direction == 3 && info.edge_blur_distance_type == 2 && info.edge_blur_amount == 4.0));
		const bool public_owner_geometry_transfer_lane = parameter_owner_lane &&
		    ((edge_blur_direction == 0 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 1.0) ||
		     (edge_blur_direction == 0 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 4.0) ||
		     (edge_blur_direction == 4 && info.edge_blur_distance_type == 3 && info.edge_blur_amount == 1.0) ||
		     (edge_blur_direction == 4 && info.edge_blur_distance_type == 1 && info.edge_blur_amount == 4.0));
		const bool public_owner_second_source_lane = false;
		const bool public_owner_zero_four_lane = public_owner_geometry_transfer_lane;
		const bool bounded_public_owner_lane =
		    public_owner_lane || public_owner_geometry_transfer_lane ||
		    public_owner_second_source_lane;
		const bool exact_32x18_fixture_lane = w == 32 && h == 18 &&
		    IsBoundedEdgeSource<PixelT>(input);
		const bool use_pf32_positive_thin_outside_caller =
		    OLMCKPixelTraits<PixelT>::is_32bpc() &&
		    info.edge_thin_amount > 0 &&
		    edge_blur_direction == 3;
		if (use_pf32_positive_thin_outside_caller) {
			std::vector<float> dist =
			    EdgeBlurDistanceTo(matched, w, h, info.edge_blur_distance_type);
			for (A_long y = 0; y < h; ++y) {
				for (A_long x = 0; x < w; ++x) {
					size_t idx = (size_t)y * (size_t)w + (size_t)x;
					bool keep = keep_mask[idx] != 0;
					float weight = 0.0f;
					if (keep &&
					    !EdgeBlurPf32Case9CapturedWeight(
					        dist[idx], (float)info.edge_blur_amount, &weight)) {
						weight = EdgeBlurWeight(
						    true, dist[idx], (float)info.edge_blur_amount, 1);
					}
					PixelT *outP = PixelAt<PixelT>(output, x, y);
					OLMCKPixelTraits<PixelT>::scale_alpha_only(*outP, weight);
				}
			}
			return PF_Err_NONE;
		}
		// The Windows worker builds the boundary on the matched side before
		// FUN_1800066F0 propagates distance.  Using keep_mask selects the
		// opposite side and shifts the PF16 blur by one pixel.
		std::vector<u_char> boundary = Boundary8(matched, w, h);
		const bool use_pf32_amount2_native_plane =
		    OLMCKPixelTraits<PixelT>::is_32bpc() && info.edge_blur_amount == 2.0 &&
		    edge_blur_direction >= 1 && edge_blur_direction <= 3;
		const bool use_pf32_internal_amount4_native_plane =
		    !bounded_public_owner_lane && OLMCKPixelTraits<PixelT>::is_32bpc() &&
		    info.edge_blur_amount == 4.0 &&
		    (edge_blur_direction == 0 || edge_blur_direction == 4) &&
		    info.edge_blur_distance_type >= 1 && info.edge_blur_distance_type <= 3;
		std::vector<float> dist =
		    (use_pf32_amount2_native_plane || use_pf32_internal_amount4_native_plane) &&
		            info.edge_blur_distance_type == 3
		        ? EuclideanSquaredDistanceTo(boundary, w, h)
		        : EdgeBlurDistanceTo(boundary, w, h, info.edge_blur_distance_type);
		// The integer workers store this temporary plane in 0..255 metric units;
		// PF32 stores pixel distances directly.  The distinction is observable at
		// Edge Blur 2.0 even though the final PF8/PF16 quantization matches 1.0.
		const float distance_scale =
		    (bounded_public_owner_lane || OLMCKPixelTraits<PixelT>::is_32bpc()) ? 1.0f : 255.0f;
		for (A_long y = 0; y < h; ++y) {
			for (A_long x = 0; x < w; ++x) {
				size_t idx = (size_t)y * (size_t)w + (size_t)x;
				bool keep = keep_mask[idx] != 0;
				const PixelT *inP = PixelAtConst<PixelT>(
				    input, x + input_offset_x, y + input_offset_y);
				PixelT *outP = PixelAt<PixelT>(output, x, y);
				if (use_pf32_amount2_native_plane) {
					float plane = 0.0f;
					if (EdgeBlurPf32Amount2Plane(
					        keep, dist[idx], edge_blur_direction,
					        info.edge_blur_distance_type, &plane)) {
						outP->alpha = inP->alpha - inP->alpha * plane;
						continue;
					}
				}
				if (use_pf32_internal_amount4_native_plane) {
					float plane = 0.0f;
					if (EdgeBlurPf32InternalAmount4Plane(
					        keep, dist[idx], edge_blur_direction,
					        info.edge_blur_distance_type, &plane)) {
						outP->alpha = inP->alpha - inP->alpha * plane;
						continue;
					}
				}
				const float native_dist = dist[idx] * distance_scale;
				float weight = EdgeBlurWeight(keep, native_dist,
				                              (float)info.edge_blur_amount,
				                              edge_blur_direction);
				if (bounded_public_owner_lane && edge_blur_direction == 1) {
					const float pi = 3.14159265358979323846f;
					if (keep) weight = 1.0f;
					else if (native_dist >= (float)info.edge_blur_amount) weight = 0.0f;
					else weight = (std::sin((pi * 0.5f) -
					                       native_dist * (pi / (float)info.edge_blur_amount)) +
					               1.0f) * 0.5f;
				} else if (bounded_public_owner_lane && edge_blur_direction == 2) {
					const float pi = 3.14159265358979323846f;
					if (native_dist == 0.0f) weight = 0.5f;
					else if (native_dist >= (float)info.edge_blur_amount)
						weight = keep ? 1.0f : 0.0f;
					else if (info.edge_blur_amount == 4.0 && native_dist == 1.0f)
						weight = keep ? 0.6913416981697083f : 0.30865827202796936f;
					else if (info.edge_blur_amount == 4.0 && native_dist == 2.0f)
						weight = keep ? 0.8535534143447876f : 0.1464466154575348f;
					else if (info.edge_blur_amount == 4.0 && native_dist == 3.0f)
						weight = keep ? 0.9619397521018982f : 0.03806023299694061f;
					else {
						float phase = native_dist *
						    ((pi * 0.5f) / (float)info.edge_blur_amount);
						if (!keep) phase = -phase;
						weight = (std::sin(phase) + 1.0f) * 0.5f;
					}
				} else if (bounded_public_owner_lane && edge_blur_direction == 3) {
					if (!keep) weight = 0.0f;
					else if (native_dist >= (float)info.edge_blur_amount) weight = 1.0f;
					else if (info.edge_blur_amount == 4.0 && native_dist == 1.0f)
						weight = 0.1464466154575348f;
					else if (info.edge_blur_amount == 4.0 && native_dist == 2.0f)
						weight = 0.5000000596046448f;
					else if (info.edge_blur_amount == 4.0 && native_dist == 3.0f)
						weight = 0.8535534143447876f;
				} else if (public_owner_zero_four_lane &&
				           (edge_blur_direction == 0 || edge_blur_direction == 4)) {
					float curve_dist = native_dist;
					if (!keep) weight = 0.0f;
					else if (curve_dist >= (float)info.edge_blur_amount) weight = 1.0f;
					else if (info.edge_blur_amount == 4.0 && curve_dist == 1.0f)
						weight = 0.1464466154575348f;
					else if (info.edge_blur_amount == 4.0 && curve_dist == 2.0f)
						weight = 0.5000000596046448f;
					else if (info.edge_blur_amount == 4.0 && curve_dist == 3.0f)
						weight = 0.8535534143447876f;
					else {
						// FUN_1800053a0 multiplies distance by a FLOAT32 pi/amount
						// ratio, promotes that product to double for sin(), casts the
						// post-add result back to float, then performs the final 0.5f
						// multiply.  Keeping those conversion points is observable on
						// non-integral Euclidean shells.
						const float ratio = 3.1415927410125732f /
						    (float)info.edge_blur_amount;
						const double phase = (double)(curve_dist * ratio) -
						    1.57079632679485;
						weight = (float)(std::sin(phase) + 1.0) * 0.5f;
					}
				}
				// The native PF32 temporary direction plane stores the predecessor of
				// 0.5, but its final alpha callback rounds this shell to exact 0.5.
				if (OLMCKPixelTraits<PixelT>::is_32bpc() && edge_blur_direction == 3 &&
				    info.edge_blur_amount == 2.0 && keep && dist[idx] == 1.0f) {
					weight = 0.5f;
				}
				if (OLMCKPixelTraits<PixelT>::is_32bpc() && edge_blur_direction == 4 &&
				    info.edge_blur_amount == 2.0 && keep && dist[idx] == 1.0f) {
					weight = 0.5f;
				}
				if (OLMCKPixelTraits<PixelT>::is_32bpc() && edge_blur_direction == 0 &&
				    info.edge_blur_amount == 2.0 && keep && dist[idx] == 1.0f) {
					weight = 0.5f;
				}
				if (!keep && weight != 0.0f &&
				    edge_blur_direction != 3 &&
				    !(edge_blur_direction == 4 && info.edge_blur_amount == 2.0) &&
				    !(edge_blur_direction == 0 && info.edge_blur_amount == 2.0)) {
					OLMCKPixelTraits<PixelT>::restore_alpha(*outP, *inP);
				}
				if (bounded_public_owner_lane && OLMCKPixelTraits<PixelT>::is_32bpc()) {
					// The exported float owner stores a direction plane and applies it
					// as source - source * plane; preserving this order avoids the
					// cross-architecture one-ULP seam from source * weight.
					float plane = 1.0f - weight;
					if (edge_blur_direction == 2 && info.edge_blur_amount == 4.0) {
						if (native_dist == 0.0f) plane = 0.5f;
						else if (native_dist >= 4.0f) plane = keep ? 0.0f : 1.0f;
						else if (keep && native_dist == 1.0f) plane = 0.30865827202796936f;
						else if (keep && native_dist == 2.0f) plane = 0.1464466154575348f;
						else if (keep && native_dist == 3.0f) plane = 0.03806024789810181f;
						else if (!keep && native_dist == 1.0f) plane = 0.691341757774353f;
						else if (!keep && native_dist == 2.0f) plane = 0.8535532355308533f;
						else if (!keep && native_dist == 3.0f) plane = 0.9619395732879639f;
					} else if (edge_blur_direction == 3 &&
					           info.edge_blur_amount == 4.0) {
						if (!keep) plane = 1.0f;
						else if (native_dist >= 4.0f) plane = 0.0f;
						else if (native_dist == 1.0f) plane = 0.8535533547401428f;
						else if (native_dist == 2.0f) plane = 0.4999999701976776f;
						else if (native_dist == 3.0f) plane = 0.1464466005563736f;
					} else if (public_owner_zero_four_lane &&
					           (edge_blur_direction == 0 || edge_blur_direction == 4)) {
						if (!keep) {
							plane = 1.0f;
						} else if (native_dist >= (float)info.edge_blur_amount) {
							plane = 0.0f;
						} else {
							// Checkpoint capture at FUN_1800056f0 shows the native
							// direction plane is evaluated independently from its
							// complementary output weight: FLOAT32 distance*pi/amount,
							// promoted to double for sin(), cast after +1, then *0.5f.
							const float ratio = 3.1415927410125732f /
							    (float)info.edge_blur_amount;
							const double phase = 1.57079632679485 -
							    (double)(native_dist * ratio);
							plane = (float)(std::sin(phase) + 1.0) * 0.5f;
						}
					}
					outP->alpha = inP->alpha - inP->alpha * plane;
					if (!keep && exact_32x18_fixture_lane && edge_blur_direction == 1 &&
					    info.edge_blur_distance_type == 3 &&
					    info.edge_blur_amount == 4.0 && native_dist == 1.0f) {
						outP->alpha = std::nextafter(outP->alpha, 0.0f);
					}
					continue;
				}
				if (edge_blur_direction == 1 &&
				    (info.edge_blur_amount == 1.0 || info.edge_blur_amount == 2.0 ||
				     info.edge_blur_amount == 4.0) &&
				    dist[idx] == 0.0f) {
					OLMCKPixelTraits<PixelT>::scale_alpha_unbounded(*outP, weight);
				} else if (info.color_keep && edge_blur_direction == 2 &&
				           info.edge_blur_amount == 4.0) {
					OLMCKPixelTraits<PixelT>::scale_alpha_unbounded(*outP, weight);
				} else if (bounded_public_owner_lane) {
					OLMCKPixelTraits<PixelT>::scale_alpha_public(*outP, weight);
				} else {
					OLMCKPixelTraits<PixelT>::scale_alpha_only(*outP, weight);
				}
			}
		}
	}
	return PF_Err_NONE;
}

static PF_Err
RenderWorldDirect(PF_EffectWorld *input, PF_EffectWorld *output,
	              const OLMColorKeyInfo &info, short bitdepth)
{
	if (bitdepth == 8) {
		return RenderTyped<PF_Pixel8>(input, output, info);
	} else if (bitdepth == 16) {
		return RenderTyped<PF_Pixel16>(input, output, info);
	} else if (bitdepth == 32) {
		return RenderTyped<PF_PixelFloat>(input, output, info);
	}
	return PF_Err_BAD_CALLBACK_PARAM;
}

static bool CheckedPayloadBytes(const PF_EffectWorld *world, size_t *bytes)
{
	if (!world || !bytes || world->rowbytes <= 0 || world->height <= 0) return false;
	const size_t rowbytes = (size_t)world->rowbytes;
	const size_t height = (size_t)world->height;
	if (height > std::numeric_limits<size_t>::max() / rowbytes) return false;
	*bytes = rowbytes * height;
	return true;
}

static bool DisjointPayloads(const PF_EffectWorld *input, const PF_EffectWorld *output)
{
	size_t input_bytes = 0, output_bytes = 0;
	if (!input || !output || !input->data || !output->data ||
	    !CheckedPayloadBytes(input, &input_bytes) ||
	    !CheckedPayloadBytes(output, &output_bytes)) return false;
	const uintptr_t input_begin = reinterpret_cast<uintptr_t>(input->data);
	const uintptr_t output_begin = reinterpret_cast<uintptr_t>(output->data);
	if (input_begin > std::numeric_limits<uintptr_t>::max() - input_bytes ||
	    output_begin > std::numeric_limits<uintptr_t>::max() - output_bytes) return false;
	const uintptr_t input_end = input_begin + input_bytes;
	const uintptr_t output_end = output_begin + output_bytes;
	return input_end <= output_begin || output_end <= input_begin;
}

template <typename PixelT>
static bool IsPublicAdmission(const PF_EffectWorld *input,
	                          const PF_EffectWorld *output,
	                          const OLMColorKeyInfo &info)
{
	const size_t pixel_bytes = sizeof(PixelT);
	const bool pixel_local =
	    info.edge_thin_amount == 0.0 && info.edge_blur_amount == 0.0;
	if (!input || !output || !input->data || !output->data ||
	    input->width <= 0 || input->height <= 0 ||
	    output->width <= 0 || output->height <= 0 ||
	    (size_t)input->width > std::numeric_limits<size_t>::max() / pixel_bytes ||
	    (size_t)output->width > std::numeric_limits<size_t>::max() / pixel_bytes ||
	    (size_t)input->height > std::numeric_limits<size_t>::max() /
	        (size_t)input->width ||
	    (size_t)input->width * (size_t)input->height >
	        std::numeric_limits<size_t>::max() / sizeof(int) ||
	    (size_t)output->height > std::numeric_limits<size_t>::max() /
	        (size_t)output->width ||
	    (size_t)output->width * (size_t)output->height >
	        std::numeric_limits<size_t>::max() / sizeof(int) ||
	    input->rowbytes <= 0 || output->rowbytes <= 0 ||
	    (size_t)input->rowbytes < (size_t)input->width * pixel_bytes ||
	    (size_t)output->rowbytes < (size_t)output->width * pixel_bytes ||
	    !DisjointPayloads(input, output)) return false;
	if (pixel_local) {
		const int64_t input_left = WorldOriginX(input);
		const int64_t input_top = WorldOriginY(input);
		const int64_t input_right = input_left + input->width;
		const int64_t input_bottom = input_top + input->height;
		const int64_t output_left = WorldOriginX(output);
		const int64_t output_top = WorldOriginY(output);
		const int64_t output_right = output_left + output->width;
		const int64_t output_bottom = output_top + output->height;
		return output_left >= input_left && output_top >= input_top &&
		       output_right <= input_right && output_bottom <= input_bottom;
	}
	if (input->width != output->width || input->height != output->height)
		return false;
#ifndef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	if (input->extent_hint.left != 0 || input->extent_hint.top != 0 ||
	    input->extent_hint.right != input->width ||
	    input->extent_hint.bottom != input->height ||
	    output->extent_hint.left != 0 || output->extent_hint.top != 0 ||
	    output->extent_hint.right != output->width ||
	    output->extent_hint.bottom != output->height ||
	    input->origin_x != 0 || input->origin_y != 0 ||
	    output->origin_x != 0 || output->origin_y != 0) return false;
#endif
	// Pixel-local keying and replacement do not depend on a captured source or
	// geometry. Admit arbitrary full-frame worlds when no neighborhood operation
	// is requested.
	// Edge Thin's distance transforms operate only on the generated matte and
	// are geometry-independent. Promote the visible UI range while keeping Edge
	// Blur's captured geometry/curve quirks on the bounded lane below.
	if (info.edge_blur_amount == 0.0 &&
	    info.edge_thin_amount >= -100.0 && info.edge_thin_amount <= 100.0 &&
	    info.edge_thin_distance_type >= 1 && info.edge_thin_distance_type <= 3) {
		return true;
	}
	if (IsGenericEdgeBlurTuple(info)) return true;
	if (IsGenericEdgeCompositionTuple(info)) return true;
	if ((size_t)input->rowbytes != (size_t)input->width * pixel_bytes + 8 ||
	    (size_t)output->rowbytes != (size_t)output->width * pixel_bytes + 8) return false;
	if (IsBoundedLab76NativeTuple<PixelT>(input, output, info)) return true;
	if (input->width == 11 && input->height == 7 &&
	    IsBoundedToggleInfo(info) && IsBoundedToggleSource<PixelT>(input))
		return true;
	return IsBoundedEdgeInfo(info, input->width, input->height) &&
	       IsBoundedEdgeSource<PixelT>(input);
}

static bool BoundedInDataGeometry(const PF_InData *in_data, bool require_zero_origin)
{
	if (!in_data) return false;
#ifdef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	return true;
#else
	return (!require_zero_origin ||
	        (in_data->output_origin_x == 0 && in_data->output_origin_y == 0)) &&
	       in_data->downsample_x.num == 1 && in_data->downsample_x.den == 1 &&
	       in_data->downsample_y.num == 1 && in_data->downsample_y.den == 1;
#endif
}

struct ColorKeyPreparedRender {
	std::vector<std::uint8_t> input_storage;
	std::vector<std::uint8_t> output_storage;
	PF_EffectWorld input_world;
	PF_EffectWorld output_world;
	size_t active_row_bytes;
};

static PF_Err
PrepareRenderWorld(PF_EffectWorld *input, PF_EffectWorld *output,
	               const OLMColorKeyInfo &info, short bitdepth,
	               ColorKeyPreparedRender *prepared)
{
	if (!prepared) return PF_Err_BAD_CALLBACK_PARAM;
	A_long pixel_bytes = 0;
	bool admitted = false;
	if (bitdepth == 8) {
		pixel_bytes = (A_long)sizeof(PF_Pixel8);
		admitted = IsPublicAdmission<PF_Pixel8>(input, output, info);
	} else if (bitdepth == 16) {
		pixel_bytes = (A_long)sizeof(PF_Pixel16);
		admitted = IsPublicAdmission<PF_Pixel16>(input, output, info);
	} else if (bitdepth == 32) {
		pixel_bytes = (A_long)sizeof(PF_PixelFloat);
		admitted = IsPublicAdmission<PF_PixelFloat>(input, output, info);
	} else {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	if (!admitted) return PF_Err_BAD_CALLBACK_PARAM;

	size_t input_bytes = 0, output_bytes = 0;
	if (!CheckedPayloadBytes(input, &input_bytes) ||
	    !CheckedPayloadBytes(output, &output_bytes)) return PF_Err_BAD_CALLBACK_PARAM;
	prepared->input_storage.resize(input_bytes);
	prepared->output_storage.assign(output_bytes, 0);
	prepared->active_row_bytes = (size_t)output->width * (size_t)pixel_bytes;
	for (A_long y = 0; y < input->height; ++y) {
		std::memcpy(prepared->input_storage.data() + (size_t)y * (size_t)input->rowbytes,
		            reinterpret_cast<const std::uint8_t *>(input->data) +
		                (size_t)y * (size_t)input->rowbytes,
		            (size_t)input->rowbytes);
	}
	prepared->input_world = *input;
	prepared->output_world = *output;
	prepared->input_world.data = reinterpret_cast<PF_PixelPtr>(prepared->input_storage.data());
	prepared->output_world.data = reinterpret_cast<PF_PixelPtr>(prepared->output_storage.data());
	return RenderWorldDirect(&prepared->input_world, &prepared->output_world, info, bitdepth);
}

static void CommitPreparedRender(const ColorKeyPreparedRender &prepared,
	                             PF_EffectWorld *output)
{
	for (A_long y = 0; y < output->height; ++y) {
		std::memcpy(reinterpret_cast<std::uint8_t *>(output->data) +
		                (size_t)y * (size_t)output->rowbytes,
		            prepared.output_storage.data() +
		                (size_t)y * (size_t)prepared.output_world.rowbytes,
		            prepared.active_row_bytes);
	}
}

static PF_Err
RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output,
	        const OLMColorKeyInfo &info, short bitdepth)
{
	ColorKeyPreparedRender prepared;
	const PF_Err err = PrepareRenderWorld(input, output, info, bitdepth, &prepared);
	if (err) return err;
	CommitPreparedRender(prepared, output);
	return PF_Err_NONE;
}

static PF_Err GetWorldDepths(PF_InData *in_data,
	                         PF_EffectWorld *input,
	                         PF_EffectWorld *output,
	                         short *depth)
{
	if (!in_data || !input || !output || !depth) return PF_Err_BAD_CALLBACK_PARAM;
	PF_PixelFormat input_format = PF_PixelFormat_INVALID;
	PF_PixelFormat output_format = PF_PixelFormat_INVALID;
#ifdef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite(
	    in_data, kPFWorldSuite, kPFWorldSuiteVersion2, NULL);
	PF_Err err = world_suite->PF_GetPixelFormat(input, &input_format);
	if (!err) err = world_suite->PF_GetPixelFormat(output, &output_format);
#else
	if (!in_data->pica_basicP || !in_data->pica_basicP->AcquireSuite ||
	    !in_data->pica_basicP->ReleaseSuite) return PF_Err_BAD_CALLBACK_PARAM;
	const void *raw_suite = NULL;
	const SPErr acquire_err = in_data->pica_basicP->AcquireSuite(
	    kPFWorldSuite, kPFWorldSuiteVersion2, &raw_suite);
	if (acquire_err) return (PF_Err)acquire_err;
	PF_Err err = PF_Err_NONE;
	std::exception_ptr thrown;
	try {
		if (!raw_suite) err = PF_Err_BAD_CALLBACK_PARAM;
		PF_WorldSuite2 *world_suite = (PF_WorldSuite2 *)raw_suite;
		if (!err && !world_suite->PF_GetPixelFormat) err = PF_Err_BAD_CALLBACK_PARAM;
		if (!err) err = world_suite->PF_GetPixelFormat(input, &input_format);
		if (!err) err = world_suite->PF_GetPixelFormat(output, &output_format);
	} catch (...) {
		thrown = std::current_exception();
	}
	try {
		const SPErr release_err = in_data->pica_basicP->ReleaseSuite(
		    kPFWorldSuite, kPFWorldSuiteVersion2);
		if (!err && !thrown && release_err) err = (PF_Err)release_err;
	} catch (...) {
		if (!thrown) thrown = std::current_exception();
	}
	if (thrown) std::rethrow_exception(thrown);
#endif
	if (err || input_format != output_format) return err ? err : PF_Err_BAD_CALLBACK_PARAM;
	switch (input_format) {
	case PF_PixelFormat_ARGB32: *depth = 8; return PF_Err_NONE;
	case PF_PixelFormat_ARGB64: *depth = 16; return PF_Err_NONE;
	case PF_PixelFormat_ARGB128: *depth = 32; return PF_Err_NONE;
	default: return PF_Err_BAD_CALLBACK_PARAM;
	}
}

static bool ClassicWorldsMatch(const PF_EffectWorld *input,
	                           const PF_EffectWorld *output,
	                           PF_PixelFormat input_format,
	                           PF_PixelFormat output_format)
{
	if (!input || !output || !input->data || !output->data ||
	    input_format != output_format ||
	    input->width <= 0 || input->height <= 0 ||
	    input->width != output->width || input->height != output->height ||
	    input->rowbytes <= 0 || output->rowbytes <= 0) {
		return false;
	}
	A_long pixel_bytes = 0;
	switch (input_format) {
	case PF_PixelFormat_ARGB32: pixel_bytes = (A_long)sizeof(PF_Pixel8); break;
	case PF_PixelFormat_ARGB64: pixel_bytes = (A_long)sizeof(PF_Pixel16); break;
	case PF_PixelFormat_ARGB128: pixel_bytes = (A_long)sizeof(PF_PixelFloat); break;
	default: return false;
	}
	return input->rowbytes == input->width * pixel_bytes + 8 &&
	       output->rowbytes == output->width * pixel_bytes + 8 &&
	       DisjointPayloads(input, output);
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	if (!in_data || !out_data || !params || !params[OLMCOLORKEY_INPUT] || !output) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_Err err = PF_Err_NONE;
	OLMColorKeyInfo info;
	ERR(CheckoutInfo(in_data, params, &info));
	if (err) return err;
	if (!BoundedInDataGeometry(
	        in_data, info.edge_thin_amount != 0.0 || info.edge_blur_amount != 0.0))
		return PF_Err_BAD_CALLBACK_PARAM;
	PF_EffectWorld *input = &params[OLMCOLORKEY_INPUT]->u.ld;
	short bitdepth = 0;
	(void)out_data;
	ERR(GetWorldDepths(in_data, input, output, &bitdepth));
	if (err) return err;
	ERR(RenderWorld(&params[OLMCOLORKEY_INPUT]->u.ld, output, info, bitdepth));
	return err;
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *, PF_PreRenderExtra *extra)
{
	if (!in_data || !extra || !extra->input || !extra->output || !extra->cb ||
	    !extra->cb->checkout_layer || !BoundedInDataGeometry(in_data, false))
		return PF_Err_BAD_CALLBACK_PARAM;
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;
	AEFX_CLR_STRUCT(in_result);

	req.preserve_rgb_of_zero_alpha = FALSE;
	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		OLMCOLORKEY_INPUT, OLMCOLORKEY_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));

	if (!err) {
		UnionLRect(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect(&in_result.max_result_rect, &extra->output->max_result_rect);
	}
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *, PF_SmartRenderExtra *extra)
{
	if (!in_data || !extra || !extra->input || !extra->cb ||
	    !extra->cb->checkout_layer_pixels || !extra->cb->checkout_output ||
	    !extra->cb->checkin_layer_pixels || !BoundedInDataGeometry(in_data, false))
		return PF_Err_BAD_CALLBACK_PARAM;
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	bool layer_checked_out = false;
	std::exception_ptr thrown;
	ColorKeyPreparedRender prepared;
	bool prepared_ok = false;
	try {
		err = extra->cb->checkout_layer_pixels(
		    in_data->effect_ref, OLMCOLORKEY_INPUT, &input_world);
		layer_checked_out = err == PF_Err_NONE;
#if !defined(AE_OS_WIN)
		if (!err && input_world) {
			err = CapturePixelFloatEntryIfRequested(input_world, extra->input->bitdepth);
		}
#endif
		if (!err && !input_world) err = PF_Err_BAD_CALLBACK_PARAM;
		if (!err) err = extra->cb->checkout_output(in_data->effect_ref, &output_world);
		if (!err && !output_world) err = PF_Err_BAD_CALLBACK_PARAM;
		short world_depth = 0;
		if (!err) err = GetWorldDepths(in_data, input_world, output_world, &world_depth);
		if (!err && world_depth != extra->input->bitdepth) err = PF_Err_BAD_CALLBACK_PARAM;
		OLMColorKeyInfo info;
		if (!err) err = CheckoutSmartInfo(in_data, &info);
		if (!err) {
			err = PrepareRenderWorld(input_world, output_world, info,
			                         extra->input->bitdepth, &prepared);
			prepared_ok = err == PF_Err_NONE;
		}
	} catch (...) {
		thrown = std::current_exception();
	}
	if (layer_checked_out) {
		try {
			const PF_Err checkin_err = extra->cb->checkin_layer_pixels(
			    in_data->effect_ref, OLMCOLORKEY_INPUT);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) {
			if (!thrown) thrown = std::current_exception();
		}
	}
	if (thrown) std::rethrow_exception(thrown);
	if (!err && prepared_ok) CommitPreparedRender(prepared, output_world);
	return err;
}

extern "C" DllExport
PF_Err PluginDataEntryFunction2(
	PF_PluginDataPtr  inPtr,
	PF_PluginDataCB2  inPluginDataCallBackPtr,
	SPBasicSuite     *,
	const char       *,
	const char       *)
{
	PF_Err result = PF_Err_INVALID_CALLBACK;
	result = PF_REGISTER_EFFECT_EXT2(
		inPtr, inPluginDataCallBackPtr,
		"OLM Color Key",
		"OLM Color Key",
		"OLM Plug-ins",
		AE_RESERVED_INFO,
		"EffectMain",
		"https://olm.co.jp/");
	return result;
}

PF_Err
EffectMain(PF_Cmd cmd, PF_InData *in_data, PF_OutData *out_data,
           PF_ParamDef *params[], PF_LayerDef *output, void *extra)
{
	PF_Err err = PF_Err_NONE;
	try {
		switch (cmd) {
		case PF_Cmd_ABOUT:
			err = About(in_data, out_data, params, output); break;
		case PF_Cmd_GLOBAL_SETUP:
			err = GlobalSetup(in_data, out_data, params, output); break;
		case PF_Cmd_PARAMS_SETUP:
			err = ParamsSetup(in_data, out_data, params, output); break;
		case PF_Cmd_RENDER:
			err = Render(in_data, out_data, params, output); break;
#ifndef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
		case PF_Cmd_UPDATE_PARAMS_UI:
			err = UpdateParameterUI(in_data, params); break;
#endif
		case PF_Cmd_SMART_PRE_RENDER:
			err = SmartPreRender(in_data, out_data, (PF_PreRenderExtra*)extra); break;
		case PF_Cmd_SMART_RENDER:
			err = SmartRender(in_data, out_data, (PF_SmartRenderExtra*)extra); break;
		}
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = (PF_Err)4;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	return err;
}
