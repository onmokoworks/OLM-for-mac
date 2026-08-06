#pragma once
#ifndef OLMKIRAKIRA_H
#define OLMKIRAKIRA_H

typedef unsigned char  u_char;
typedef unsigned short u_short;
typedef unsigned short u_int16;
typedef unsigned long  u_long;
typedef short int      int16;

#define PF_TABLE_BITS   12
#define PF_TABLE_SZ_16  4096
#define PF_DEEP_COLOR_AWARE 1

#include "AEConfig.h"

#ifdef AE_OS_WIN
	typedef unsigned short PixelType;
	#include <Windows.h>
#endif

#include "entry.h"
#include "AE_Effect.h"
#include "AE_EffectCB.h"
#include "AE_Macros.h"
#include "Param_Utils.h"
#include "AE_EffectCBSuites.h"
#include "String_Utils.h"
#include "AE_GeneralPlug.h"
#include "AEFX_ChannelDepthTpl.h"
#include "AEGP_SuiteHandler.h"

#include "OLMKiraKira_Strings.h"

#define MAJOR_VERSION 3
#define MINOR_VERSION 2
#define BUG_VERSION   0
#define STAGE_VERSION PF_Stage_DEVELOP
#define BUILD_VERSION 0

enum {
	OLMKIRAKIRA_INPUT = 0,
	OLMKIRAKIRA_CHANNEL,
	OLMKIRAKIRA_BLUR_MODE,
	OLMKIRAKIRA_MERGE_MODE,
	OLMKIRAKIRA_APPROX_INPUT,
	OLMKIRAKIRA_BRIGHTNESS_GAIN,
	OLMKIRAKIRA_STRENGTH_MULTIPLIER,
	OLMKIRAKIRA_FADE_OUT,
	OLMKIRAKIRA_GLOW_OPACITY,
	OLMKIRAKIRA_SOURCE_OPACITY,
	OLMKIRAKIRA_VERTICAL_LENGTH,
	OLMKIRAKIRA_VERTICAL_COLOR,
	OLMKIRAKIRA_VERTICAL_RAMP_GROUP,
	OLMKIRAKIRA_VERTICAL_USE_RAMP,
	OLMKIRAKIRA_VERTICAL_RAMP,
	OLMKIRAKIRA_VERTICAL_RAMP_END,
	OLMKIRAKIRA_HORIZONTAL_LENGTH,
	OLMKIRAKIRA_HORIZONTAL_COLOR,
	OLMKIRAKIRA_HORIZONTAL_RAMP_GROUP,
	OLMKIRAKIRA_HORIZONTAL_USE_RAMP,
	OLMKIRAKIRA_HORIZONTAL_RAMP,
	OLMKIRAKIRA_HORIZONTAL_RAMP_END,
	OLMKIRAKIRA_DIAGONAL_LENGTH,
	OLMKIRAKIRA_DIAGONAL_COLOR,
	OLMKIRAKIRA_DIAGONAL_RAMP_GROUP,
	OLMKIRAKIRA_DIAGONAL_USE_RAMP,
	OLMKIRAKIRA_DIAGONAL_RAMP,
	OLMKIRAKIRA_DIAGONAL_RAMP_END,
	OLMKIRAKIRA_DIAGONAL2_LENGTH,
	OLMKIRAKIRA_DIAGONAL2_COLOR,
	OLMKIRAKIRA_DIAGONAL2_RAMP_GROUP,
	OLMKIRAKIRA_DIAGONAL2_USE_RAMP,
	OLMKIRAKIRA_DIAGONAL2_RAMP,
	OLMKIRAKIRA_DIAGONAL2_RAMP_END,
	OLMKIRAKIRA_HIGHLIGHT_RADIUS,
	OLMKIRAKIRA_HIGHLIGHT_COLOR,
	OLMKIRAKIRA_HIGHLIGHT_RAMP_GROUP,
	OLMKIRAKIRA_HIGHLIGHT_USE_RAMP,
	OLMKIRAKIRA_HIGHLIGHT_RAMP,
	OLMKIRAKIRA_HIGHLIGHT_RAMP_END,
	OLMKIRAKIRA_GLOW_ROTATION,
	OLMKIRAKIRA_NUM_PARAMS
};

struct OLMKiraKiraRampStop {
	float position;
	float alpha;
	float red;
	float green;
	float blue;
};

struct OLMKiraKiraRampData {
	A_u_long count;
	OLMKiraKiraRampStop stops[16];
};

