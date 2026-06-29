#include "OLMKiraKira.h"

typedef struct {
	A_u_long	index;
	A_char		str[256];
} TableString;

TableString g_strs[StrID_NUMTYPES] = {
	{ StrID_NONE,                         "" },
	{ StrID_Name,                         "OLM Kira Kira" },
	{ StrID_Description,                  "Apple Silicon port scaffold of OLM Kira Kira.\rCopyright 2010 OLM Digital, Inc." },
	{ StrID_GlowRotation_Param_Name,      "Glow Rotation" },
	{ StrID_BrightnessGain_Param_Name,    "Brightness Gain" },
	{ StrID_VerticalLength_Param_Name,    "Vertical Length" },
	{ StrID_HorizontalLength_Param_Name,  "Horizontal Length" },
	{ StrID_DiagonalLength_Param_Name,    "Diagonal Length" },
	{ StrID_HighlightRadius_Param_Name,   "Highlight Radius" },
	{ StrID_GlowOpacity_Param_Name,       "Glow Opacity" },
	{ StrID_Channel_Param_Name,           "Channel" },
	{ StrID_Channel_Choices,              "Alpha|Luminance|RGB Max|RGB" },
	{ StrID_BlurMode_Param_Name,          "Blur Mode" },
	{ StrID_BlurMode_Choices,             "Normal|Soft" },
	{ StrID_ApproximatedInput_Param_Name, "Approximated Input" },
	{ StrID_StrengthMultiplier_Param_Name,"Strength Multiplier" },
	{ StrID_SourceOpacity_Param_Name,     "Source Opacity" },
	{ StrID_VerticalColor_Param_Name,     "Vertical Color" },
	{ StrID_HorizontalColor_Param_Name,   "Horizontal Color" },
	{ StrID_DiagonalColor_Param_Name,     "Diagonal Color" },
	{ StrID_HighlightColor_Param_Name,    "Highlight Color" },
	{ StrID_MergeMode_Param_Name,         "Merge Mode" },
	{ StrID_MergeMode_Choices,            "Normal|Add" },
	{ StrID_UseRamp_Param_Name,           "Use Ramp" },
	{ StrID_Diagonal2Length_Param_Name,   "Diagonal2 Length" },
	{ StrID_FadeOut_Param_Name,           "Fade Out" },
	{ StrID_Diagonal2Color_Param_Name,    "Diagonal2 Color" },
};

char *GetStringPtr(int strNum)
{
	return g_strs[strNum].str;
}
