#pragma once
#ifndef OLMDIRECTIONALBLUR_H
#define OLMDIRECTIONALBLUR_H

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

#include "OLMDirectionalBlur_Strings.h"

#define MAJOR_VERSION 1
#define MINOR_VERSION 3
#define BUG_VERSION   0
#define STAGE_VERSION PF_Stage_DEVELOP
#define BUILD_VERSION 0

enum {
	OLMDIRECTIONALBLUR_INPUT = 0,
	OLMDIRECTIONALBLUR_ANGLE,
	OLMDIRECTIONALBLUR_BRIGHTNESS_GAIN,
	OLMDIRECTIONALBLUR_SIZE_VARIATION,
	OLMDIRECTIONALBLUR_FRONT_STRENGTH,
	OLMDIRECTIONALBLUR_FRONT_ALPHA_FADE,
	OLMDIRECTIONALBLUR_FRONT_SHARP_TAIL,
	OLMDIRECTIONALBLUR_BACK_STRENGTH,
	OLMDIRECTIONALBLUR_BACK_ALPHA_FADE,
	OLMDIRECTIONALBLUR_BACK_SHARP_TAIL,
	OLMDIRECTIONALBLUR_NOISE_VARIATION,
	OLMDIRECTIONALBLUR_NUM_PARAMS
};

enum {
	ANGLE_DISK_ID = 1,
	BRIGHTNESS_GAIN_DISK_ID,
	SIZE_VARIATION_DISK_ID,
	FRONT_STRENGTH_DISK_ID,
	FRONT_ALPHA_FADE_DISK_ID,
	FRONT_SHARP_TAIL_DISK_ID,
	BACK_STRENGTH_DISK_ID,
	BACK_ALPHA_FADE_DISK_ID,
	BACK_SHARP_TAIL_DISK_ID,
	NOISE_VARIATION_DISK_ID
};

typedef struct {
	PF_FpLong angle_deg;
	PF_FpLong brightness_gain;
	PF_FpLong size_variation;
	A_long front_strength;
	A_long front_alpha_fade;
	PF_FpLong front_sharp_tail;
	A_long back_strength;
	A_long back_alpha_fade;
	PF_FpLong back_sharp_tail;
	PF_FpLong noise_variation;
	PF_FpLong frame_rate;
} OLMDirectionalBlurInfo;

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
