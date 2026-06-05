#include "OLMRadialBlur.h"

typedef struct {
	A_u_long	index;
	A_char		str[256];
} TableString;

TableString g_strs[StrID_NUMTYPES] = {
	{ StrID_NONE,                  "" },
	{ StrID_Name,                  "OLM RadialBlur" },
	{ StrID_Description,           "Port of OLM RadialBlur.\rCopyright 2010 OLM Digital, Inc." },
	{ StrID_BlurType_Param_Name,   "Blur Type" },
	{ StrID_BlurType_Choices,      "Zoom|Rotation" },
	{ StrID_Center_Param_Name,     "Center" },
	{ StrID_OuterStrength_Param_Name, "Strength" },
	{ StrID_OuterOffsetMode_Param_Name, "Offset Mode" },
	{ StrID_OffsetMode_Choices,    "Add|Max|Replace" },
	{ StrID_OuterOffset_Param_Name, "Offset" },
	{ StrID_InnerStrength_Param_Name, "Inner Strength" },
	{ StrID_RepeatBorder_Param_Name, "Repeat Border" },
	{ StrID_Ratio_Param_Name,      "Ratio" },
	{ StrID_Angle_Param_Name,      "Angle" },
	{ StrID_Quality_Param_Name,    "Quality" },
	{ StrID_BrightnessGain_Param_Name, "Brightness Gain" },
	{ StrID_SizeVariation_Param_Name, "Size Variation" },
	{ StrID_NoiseVariation_Param_Name, "Noise Variation" },
};

char *GetStringPtr(int strNum)
{
	return g_strs[strNum].str;
}
