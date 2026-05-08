#include "ColorKeep.h"

typedef struct {
	A_u_long	index;
	A_char		str[256];
} TableString;

TableString g_strs[StrID_NUMTYPES] = {
	{ StrID_NONE,                         "" },
	{ StrID_Name,                         "Color Keep" },
	{ StrID_Description,                  "Keep the selected color from the source.\rCopyright 2010 OLM Digital, Inc." },
	{ StrID_EnabledColorNum_Param_Name,   "Enabled Color Num" },
	{ StrID_Color_Param_Name,             "Color" },
};

char *GetStringPtr(int strNum)
{
	return g_strs[strNum].str;
}
