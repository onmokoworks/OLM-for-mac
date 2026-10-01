#pragma once
#ifndef OLMRADIALBLUR_H
#define OLMRADIALBLUR_H

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

#include "OLMRadialBlur_Strings.h"

#define MAJOR_VERSION 1
#define MINOR_VERSION 3
#define BUG_VERSION   0
#define STAGE_VERSION PF_Stage_DEVELOP
#define BUILD_VERSION 0

enum {
	OLMRADIALBLUR_INPUT = 0,
	OLMRADIALBLUR_BLUR_TYPE,
	OLMRADIALBLUR_CENTER,
	OLMRADIALBLUR_OUTER_BLUR_LABEL,
	OLMRADIALBLUR_OUTER_STRENGTH,
	OLMRADIALBLUR_OUTER_OFFSET_MODE,
	OLMRADIALBLUR_OUTER_OFFSET,
	OLMRADIALBLUR_OUTER_EDGE_FADE,
	OLMRADIALBLUR_OUTER_BLANK,
	OLMRADIALBLUR_INNER_BLUR_LABEL,
	OLMRADIALBLUR_INNER_STRENGTH,
	OLMRADIALBLUR_INNER_OFFSET_MODE,
	OLMRADIALBLUR_INNER_OFFSET,
	OLMRADIALBLUR_INNER_EDGE_FADE,
	OLMRADIALBLUR_INNER_BLANK,
	OLMRADIALBLUR_REPEAT_BORDER,
	OLMRADIALBLUR_ELLIPSE_LABEL,
	OLMRADIALBLUR_RATIO,
	OLMRADIALBLUR_ANGLE,
	OLMRADIALBLUR_ELLIPSE_BLANK,
	OLMRADIALBLUR_QUALITY,
	OLMRADIALBLUR_BRIGHTNESS_GAIN,
	OLMRADIALBLUR_SIZE_VARIATION,
	OLMRADIALBLUR_NOISE_PARAMS_LABEL,
	OLMRADIALBLUR_NOISE_VARIATION,
	OLMRADIALBLUR_NOISE_TYPE,
	OLMRADIALBLUR_NOISE_LAYER,
	OLMRADIALBLUR_SEED,
	OLMRADIALBLUR_NOISE_OFFSET,
	OLMRADIALBLUR_THICKNESS,
	OLMRADIALBLUR_NOISE_BLANK,
	OLMRADIALBLUR_NUM_PARAMS
};

enum {
	BLUR_TYPE_DISK_ID = 1,
	CENTER_DISK_ID,
	OUTER_BLUR_LABEL_DISK_ID,
	OUTER_STRENGTH_DISK_ID,
	OUTER_EDGE_FADE_DISK_ID,
	OUTER_BLANK_DISK_ID,
	INNER_BLUR_LABEL_DISK_ID,
	INNER_STRENGTH_DISK_ID,
	INNER_EDGE_FADE_DISK_ID,
	INNER_BLANK_DISK_ID,
	ELLIPSE_LABEL_DISK_ID,
	RATIO_DISK_ID,
	ANGLE_DISK_ID,
	ELLIPSE_BLANK_DISK_ID,
	QUALITY_DISK_ID,
	BRIGHTNESS_GAIN_DISK_ID,
	SIZE_VARIATION_DISK_ID,
	NOISE_PARAMS_LABEL_DISK_ID,
	NOISE_VARIATION_DISK_ID,
	NOISE_TYPE_DISK_ID,
	NOISE_LAYER_DISK_ID,
	SEED_DISK_ID,
	NOISE_OFFSET_DISK_ID,
	THICKNESS_DISK_ID,
	NOISE_BLANK_DISK_ID,
	REPEAT_BORDER_DISK_ID = 26,
	OUTER_OFFSET_MODE_DISK_ID = 28,
	OUTER_OFFSET_DISK_ID,
	INNER_OFFSET_MODE_DISK_ID,
	INNER_OFFSET_DISK_ID
};

typedef struct {
	A_long blur_type;
	PF_FpLong center_x;
	PF_FpLong center_y;
	A_long outer_strength;
	A_long outer_edge_fade;
	A_long outer_offset_mode;
	A_long outer_offset;
	A_long inner_strength;
	A_long inner_edge_fade;
	A_long inner_offset_mode;
	A_long inner_offset;
	PF_Boolean repeat_border;
	PF_FpLong ratio;
	PF_FpLong angle_deg;
	PF_FpLong quality;
	PF_FpLong brightness_gain;
	PF_FpLong size_variation;
	PF_FpLong noise_variation;
	A_long noise_type;
	A_long noise_layer;
	A_long seed;
	float noise_offset;
	PF_FpLong thickness;
	PF_FpLong comp_width;
	PF_FpLong comp_height;
} OLMRadialBlurInfo;

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
