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
	OLMKIRAKIRA_GLOW_ROTATION,
	OLMKIRAKIRA_BRIGHTNESS_GAIN,
	OLMKIRAKIRA_VERTICAL_LENGTH,
	OLMKIRAKIRA_HORIZONTAL_LENGTH,
	OLMKIRAKIRA_DIAGONAL_LENGTH,
	OLMKIRAKIRA_HIGHLIGHT_RADIUS,
	OLMKIRAKIRA_GLOW_OPACITY,
	OLMKIRAKIRA_CHANNEL,
	OLMKIRAKIRA_BLUR_MODE,
	OLMKIRAKIRA_APPROX_INPUT,
	OLMKIRAKIRA_STRENGTH_MULTIPLIER,
	OLMKIRAKIRA_SOURCE_OPACITY,
	OLMKIRAKIRA_VERTICAL_COLOR,
	OLMKIRAKIRA_HORIZONTAL_COLOR,
	OLMKIRAKIRA_DIAGONAL_COLOR,
	OLMKIRAKIRA_MERGE_MODE,
	OLMKIRAKIRA_DIAGONAL2_LENGTH,
	OLMKIRAKIRA_FADE_OUT,
	OLMKIRAKIRA_DIAGONAL2_COLOR,
	OLMKIRAKIRA_NUM_PARAMS
};

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
	MERGE_MODE_DISK_ID = 16,
	DIAGONAL2_LENGTH_DISK_ID = 26,
	FADE_OUT_DISK_ID = 27,
	DIAGONAL2_COLOR_DISK_ID = 28
};

typedef struct {
	PF_FpLong glow_rotation;
	PF_FpLong brightness_gain;
	A_long vertical_length;
	A_long horizontal_length;
	A_long diagonal_length;
	A_long diagonal2_length;
	PF_FpLong glow_opacity;
	A_long channel;
	A_long blur_mode;
	PF_FpLong strength_multiplier;
	PF_FpLong source_opacity;
	PF_PixelFloat vertical_color;
	PF_PixelFloat horizontal_color;
	PF_PixelFloat diagonal_color;
	PF_PixelFloat diagonal2_color;
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
