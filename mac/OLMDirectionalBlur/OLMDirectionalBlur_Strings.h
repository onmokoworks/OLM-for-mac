#pragma once

typedef enum {
	StrID_NONE,
	StrID_Name,
	StrID_Description,
	StrID_Angle_Param_Name,
	StrID_BrightnessGain_Param_Name,
	StrID_SizeVariation_Param_Name,
	StrID_FrontBlurParams_Param_Name,
	StrID_FrontStrength_Param_Name,
	StrID_FrontAlphaFade_Param_Name,
	StrID_FrontSharpTail_Param_Name,
	StrID_FrontBlank_Param_Name,
	StrID_BackBlurParams_Param_Name,
	StrID_BackStrength_Param_Name,
	StrID_BackAlphaFade_Param_Name,
	StrID_BackSharpTail_Param_Name,
	StrID_BackBlank_Param_Name,
	StrID_NoiseParams_Param_Name,
	StrID_NoiseVariation_Param_Name,
	StrID_NoiseType_Param_Name,
	StrID_NoiseType_Choices,
	StrID_NoiseLayer_Param_Name,
	StrID_Seed_Param_Name,
	StrID_NoiseOffset_Param_Name,
	StrID_Thickness_Param_Name,
	StrID_NoiseBlank_Param_Name,
	StrID_NUMTYPES
} StrIDType;

char *GetStringPtr(int strNum);
