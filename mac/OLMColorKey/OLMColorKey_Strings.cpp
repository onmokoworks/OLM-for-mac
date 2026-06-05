#include "OLMColorKey.h"

typedef struct {
	A_u_long	index;
	A_char		str[256];
} TableString;

TableString g_strs[StrID_NUMTYPES] = {
	{ StrID_NONE,                            "" },
	{ StrID_Name,                            "OLM Color Key" },
	{ StrID_Description,                     "Port of OLM Color Key.\rCopyright 2010 OLM Digital, Inc." },
	{ StrID_ColorKeep_Param_Name,            "Color Keep" },
	{ StrID_Threshold_Param_Name,            "Threshold" },
	{ StrID_Premultiplied_Param_Name,        "Premultiplied Color" },
	{ StrID_ColorSpace_Param_Name,           "Color Space" },
	{ StrID_ColorSpace_Choices,              "RGB|HSV|Lab76|Lab94|YUV|YCrCb" },
	{ StrID_ForceLowerPrecision_Param_Name,  "Force Lower Precision" },
	{ StrID_ForceLowerPrecision_Choices,     "Full|16bit|8bit" },
	{ StrID_PerColor_Param_Name,             "Per Color" },
	{ StrID_PerComponent_Param_Name,         "Per Component" },
	{ StrID_ThresholdR_Param_Name,           "Threshold(R,H,L,Y,Y)" },
	{ StrID_ThresholdG_Param_Name,           "Threshold(G,S,a,U,Cr)" },
	{ StrID_ThresholdB_Param_Name,           "Threshold(B,V,b,V,Cb)" },
	{ StrID_EdgeThinAmount_Param_Name,       "Edge Thin Amount" },
	{ StrID_DistanceType_Param_Name,         "Distance Type" },
	{ StrID_DistanceType_Choices,            "Box|Approximate|Euclidean" },
	{ StrID_EdgeBlurAmount_Param_Name,       "Edge Blur Amount" },
	{ StrID_EdgeBlurDirection_Param_Name,    "Direction" },
	{ StrID_EdgeBlurDirection_Choices,       "Inside|Around|Outside" },
	{ StrID_NumberOfColors_Param_Name,       "Number of Colors" },
	{ StrID_EnableReplace_Param_Name,        "Enable Replace" },
	{ StrID_Color_Param_Name,                "Color" },
	{ StrID_ThresholdIndexed_Param_Name,     "Threshold" },
	{ StrID_UseColor_Param_Name,             "Use Color" },
	{ StrID_UseReplaceColor_Param_Name,      "Use Replace Color" },
	{ StrID_ReplaceColor_Param_Name,         "Replace Color" },
};

char *GetStringPtr(int strNum)
{
	return g_strs[strNum].str;
}