static_assert(sizeof(OLMKiraKiraRampData) == 0x144, "Windows ramp payload ABI");

enum {
	GLOW_ROTATION_DISK_ID = 1,
	BRIGHTNESS_GAIN_DISK_ID = 2,
	VERTICAL_LENGTH_DISK_ID = 3,
	HORIZONTAL_LENGTH_DISK_ID = 4,
	DIAGONAL_LENGTH_DISK_ID = 5,
	HIGHLIGHT_RADIUS_DISK_ID = 6,
	GLOW_OPACITY_DISK_ID = 7,
	CHANNEL_DISK_ID = 8,
	BLUR_MODE_DISK_ID = 9,
	APPROX_INPUT_DISK_ID = 10,
	STRENGTH_MULTIPLIER_DISK_ID = 11,
	SOURCE_OPACITY_DISK_ID = 12,
	VERTICAL_COLOR_DISK_ID = 13,
	HORIZONTAL_COLOR_DISK_ID = 14,
	DIAGONAL_COLOR_DISK_ID = 15,
	HIGHLIGHT_COLOR_DISK_ID = 16,
	MERGE_MODE_DISK_ID = 17,
	VERTICAL_USE_RAMP_DISK_ID = 18,
	VERTICAL_RAMP_SPACER_DISK_ID = 19,
	HORIZONTAL_USE_RAMP_DISK_ID = 20,
	HORIZONTAL_RAMP_SPACER_DISK_ID = 21,
	DIAGONAL_USE_RAMP_DISK_ID = 22,
	DIAGONAL_RAMP_SPACER_DISK_ID = 23,
	HIGHLIGHT_USE_RAMP_DISK_ID = 24,
	HIGHLIGHT_RAMP_SPACER_DISK_ID = 25,
	DIAGONAL2_LENGTH_DISK_ID = 26,
	FADE_OUT_DISK_ID = 27,
	DIAGONAL2_COLOR_DISK_ID = 28,
	VERTICAL_RAMP_GROUP_DISK_ID = 29,
	VERTICAL_RAMP_END_DISK_ID = 30,
	HORIZONTAL_RAMP_GROUP_DISK_ID = 31,
	HORIZONTAL_RAMP_END_DISK_ID = 32,
	DIAGONAL_RAMP_GROUP_DISK_ID = 33,
	DIAGONAL_RAMP_END_DISK_ID = 34,
	DIAGONAL2_USE_RAMP_DISK_ID = 35,
	DIAGONAL2_RAMP_SPACER_DISK_ID = 36,
	DIAGONAL2_RAMP_GROUP_DISK_ID = 37,
	DIAGONAL2_RAMP_END_DISK_ID = 38,
	HIGHLIGHT_RAMP_GROUP_DISK_ID = 39,
	HIGHLIGHT_RAMP_END_DISK_ID = 40
};

typedef struct {
	PF_FpLong glow_rotation;
	PF_FpLong brightness_gain;
	PF_FpLong fade_out;
	A_long vertical_length;
	A_long horizontal_length;
	A_long diagonal_length;
	A_long diagonal2_length;
	A_long highlight_radius;
	PF_FpLong glow_opacity;
	A_long channel;
	A_long blur_mode;
	A_long merge_mode;
	PF_Boolean approximated_input;
	PF_FpLong strength_multiplier;
	PF_FpLong source_opacity;
	PF_PixelFloat vertical_color;
	PF_PixelFloat horizontal_color;
	PF_PixelFloat diagonal_color;
	PF_PixelFloat highlight_color;
	PF_PixelFloat diagonal2_color;
	PF_Boolean vertical_use_ramp;
	PF_Boolean horizontal_use_ramp;
	PF_Boolean diagonal_use_ramp;
	PF_Boolean highlight_use_ramp;
	PF_Boolean diagonal2_use_ramp;
	OLMKiraKiraRampData vertical_ramp;
	OLMKiraKiraRampData horizontal_ramp;
	OLMKiraKiraRampData diagonal_ramp;
	OLMKiraKiraRampData highlight_ramp;
	OLMKiraKiraRampData diagonal2_ramp;
	PF_FpLong comp_width;
} OLMKiraKiraInfo;

extern "C" {
	DllExport
	PF_Err EffectMain(
		PF_Cmd         cmd,
		PF_InData     *in_data,
		PF_OutData    *out_data,
		PF_ParamDef   *params[],
		PF_LayerDef   *output,
		void          *extra);
}

#endif
